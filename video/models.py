from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

class Video(models.Model):
    """Video-Model für die Videoflix-Anwendung"""
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
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, help_text='Thumbnail-Bild (320x180px empfohlen)')
    thumbnail_url = models.URLField(blank=True, null=True, help_text='Alternative: Thumbnail-URL')
    poster = models.ImageField(upload_to='posters/', blank=True, null=True, help_text='Poster-Bild (1280x720px empfohlen)')
    background = models.ImageField(upload_to='backgrounds/', blank=True, null=True, help_text='Hintergrund-Bild (1920x1080px empfohlen)')
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, help_text='Video-Datei (MP4 empfohlen)')
    video_url = models.URLField(blank=True, null=True, help_text='Alternative: Video-URL')
    duration = models.IntegerField(help_text='Duration in seconds', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_thumbnail_url(self):
        """Gibt die Thumbnail-URL zurück (priorisiert lokale Datei)"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.thumbnail_url:
            return self.thumbnail_url
        return None
    
    def get_poster_url(self):
        """Gibt die Poster-URL zurück"""
        if self.poster:
            return self.poster.url
        return None
    
    def get_background_url(self):
        """Gibt die Background-URL zurück"""
        if self.background:
            return self.background.url
        return None
    
    def get_video_url(self):
        """Gibt die Video-URL zurück (priorisiert lokale Datei)"""
        if self.video_file:
            return self.video_file.url
        elif self.video_url:
            return self.video_url
        return None


@receiver(post_save, sender=Video)
def create_hls_segments_on_video_save(sender, instance, created, **kwargs):
    """
    Signal-Handler: Erstellt automatisch HLS-Segmente synchron wenn ein Video gespeichert wird
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
                        print(f"HLS-Segmente für Video {instance.id} ({resolution}) erfolgreich erstellt")
                    else:
                        print(f"Fehler beim Erstellen der HLS-Segmente für Video {instance.id} ({resolution}): {result.get('error')}")
                
                if created and (not instance.thumbnail and not instance.thumbnail_url):
                    thumbnail_result = extract_video_thumbnail(video_path, instance.id)
                    if thumbnail_result.get('success'):
                        instance.thumbnail = thumbnail_result['thumbnail_path']
                        instance.save(update_fields=['thumbnail'])
                        print(f"Thumbnail für Video {instance.id} erfolgreich erstellt: {thumbnail_result['thumbnail_path']}")
                    else:
                        print(f"Fehler beim Erstellen des Thumbnails für Video {instance.id}: {thumbnail_result.get('error')}")
                elif not created and (not instance.thumbnail and not instance.thumbnail_url):
                    thumbnail_result = extract_video_thumbnail(video_path, instance.id)
                    if thumbnail_result.get('success'):
                        instance.thumbnail = thumbnail_result['thumbnail_path']
                        instance.save(update_fields=['thumbnail'])
                        print(f"Thumbnail für Video {instance.id} erfolgreich erstellt: {thumbnail_result['thumbnail_path']}")
                    else:
                        print(f"Fehler beim Erstellen des Thumbnails für Video {instance.id}: {thumbnail_result.get('error')}")
                
                cache.delete('video_list_public')
            else:
                print(f"Video-Datei nicht gefunden: {video_path}")
            
        except Exception as e:
            print(f"Fehler im Signal-Handler für Video {instance.id}: {str(e)}")


@receiver(post_delete, sender=Video)
def clear_cache_on_video_delete(sender, instance, **kwargs):
    """
    Signal-Handler: Leert den Cache wenn ein Video gelöscht wird
    """
    try:
        cache.delete('video_list_public')
        print(f"Cache geleert nach Löschung von Video {instance.id}")
    except Exception as e:
        print(f"Fehler beim Leeren des Caches nach Video-Löschung: {str(e)}")
