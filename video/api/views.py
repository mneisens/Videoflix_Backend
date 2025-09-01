import os
import re
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from .serializers import VideoSerializer
from ..models import Video
from ..services import ensure_hls_stream, get_hls_segments
from auth_app.api.authentication import CustomJWTAuthentication
from django.conf import settings

class VideoListView(generics.ListAPIView):
    serializer_class = VideoSerializer
    permission_classes = [AllowAny] 
    
    def get_queryset(self):
        return Video.objects.filter(is_active=True)

class VideoListViewAuthenticated(generics.ListAPIView):
    """Authentifizierte Video-Liste für eingeloggte Benutzer"""
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication] 
    
    def get_queryset(self):
        return Video.objects.filter(is_active=True)

class HLSManifestView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, movie_id, resolution):
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            
            if video.video_file:
                try:
                    hls_info = get_hls_segments(movie_id, resolution)
                    
                    if not hls_info:
                        hls_info = ensure_hls_stream(video.video_file.path, movie_id, resolution)
                    
                    if not hls_info or not hls_info.get('success'):
                        return Response({
                            'error': f'Fehler beim Erstellen des HLS-Streams: {hls_info.get("error", "Unbekannter Fehler")}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    try:
                        with open(hls_info['playlist'], 'r') as f:
                            manifest_content = f.read()
                        
                        response = HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
                        response['Access-Control-Allow-Origin'] = '*'
                        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
                        return response
                        
                    except FileNotFoundError:
                        return Response({
                            'error': f'HLS-Playlist nicht gefunden: {hls_info["playlist"]}'
                        }, status=status.HTTP_404_NOT_FOUND)
                    except Exception as e:
                        return Response({
                            'error': f'Fehler beim Lesen der HLS-Playlist: {str(e)}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        
                except Exception as e:
                    return Response({
                        'error': f'Fehler beim HLS-Service: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            elif video.video_url and not video.video_url.startswith('http://localhost:8000'):
                manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.000000,
{video.video_url}
#EXT-X-ENDLIST
"""
                
                response = HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
                return response
            
            else:
                manifest_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-ENDLIST
"""
                
                response = HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
                return response
            
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des HLS-Manifests: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HLSVideoSegmentView(APIView):
    """View für echte HLS-Video-Segmente"""
    permission_classes = [AllowAny] 
    
    def get(self, request, movie_id, resolution, segment_name):
        """Gibt ein echtes HLS-Video-Segment zurück"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            
            if not video.video_file:
                return Response({
                    'error': 'Kein Video für diesen Film verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
            

            segment_path = os.path.join(settings.MEDIA_ROOT, 'hls', str(movie_id), resolution, segment_name)
            
            if not os.path.exists(segment_path):
                return Response({
                    'error': 'HLS-Segment nicht gefunden.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Segment als .ts Datei senden
            response = FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS, HEAD'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Range, Origin'
            response['Cache-Control'] = 'public, max-age=3600'
            return response
                
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des Video-Segments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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