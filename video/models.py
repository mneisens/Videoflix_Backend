from django.db import models

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
