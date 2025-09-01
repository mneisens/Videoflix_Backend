from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid

def send_activation_email(user, request):
    """
    Sendet eine Aktivierungs-E-Mail an den Benutzer
    """
    activation_url = f"{request.scheme}://{request.get_host()}/api/activate/{user.id}/{user.activation_token}/"
    
    html_message = render_to_string('video/activation_email.html', {
        'user': user,
        'activation_url': activation_url,
    })
    plain_message = strip_tags(html_message)
    
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
    frontend_url = "http://localhost:5500"
    if request.get_host().startswith('127.0.0.1'):
        frontend_url = "http://127.0.0.1:5500"
    
    reset_url = f"{frontend_url}/pages/auth/confirm_password.html?uid={user.id}&token={user.password_reset_token}"
    
    html_message = render_to_string('video/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Videoflix - Passwort zurücksetzen',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@videoflix.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
