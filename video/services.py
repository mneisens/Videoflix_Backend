from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid
import os
import subprocess
import json
from pathlib import Path

def send_activation_email(user, request):
    """
    Sendet eine Aktivierungs-E-Mail an den Benutzer
    """
    activation_url = f"{request.scheme}://{request.get_host()}/api/activate/{user.id}/{user.activation_token}/"
    
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
        # HLS-Ausgabeverzeichnis erstellen
        hls_output_dir = Path(settings.MEDIA_ROOT) / 'hls' / str(video_id) / resolution
        hls_output_dir.mkdir(parents=True, exist_ok=True)
        
        # HLS-Ausgabedatei
        hls_output = hls_output_dir / 'playlist.m3u8'
        
        # FFmpeg-Befehl für HLS-Konvertierung
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', str(video_file_path),
            '-c:v', 'libx264',  # H.264 Video-Codec
            '-c:a', 'aac',      # AAC Audio-Codec
            '-f', 'hls',        # HLS-Format
            '-hls_time', '10',  # Segment-Länge in Sekunden
            '-hls_list_size', '0',  # Alle Segmente behalten
            '-hls_segment_filename', str(hls_output_dir / 'segment_%03d.ts'),
            '-hls_playlist_type', 'vod',  # Video on Demand
            '-preset', 'fast',  # Schnelle Kodierung
            '-crf', '23',       # Qualität (23 = gut)
            str(hls_output)
        ]
        
        # FFmpeg ausführen
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 Minuten Timeout
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
            
        # Playlist-Datei finden
        playlist_files = list(hls_dir.glob('*.m3u8'))
        if not playlist_files:
            return None
            
        playlist_path = playlist_files[0]
        
        # Segmente finden
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
    Stellt sicher, dass ein HLS-Stream existiert, erstellt ihn falls nötig
    """
    hls_info = get_hls_segments(video_id, resolution)
    
    if hls_info is None:
        # HLS-Stream erstellen
        return create_hls_stream(video_file_path, video_id, resolution)
    
    return hls_info

def process_video_async(video_id, resolutions=None, priority='default'):
    """
    Verarbeitet ein Video asynchron mit Background-Tasks
    """
    if resolutions is None:
        resolutions = ['480p', '720p', '1080p']
    
    try:
        # Import hier, um zirkuläre Imports zu vermeiden
        from .tasks import process_video_upload, process_multiple_resolutions
        
        if len(resolutions) == 1:
            # Einzelne Auflösung
            job = process_video_upload.delay(video_id, resolutions[0])
            return {
                'success': True,
                'job_id': job.id,
                'message': f'Video processing queued for {resolutions[0]}',
                'queue': priority
            }
        else:
            # Mehrere Auflösungen
            job = process_multiple_resolutions.delay(video_id, resolutions)
            return {
                'success': True,
                'job_id': job.id,
                'message': f'Video processing queued for {len(resolutions)} resolutions',
                'queue': 'high'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_video_processing_status(video_id):
    """
    Gibt den aktuellen Verarbeitungsstatus eines Videos zurück
    """
    try:
        from django_rq import get_queue
        
        # Prüfe alle Queues nach Jobs für dieses Video
        status = {
            'video_id': video_id,
            'queues': {},
            'processing': False,
            'completed_resolutions': [],
            'pending_resolutions': []
        }
        
        for queue_name in ['default', 'high', 'low']:
            queue = get_queue(queue_name)
            queue_jobs = []
            
            for job in queue.jobs:
                if hasattr(job, 'args') and len(job.args) > 0:
                    if job.args[0] == video_id:
                        queue_jobs.append({
                            'job_id': job.id,
                            'status': 'queued',
                            'created_at': job.created_at.isoformat() if job.created_at else None
                        })
                        status['processing'] = True
            
            status['queues'][queue_name] = queue_jobs
        
        # Prüfe welche Auflösungen bereits verarbeitet wurden
        resolutions = ['480p', '720p', '1080p']
        for resolution in resolutions:
            hls_info = get_hls_segments(video_id, resolution)
            if hls_info:
                status['completed_resolutions'].append(resolution)
            else:
                status['pending_resolutions'].append(resolution)
        
        return status
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def cancel_video_processing(video_id):
    """
    Bricht die Verarbeitung eines Videos ab
    """
    try:
        from django_rq import get_queue
        
        cancelled_count = 0
        
        for queue_name in ['default', 'high', 'low']:
            queue = get_queue(queue_name)
            
            for job in queue.jobs:
                if hasattr(job, 'args') and len(job.args) > 0:
                    if job.args[0] == video_id:
                        job.cancel()
                        cancelled_count += 1
        
        return {
            'success': True,
            'cancelled_jobs': cancelled_count,
            'message': f'Cancelled {cancelled_count} processing jobs for video {video_id}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
