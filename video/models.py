from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

class Video(models.Model):
    """Video model for the Videoflix application"""
    CATEGORY_CHOICES = [
        ('action', 'Action'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('romance', 'Romance'),
        ('sci-fi', 'Science Fiction'),
        ('thriller', 'Thriller'),
        ('documentary', 'Documentary'),
        ('animation', 'Animation'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, help_text='Thumbnail image (320x180px recommended)')
    thumbnail_url = models.URLField(blank=True, null=True, help_text='Alternative: Thumbnail URL')
    poster = models.ImageField(upload_to='posters/', blank=True, null=True, help_text='Poster image (1280x720px recommended)')
    background = models.ImageField(upload_to='backgrounds/', blank=True, null=True, help_text='Background image (1920x1080px recommended)')
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, help_text='Video file (MP4 recommended)')
    video_url = models.URLField(blank=True, null=True, help_text='Alternative: Video URL')
    duration = models.IntegerField(help_text='Duration in seconds', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_thumbnail_url(self):
        """Returns the thumbnail URL (prioritizes local file)"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.thumbnail_url:
            return self.thumbnail_url
        return None
    
    def get_poster_url(self):
        """Returns the poster URL"""
        if self.poster:
            return self.poster.url
        return None
    
    def get_background_url(self):
        """Returns the background URL"""
        if self.background:
            return self.background.url
        return None
    
    def get_video_url(self):
        """Returns the video URL (prioritizes local file)"""
        if self.video_file:
            return self.video_file.url
        elif self.video_url:
            return self.video_url
        return None


@receiver(post_save, sender=Video)
def create_hls_segments_on_video_save(sender, instance, created, **kwargs):
    """
    Signal handler: Automatically creates HLS segments synchronously when a video is saved
    """
    if instance.video_file and instance.video_file.name:
        try:
            from .services import create_hls_stream, extract_video_thumbnail
            import os
            
            video_path = instance.video_file.path
            
            if os.path.exists(video_path):
                resolutions = ['480p', '720p', '1080p']
                for resolution in resolutions:
                    result = create_hls_stream(video_path, instance.id, resolution)
                    if result.get('success'):
                        print(f"HLS segments for video {instance.id} ({resolution}) created successfully")
                    else:
                        print(f"Error creating HLS segments for video {instance.id} ({resolution}): {result.get('error')}")
                
                if created and (not instance.thumbnail and not instance.thumbnail_url):
                    thumbnail_result = extract_video_thumbnail(video_path, instance.id)
                    if thumbnail_result.get('success'):
                        instance.thumbnail = thumbnail_result['thumbnail_path']
                        instance.save(update_fields=['thumbnail'])
                        print(f"Thumbnail for video {instance.id} created successfully: {thumbnail_result['thumbnail_path']}")
                    else:
                        print(f"Error creating thumbnail for video {instance.id}: {thumbnail_result.get('error')}")
                elif not created and (not instance.thumbnail and not instance.thumbnail_url):
                    thumbnail_result = extract_video_thumbnail(video_path, instance.id)
                    if thumbnail_result.get('success'):
                        instance.thumbnail = thumbnail_result['thumbnail_path']
                        instance.save(update_fields=['thumbnail'])
                        print(f"Thumbnail for video {instance.id} created successfully: {thumbnail_result['thumbnail_path']}")
                    else:
                        print(f"Error creating thumbnail for video {instance.id}: {thumbnail_result.get('error')}")
                
                cache.delete('video_list_public')
            else:
                print(f"Video file not found: {video_path}")
            
        except Exception as e:
            print(f"Error in signal handler for video {instance.id}: {str(e)}")


@receiver(post_delete, sender=Video)
def clear_cache_on_video_delete(sender, instance, **kwargs):
    """
    Signal handler: Clears cache when a video is deleted
    """
    try:
        cache.delete('video_list_public')
        print(f"Cache cleared after deletion of video {instance.id}")
    except Exception as e:
        print(f"Error clearing cache after video deletion: {str(e)}")
