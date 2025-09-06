from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The email address is required.')
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
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
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
        """Generates a new activation token"""
        self.activation_token = uuid.uuid4()
        self.activation_token_created = timezone.now()
        self.save()
        return self.activation_token
    
    def is_activation_token_expired(self):
        """Checks if the activation token is expired (24 hours)"""
        if not self.activation_token_created:
            return True
        return timezone.now() > self.activation_token_created + timezone.timedelta(hours=24)
    
    def clear_activation_token(self):
        """Clears the activation token"""
        self.activation_token = None
        self.activation_token_created = None
        self.save()
    
    def generate_password_reset_token(self):
        """Generates a new password reset token"""
        self.password_reset_token = uuid.uuid4()
        self.password_reset_token_created = timezone.now()
        self.save()
        return self.password_reset_token
    
    def is_password_reset_token_expired(self):
        """Checks if the password reset token is expired (1 hour)"""
        if not self.password_reset_token_created:
            return True
        return timezone.now() > self.password_reset_token_created + timezone.timedelta(hours=1)
    
    def clear_password_reset_token(self):
        """Clears the password reset token"""
        self.password_reset_token = None
        self.password_reset_token_created = None
        self.save()
