"""
Background tasks for video processing using Django RQ
"""
import os
import logging
import subprocess
from pathlib import Path
from django_rq import job
from django.conf import settings
from .models import Video

logger = logging.getLogger(__name__)


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


@job('default')
def process_video_upload(video_id, resolution='720p'):
    """
    Background task to process video upload and create HLS streams
    """
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.video_file:
            logger.error(f"Video {video_id} has no video file")
            return False
        
        video_path = video.video_file.path
        
        result = create_hls_stream(video_path, video_id, resolution)
        
        if result['success']:
            logger.info(f"Successfully created HLS stream for video {video_id} at {resolution}")
            video.save()
            return True
        else:
            logger.error(f"Failed to create HLS stream for video {video_id}: {result.get('error')}")
            return False
            
    except Video.DoesNotExist:
        logger.error(f"Video {video_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        return False


@job('high')
def process_multiple_resolutions(video_id, resolutions=None):
    """
    Process video for multiple resolutions (high priority)
    """
    if resolutions is None:
        resolutions = ['480p', '720p', '1080p']
    
    results = {}
    
    for resolution in resolutions:
        try:
            existing_stream = get_hls_segments(video_id, resolution)
            
            if existing_stream:
                logger.info(f"Stream for {resolution} already exists for video {video_id}")
                results[resolution] = True
                continue
            
            result = process_video_upload.delay(video_id, resolution)
            results[resolution] = result
            
        except Exception as e:
            logger.error(f"Error processing {resolution} for video {video_id}: {str(e)}")
            results[resolution] = False
    
    return results


@job('low')
def cleanup_old_segments(video_id, days_old=7):
    """
    Clean up old HLS segments (low priority maintenance task)
    """
    try:
        import shutil
        from datetime import datetime, timedelta
        
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id))
        
        if not os.path.exists(hls_dir):
            return True
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        for resolution_dir in os.listdir(hls_dir):
            resolution_path = os.path.join(hls_dir, resolution_dir)
            
            if os.path.isdir(resolution_path):
                for segment_file in os.listdir(resolution_path):
                    if segment_file.endswith('.ts'):
                        segment_path = os.path.join(resolution_path, segment_file)
                        
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(segment_path))
                        
                        if file_mtime < cutoff_date:
                            os.remove(segment_path)
                            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old segments for video {video_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up segments for video {video_id}: {str(e)}")
        return False


@job('default')
def regenerate_hls_stream(video_id, resolution='720p', force=False):
    """
    Regenerate HLS stream for a video (useful for quality updates)
    """
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.video_file:
            logger.error(f"Video {video_id} has no video file")
            return False
        
        if force:
            hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id), resolution)
            if os.path.exists(hls_dir):
                import shutil
                shutil.rmtree(hls_dir)
                logger.info(f"Removed existing {resolution} stream for video {video_id}")
        
        return process_video_upload.delay(video_id, resolution)
        
    except Video.DoesNotExist:
        logger.error(f"Video {video_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error regenerating HLS stream for video {video_id}: {str(e)}")
        return False


def handle_failed_job(job, *exc_info):
    """
    Handle failed RQ jobs
    """
    logger.error(f"Job {job.id} failed: {exc_info}")    
    return False


def get_queue_stats():
    """
    Get statistics about RQ queues
    """
    from django_rq import get_queue
    
    stats = {}
    
    for queue_name in ['default', 'high', 'low']:
        queue = get_queue(queue_name)
        stats[queue_name] = {
            'count': len(queue),
            'jobs': [job.id for job in queue.jobs]
        }
    
    return stats


def clear_all_queues():
    """
    Clear all RQ queues (useful for development/testing)
    """
    from django_rq import get_queue
    
    for queue_name in ['default', 'high', 'low']:
        queue = get_queue(queue_name)
        queue.empty()
        logger.info(f"Cleared {queue_name} queue")


def retry_failed_jobs():
    """
    Retry all failed jobs (useful for recovery)
    """
    from django_rq import get_queue
    
    retry_count = 0
    
    for queue_name in ['default', 'high', 'low']:
        queue = get_queue(queue_name)
        
        for job in queue.failed_job_registry:
            try:
                job.requeue()
                retry_count += 1
            except Exception as e:
                logger.error(f"Failed to requeue job {job.id}: {str(e)}")
    
    logger.info(f"Retried {retry_count} failed jobs")
    return retry_count
