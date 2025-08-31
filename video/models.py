from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    activation_token = models.UUIDField(null=True, blank=True, editable=False)
    activation_token_created = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.UUIDField(null=True, blank=True, editable=False)
    password_reset_token_created = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 
    
    def __str__(self):
        return self.email
    
    def generate_activation_token(self):
        """Generiert einen neuen Aktivierungstoken"""
        self.activation_token = uuid.uuid4()
        self.activation_token_created = timezone.now()
        self.save()
        return self.activation_token
    
    def is_activation_token_expired(self):
        """Prüft ob der Aktivierungstoken abgelaufen ist (24 Stunden)"""
        if not self.activation_token_created:
            return True
        return timezone.now() > self.activation_token_created + timezone.timedelta(hours=24)
    
    def clear_activation_token(self):
        """Löscht den Aktivierungstoken"""
        self.activation_token = None
        self.activation_token_created = None
        self.save()
    
    def generate_password_reset_token(self):
        """Generiert einen neuen Passwort-Reset-Token"""
        self.password_reset_token = uuid.uuid4()
        self.password_reset_token_created = timezone.now()
        self.save()
        return self.password_reset_token
    
    def is_password_reset_token_expired(self):
        """Prüft ob der Passwort-Reset-Token abgelaufen ist (1 Stunde)"""
        if not self.password_reset_token_created:
            return True
        return timezone.now() > self.password_reset_token_created + timezone.timedelta(hours=1)
    
    def clear_password_reset_token(self):
        """Löscht den Passwort-Reset-Token"""
        self.password_reset_token = None
        self.password_reset_token_created = None
        self.save()

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
