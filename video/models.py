from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    # E-Mail als Hauptidentifikator verwenden
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Aktivierungsfelder
    activation_token = models.UUIDField(null=True, blank=True, editable=False)
    activation_token_created = models.DateTimeField(null=True, blank=True)
    
    # Passwort-Reset-Felder
    password_reset_token = models.UUIDField(null=True, blank=True, editable=False)
    password_reset_token_created = models.DateTimeField(null=True, blank=True)
    
    # E-Mail als USERNAME_FIELD verwenden
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
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
    thumbnail_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    duration = models.IntegerField(help_text='Duration in seconds', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
