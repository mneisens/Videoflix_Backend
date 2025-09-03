from django.db import models
from django.db.models.signals import post_save
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
    Signal-Handler: Erstellt automatisch HLS-Segmente wenn ein Video gespeichert wird
    """
    if instance.video_file and instance.video_file.name:
        try:
            from .services import create_hls_stream
            resolutions = ['480p', '720p', '1080p']
            
            for resolution in resolutions:
                try:
                    result = create_hls_stream(instance.video_file.path, instance.id, resolution)
                    if result['success']:
                        print(f" HLS-Segmente für Video {instance.id} ({resolution}) erfolgreich erstellt")
                    else:
                        print(f" Fehler beim Erstellen der HLS-Segmente für Video {instance.id} ({resolution}): {result['error']}")
                except Exception as e:
                    print(f" Exception beim Erstellen der HLS-Segmente für Video {instance.id} ({resolution}): {str(e)}")
            cache.delete('video_list_public')
            
        except Exception as e:
            print(f"Fehler im Signal-Handler für Video {instance.id}: {str(e)}")
