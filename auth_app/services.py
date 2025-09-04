from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid

def send_activation_email(user, request):
    """
    Sendet eine Aktivierungs-E-Mail asynchron an den Benutzer
    """
    from .tasks import send_activation_email_async
    
    request_data = {
        'scheme': request.scheme,
        'host': request.get_host()
    }

    send_activation_email_async.delay(user.id, request_data)

def send_password_reset_email(user, request):
    """
    Sendet eine Passwort-Reset-E-Mail asynchron an den Benutzer
    """
    from .tasks import send_password_reset_email_async
    
    # Request-Daten für asynchronen Task sammeln
    request_data = {
        'scheme': request.scheme,
        'host': request.get_host()
    }
    
    # E-Mail asynchron versenden
    send_password_reset_email_async.delay(user.id, request_data)
