from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Die E-Mail-Adresse ist erforderlich.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser muss is_staff=True haben.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser muss is_superuser=True haben.')
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    activation_token = models.UUIDField(null=True, blank=True, editable=False)
    activation_token_created = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.UUIDField(null=True, blank=True, editable=False)
    password_reset_token_created = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager() 
    
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
