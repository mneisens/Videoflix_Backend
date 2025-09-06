from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .serializers import VideoSerializer
from ..models import Video
from ..utils import (
    get_video_list, create_hls_manifest_content, create_external_video_manifest,
    create_empty_manifest, get_hls_segment_path, validate_hls_directory,
    validate_segment_file, create_segment_response, get_active_video,
    create_direct_video_response, create_redirect_response,
    create_video_not_found_response, create_video_error_response,
    create_segment_error_response
)

class VideoListView(generics.ListAPIView):
    """
    Returns a list of all available videos
    """
    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer
    permission_classes = [AllowAny] 

    def get(self, request, *args, **kwargs):
        try:
            videos = get_video_list()
            serializer = VideoSerializer(videos, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response([], status=200)


class HLSManifestView(generics.GenericAPIView):
    """
    HLS manifest for a specific movie and selected resolution
    """
    permission_classes = [AllowAny]
    
    def get(self, request, movie_id, resolution):
        try:
            video = get_object_or_404(Video, id=movie_id)
            
            if video.video_file:
                from django.conf import settings
                video_url = f"{settings.SITE_URL}{video.video_file.url}"
                manifest_content = create_hls_manifest_content(video_url)
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
            
            elif video.video_url and not video.video_url.startswith(f'/api/video/{movie_id}'):
                manifest_content = create_external_video_manifest(video.video_url, resolution)
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
            
            else:
                manifest_content = create_empty_manifest()
                return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
                
        except Exception as e:
            manifest_content = create_empty_manifest()
            return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')


class HLSVideoSegmentView(generics.GenericAPIView):
    """
    HLS video segment for a specific movie in selected resolution
    """
    permission_classes = [AllowAny]
    
    def get(self, request, movie_id, resolution, segment):
        try:
            from pathlib import Path
            from django.conf import settings
            
            hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(movie_id) / resolution
            segment_path = get_hls_segment_path(movie_id, resolution, segment)

            directory_error = validate_hls_directory(hls_dir)
            if directory_error:
                return directory_error
            
            segment_error = validate_segment_file(segment_path)
            if segment_error:
                return segment_error
            
            return create_segment_response(segment_path)
            
        except Exception as e:
            return create_segment_error_response(str(e))


class DirectVideoView(APIView):
    """Direct video stream for simple frontend integration"""
    permission_classes = [AllowAny]
    
    def get(self, request, video_id):
        try:
            video = get_active_video(video_id)
            
            if video.video_file:
                return create_direct_video_response(video.video_file)
            
            elif video.video_url:
                return create_redirect_response(video.video_url)
            
            else:
                return create_video_not_found_response()
                
        except Exception as e:
            return create_video_error_response(str(e))
