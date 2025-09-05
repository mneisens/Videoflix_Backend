from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid

def send_activation_email(user, request):
    """
    Sendet eine Aktivierungs-E-Mail synchron an den Benutzer
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starte synchronen E-Mail-Versand für Benutzer: {user.email}")
        
        # Backend-URL für Aktivierung generieren
        backend_url = f"{request.scheme}://{request.get_host()}"
        activation_url = f"{backend_url}/api/activate/{user.id}/{user.activation_token}/"
        logger.info(f"Aktivierungs-URL: {activation_url}")
        
        html_message = render_to_string('video/activation_email.html', {
            'user': user,
            'activation_url': activation_url,
        })
        plain_message = strip_tags(html_message)
        
        # E-Mail-Konfiguration loggen
        logger.info(f"E-Mail-Konfiguration:")
        logger.info(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        logger.info(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        logger.info(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        logger.info(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        logger.info(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        logger.info(f"  Empfänger: {user.email}")
        
        result = send_mail(
            subject='Videoflix - Aktivieren Sie Ihr Konto',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@videoflix.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"E-Mail-Versand erfolgreich: {result}")
        print(f"Aktivierungs-E-Mail erfolgreich an {user.email} gesendet")
        
    except Exception as e:
        error_msg = f"E-Mail-Versand fehlgeschlagen für {user.email}: {e}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        raise e

def send_password_reset_email(user, request):
    """
    Sendet eine Passwort-Reset-E-Mail synchron an den Benutzer
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starte synchronen Passwort-Reset-E-Mail-Versand für: {user.email}")
        

        frontend_url = "http://localhost:5500"  
        reset_url = f"{frontend_url}/pages/auth/confirm_password.html?uid={user.id}&token={user.password_reset_token}"
        logger.info(f"Reset-URL: {reset_url}")
        
        html_message = render_to_string('video/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
        })
        plain_message = strip_tags(html_message)
        
        result = send_mail(
            subject='Videoflix - Passwort zurücksetzen',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@videoflix.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Passwort-Reset-E-Mail erfolgreich gesendet: {result}")
        print(f"Passwort-Reset-E-Mail erfolgreich an {user.email} gesendet")
        
    except Exception as e:
        error_msg = f"Passwort-Reset-E-Mail-Versand fehlgeschlagen für {user.email}: {e}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        raise e
