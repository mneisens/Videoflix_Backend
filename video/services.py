from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid
import os
import subprocess
import json
from pathlib import Path
from django_rq import get_queue
from .models import Video

def send_activation_email(user, request):
    """
    Sendet eine Aktivierungs-E-Mail an den Benutzer
    """
    frontend_url = "http://localhost:5500"
    if request.get_host().startswith('127.0.0.1'):
        frontend_url = "http://127.0.0.1:5500"
    
    activation_url = f"{frontend_url}/pages/auth/login.html?message=activation_success&uid={user.id}&token={user.activation_token}"
    
    html_message = render_to_string('video/activation_email.html', {
        'user': user,
        'activation_url': activation_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Videoflix - Aktivieren Sie Ihr Konto',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@videoflix.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_password_reset_email(user, request):
    """
    Sendet eine Passwort-Reset-E-Mail an den Benutzer
    """
    frontend_url = "http://localhost:5500"
    if request.get_host().startswith('127.0.0.1'):
        frontend_url = "http://127.0.0.1:5500"
    
    reset_url = f"{frontend_url}/pages/auth/confirm_password.html?uid={user.id}&token={user.password_reset_token}"
    
    html_message = render_to_string('video/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Videoflix - Passwort zurücksetzen',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@videoflix.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

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
    
    queue = get_queue('default')
    job = queue.enqueue(
        create_hls_stream,
        video_file_path,
        video_id,
        resolution,
        timeout=600  
    )
    return create_hls_stream(video_file_path, video_id, resolution)


def get_queue_status():
    """
    Gibt den Status der RQ-Queues zurück
    """
    try:
        queue = get_queue('default')
        return {
            'queue_name': 'default',
            'job_count': len(queue),
            'workers': len(queue.workers)
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def clear_all_queues():
    """
    Löscht alle Jobs aus allen Queues (nützlich für Development/Testing)
    """
    try:
        from django_rq import get_queue
        
        queues = ['default', 'high', 'low']
        for queue_name in queues:
            queue = get_queue(queue_name)
            queue.empty()
        
        return {
            'success': True,
            'message': f'All queues cleared: {", ".join(queues)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
