import os
import re
from pathlib import Path
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

class CookieOrAuthenticatedPermission(BasePermission):
    """
    Erlaubt Zugriff wenn:
    1. Benutzer ist authentifiziert (JWT-Token im Header)
    2. ODER gültiger access_token Cookie ist vorhanden
    """
    
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

        access_token = request.COOKIES.get('access_token')
        if access_token:
            try:
                from auth_app.api.authentication import CustomJWTAuthentication
                auth = CustomJWTAuthentication()
                user, token = auth.authenticate(request)
                if user:
                    request.user = user
                    return True
            except:
                pass
        
        return False
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .serializers import VideoSerializer
from ..models import Video
from ..services import ensure_hls_stream, get_hls_segments
from auth_app.api.authentication import CustomJWTAuthentication
from django.conf import settings
from django.core.cache import cache

class VideoListView(generics.ListAPIView):
    """
    Gibt eine Liste aller verfügbaren Videos zurück
    """
    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer
    permission_classes = [CookieOrAuthenticatedPermission] 

    def get(self, request, *args, **kwargs):
        try:
            cache_key = 'video_list_public'
            cached_data = cache.get(cache_key)
            
            if cached_data is None:
                response = super().get(request, *args, **kwargs)
                cache.set(cache_key, response.data, 300)
                return response
            
            return Response(cached_data)
        except Exception as e:
            try:
                videos = Video.objects.all().order_by('-created_at')
                serializer = VideoSerializer(videos, many=True, context={'request': request})
                return Response(serializer.data)
            except Exception as fallback_error:
                return Response([], status=200)


class HLSManifestView(generics.GenericAPIView):
    """
    HLS-Manifest für einen bestimmten Film und eine gewählte Auflösung
    """
    permission_classes = [CookieOrAuthenticatedPermission]
    
    def get(self, request, movie_id, resolution):
        try:
            video = get_object_or_404(Video, id=movie_id)
            
            if video.video_file:
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
            
            elif video.video_url and not video.video_url.startswith(f'/api/video/{movie_id}'):
                manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION={resolution}
{video.video_url}
"""
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
            
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
    permission_classes = [CookieOrAuthenticatedPermission]  # Cookie-basierte Auth
    
    def get(self, request, movie_id, resolution, segment):
        try:
            hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(movie_id) / resolution
            segment_path = hls_dir / segment

            if not hls_dir.exists():
                return JsonResponse({'error': f'HLS-Verzeichnis nicht gefunden: {hls_dir}'}, status=404)
            
            if not segment_path.exists():
                return JsonResponse({'error': f'Segment nicht gefunden: {segment_path}'}, status=404)
            
            response = FileResponse(
                open(segment_path, 'rb'),
                content_type='video/MP2T'
            )
            
            response['Cache-Control'] = 'public, max-age=3600'
            response['Content-Disposition'] = 'inline'
            
            return response
            
        except Exception as e:
            return JsonResponse({'error': f'Fehler beim Laden des Segments: {str(e)}'}, status=500)


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
