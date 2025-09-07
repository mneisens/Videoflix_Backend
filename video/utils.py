"""
Helper functions for the Video app
"""
import os
from pathlib import Path
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Video


def get_video_list():
    """
    Retrieves all videos ordered by creation date
    """
    try:
        videos = Video.objects.all().order_by('-created_at')
        return videos
    except Exception as e:
        return []


def create_hls_manifest_content(video_id, resolution):
    """
    Creates HLS manifest content using real HLS segments
    """
    from pathlib import Path
    
    hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(video_id) / resolution
    playlist_file = hls_dir / 'playlist.m3u8'
    
    # Prüfe ob echte HLS-Segmente existieren
    if playlist_file.exists():
        try:
            with open(playlist_file, 'r') as f:
                playlist_content = f.read()
            
            # Ersetze relative Segment-Pfade mit absoluten URLs
            base_url = f"{settings.SITE_URL}/api/video/{video_id}/{resolution}/"
            lines = playlist_content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.endswith('.ts'):
                    # Segment-Datei - erstelle absolute URL
                    updated_lines.append(f"{base_url}{line}")
                else:
                    updated_lines.append(line)
            
            return '\n'.join(updated_lines)
        except Exception as e:
            print(f"Fehler beim Lesen der HLS-Playlist: {e}")
    
    # Fallback: Direkte Video-URL (wie vorher)
    video = Video.objects.get(id=video_id)
    if video.video_file:
        video_url = f"{settings.SITE_URL}{video.video_file.url}"
        return f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.0,
{video_url}
#EXT-X-ENDLIST
"""
    
    return create_empty_manifest()


def create_external_video_manifest(video_url, resolution):
    """
    Creates HLS manifest for external video URL
    """
    return f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION={resolution}
{video_url}
"""


def create_empty_manifest():
    """
    Creates an empty HLS manifest as fallback
    """
    return """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.0,
#EXT-X-ENDLIST
"""


def get_hls_segment_path(movie_id, resolution, segment):
    """
    Gets the path to an HLS video segment
    """
    hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(movie_id) / resolution
    return hls_dir / segment


def validate_hls_directory(hls_dir):
    """
    Validates if HLS directory exists
    """
    if not hls_dir.exists():
        return JsonResponse({'error': f'HLS directory not found: {hls_dir}'}, status=404)
    return None


def validate_segment_file(segment_path):
    """
    Validates if segment file exists
    """
    if not segment_path.exists():
        return JsonResponse({'error': f'Segment not found: {segment_path}'}, status=404)
    return None


def create_segment_response(segment_path):
    """
    Creates a FileResponse for video segment
    """
    response = FileResponse(
        open(segment_path, 'rb'),
        content_type='video/MP2T'
    )
    
    response['Cache-Control'] = 'public, max-age=3600'
    response['Content-Disposition'] = 'inline'
    
    return response


def get_active_video(video_id):
    """
    Retrieves an active video by ID
    """
    return get_object_or_404(Video, id=video_id, is_active=True)


def create_direct_video_response(video_file):
    """
    Creates a FileResponse for direct video streaming
    """
    response = FileResponse(video_file, content_type='video/mp4')
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response['Accept-Ranges'] = 'bytes'
    return response


def create_redirect_response(video_url):
    """
    Creates a redirect response for external video URL
    """
    response = HttpResponseRedirect(video_url)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


def create_video_not_found_response():
    """
    Creates a response when no video is available
    """
    return Response({
        'error': 'No video available.'
    }, status=status.HTTP_404_NOT_FOUND)


def create_video_error_response(error_message):
    """
    Creates an error response for video loading failures
    """
    return Response({
        'error': f'Error loading video: {error_message}'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_segment_error_response(error_message):
    """
    Creates an error response for segment loading failures
    """
    return JsonResponse({'error': f'Error loading segment: {error_message}'}, status=500)
