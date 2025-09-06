import os
import subprocess
import json
from pathlib import Path
from django.conf import settings
from .models import Video

def create_hls_stream(video_file_path, video_id, resolution='720p'):
    """
    Konvertiert eine MP4-Datei in einen HLS-Stream
    """
    try:
        hls_output_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(video_id) / resolution
        hls_output_dir.mkdir(parents=True, exist_ok=True)
        
        hls_output = hls_output_dir / 'playlist.m3u8'
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', str(video_file_path),
            '-c:v', 'libx264',  
            '-c:a', 'aac',     
            '-f', 'hls',        
            '-hls_time', '10',  
            '-hls_list_size', '0',  
            '-hls_segment_filename', str(hls_output_dir / 'segment_%03d.ts'),
            '-hls_playlist_type', 'vod',  
            '-preset', 'fast',  
            '-crf', '23',      
            str(hls_output)
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'playlist_path': str(hls_output),
                'output_dir': str(hls_output_dir)
            }
        else:
            return {
                'success': False,
                'error': result.stderr
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_hls_segments(video_id, resolution='720p'):
    """
    Gibt die Liste der HLS-Segmente zurück
    """
    try:
        hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(video_id) / resolution
        
        if not hls_dir.exists():
            return None

        playlist_files = list(hls_dir.glob('*.m3u8'))
        if not playlist_files:
            return None
            
        playlist_path = playlist_files[0]
        
        segment_files = sorted(hls_dir.glob('*.ts'))
        
        return {
            'success': True,
            'playlist': str(playlist_path),
            'segments': [str(seg) for seg in segment_files],
            'segment_count': len(segment_files)
        }
        
    except Exception as e:
        return None


def ensure_hls_stream(video_file_path, video_id, resolution='720p'):
    """
    Stellt sicher, dass ein HLS-Stream existiert, erstellt ihn bei Bedarf
    """
    existing_stream = get_hls_segments(video_id, resolution)
    if existing_stream:
        return existing_stream
    
    return create_hls_stream(video_file_path, video_id, resolution)


def extract_video_thumbnail(video_file_path, video_id, timestamp='00:00:01'):
    """
    Extrahiert ein Thumbnail aus dem Video mit FFmpeg
    """
    try:
        thumbnail_dir = Path(settings.MEDIA_ROOT) / 'thumbnails'
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        thumbnail_filename = f"video_{video_id}_thumbnail.jpg"
        thumbnail_path = thumbnail_dir / thumbnail_filename
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', str(video_file_path),
            '-ss', timestamp, 
            '-vframes', '1', 
            '-q:v', '2',       
            '-vf', 'scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2',
            '-y',             
            str(thumbnail_path)
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=60 
        )
        
        if result.returncode == 0 and thumbnail_path.exists():
            relative_path = f"thumbnails/{thumbnail_filename}"
            return {
                'success': True,
                'thumbnail_path': relative_path,
                'full_path': str(thumbnail_path)
            }
        else:
            return {
                'success': False,
                'error': result.stderr or 'Thumbnail konnte nicht erstellt werden'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
