import os
import re
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .serializers import VideoSerializer
from ..models import Video
from ..services import ensure_hls_stream, get_hls_segments, get_queue_status, clear_all_queues
from auth_app.api.authentication import CustomJWTAuthentication
from django.conf import settings
from django.core.cache import cache

class VideoListView(generics.ListAPIView):
    """
    Gibt eine Liste aller verfügbaren Videos zurück
    """
    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer
    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            cache_key = 'video_list_public'
            cached_data = cache.get(cache_key)
            
            if cached_data is None:
                response = super().get(request, *args, **kwargs)
                # Cache für 5 Minuten
                cache.set(cache_key, response.data, 300)
                return response
            
            return Response(cached_data)
        except Exception as e:
            # Fallback: Direkte Serialisierung ohne Cache
            try:
                videos = Video.objects.all().order_by('-created_at')
                serializer = VideoSerializer(videos, many=True, context={'request': request})
                return Response(serializer.data)
            except Exception as fallback_error:
                return Response([], status=200)  # Leere Liste als Fallback


class HLSManifestView(generics.GenericAPIView):
    """
    HLS-Manifest für einen bestimmten Film und eine gewählte Auflösung
    """
    permission_classes = []  # Keine Authentifizierung erforderlich
    
    def get(self, request, movie_id, resolution):
        try:
            video = get_object_or_404(Video, id=movie_id)
            
            # Wenn Video eine lokale Datei hat, erstelle ein HLS-Manifest
            if video.video_file:
                # Direkte Referenz auf die MP4-Datei
                video_url = f"{settings.SITE_URL}{video.video_file.url}"
                
                manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.0,
{video_url}
#EXT-X-ENDLIST
"""
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
            
            # Wenn Video eine externe URL hat
            elif video.video_url and not video.video_url.startswith(f'/api/video/{movie_id}'):
                manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION={resolution}
{video.video_url}
"""
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
            
            # Fallback: Leeres Manifest
            else:
                manifest_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.0,
#EXT-X-ENDLIST
"""
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
                
        except Exception as e:
            # Fallback: Leeres Manifest bei Fehlern
            manifest_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.0,
#EXT-X-ENDLIST
"""
            return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')


class HLSVideoSegmentView(generics.GenericAPIView):
    """
    HLS-Videosegment für einen bestimmten Film in gewählter Auflösung
    """
    permission_classes = []  # Keine Authentifizierung erforderlich
    
    def get(self, request, movie_id, resolution, segment):
        try:
            video = get_object_or_404(Video, id=movie_id)
            
            # Cache-Key für Segment-Info
            cache_key = f'hls_segment_info_{movie_id}_{resolution}'
            segment_info = cache.get(cache_key)
            
            if not segment_info:
                segment_info = get_hls_segments(movie_id, resolution)
                if segment_info:
                    cache.set(cache_key, segment_info, 1800)  # 30 Minuten Cache
            
            if not segment_info:
                return JsonResponse({'error': 'HLS-Segmente nicht gefunden'}, status=404)
            
            # Suche nach dem spezifischen Segment
            segment_path = None
            for seg in segment_info.get('segments', []):
                if seg.endswith(segment):
                    segment_path = seg
                    break
            
            if not segment_path or not os.path.exists(segment_path):
                return JsonResponse({'error': 'Segment nicht gefunden'}, status=404)
            
            # Serve das Segment mit Range-Header-Unterstützung
            response = FileResponse(
                open(segment_path, 'rb'),
                content_type='video/MP2T'
            )
            
            # Cache-Headers für bessere Performance
            response['Cache-Control'] = 'public, max-age=3600'
            response['Content-Disposition'] = 'inline'
            
            return response
            
        except Exception as e:
            return JsonResponse({'error': f'Fehler beim Laden des Segments: {str(e)}'}, status=500)


class QueueStatusView(generics.GenericAPIView):
    """
    Status der RQ-Queues
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            status_info = get_queue_status()
            return JsonResponse(status_info)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class QueueManagementView(generics.GenericAPIView):
    """
    Queue-Management (nur für Development/Testing)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            action = request.data.get('action')
            
            if action == 'clear_all':
                result = clear_all_queues()
                return JsonResponse(result)
            else:
                return JsonResponse({'error': 'Unbekannte Aktion'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class DirectVideoView(APIView):
    """Direkter Video-Stream für einfache Frontend-Integration"""
    permission_classes = [AllowAny]
    
    def get(self, request, video_id):
        try:
            video = get_object_or_404(Video, id=video_id, is_active=True)
            
            if video.video_file:
                response = FileResponse(video.video_file, content_type='video/mp4')
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response['Accept-Ranges'] = 'bytes'
                return response
            
            elif video.video_url:
                response = HttpResponseRedirect(video.video_url)
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return response
            
            else:
                return Response({
                    'error': 'Kein Video verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des Videos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)