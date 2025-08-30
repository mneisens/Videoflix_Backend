from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid

def send_activation_email(user, request):
    """
    Sendet eine Aktivierungs-E-Mail an den Benutzer
    """
    # Aktivierungs-URL erstellen
    activation_url = f"{request.scheme}://{request.get_host()}/api/activate/{user.id}/{user.activation_token}/"
    
    # HTML-E-Mail-Template rendern
    html_message = render_to_string('video/activation_email.html', {
        'user': user,
        'activation_url': activation_url,
    })
    
    # Plain-Text-Version erstellen
    plain_message = strip_tags(html_message)
    
    # E-Mail senden
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
    # Passwort-Reset-URL erstellen
    reset_url = f"{request.scheme}://{request.get_host()}/api/password_confirm/{user.id}/{user.password_reset_token}/"
    
    # HTML-E-Mail-Template rendern
    html_message = render_to_string('video/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    # Plain-Text-Version erstellen
    plain_message = strip_tags(html_message)
    
    # E-Mail senden
    send_mail(
        subject='Videoflix - Passwort zurücksetzen',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@videoflix.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
