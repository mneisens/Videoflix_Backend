from django_rq import job
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

User = get_user_model()

@job('default')
def send_activation_email_async(user_id, request_data):
    """
    Asynchroner E-Mail-Versand für Benutzeraktivierung
    """
    try:
        user = User.objects.get(id=user_id)
        
        class MockRequest:
            def __init__(self, data):
                self.scheme = data.get('scheme', 'http')
                self.get_host = lambda: data.get('host', 'localhost:8000')
        
        mock_request = MockRequest(request_data)

        activation_url = f"{mock_request.scheme}://{mock_request.get_host()}/api/activate/{user.id}/{user.activation_token}/"
        
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
        
        print(f"Aktivierungs-E-Mail erfolgreich an {user.email} gesendet")
        
    except User.DoesNotExist:
        print(f"Benutzer mit ID {user_id} nicht gefunden - E-Mail nicht gesendet")
    except Exception as e:
        print(f"E-Mail-Versand fehlgeschlagen für Benutzer {user_id}: {e}")

@job('default')
def send_password_reset_email_async(user_id, request_data):
    """
    Asynchroner E-Mail-Versand für Passwort-Reset
    """
    try:
        user = User.objects.get(id=user_id)
        

        class MockRequest:
            def __init__(self, data):
                self.scheme = data.get('scheme', 'http')
                self.get_host = lambda: data.get('host', 'localhost:8000')
        
        mock_request = MockRequest(request_data)
        

        reset_url = f"{mock_request.scheme}://{mock_request.get_host()}/api/password-reset/{user.id}/{user.password_reset_token}/"
        
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
        
        print(f"Passwort-Reset-E-Mail erfolgreich an {user.email} gesendet")
        
    except User.DoesNotExist:
        print(f"Benutzer mit ID {user_id} nicht gefunden - E-Mail nicht gesendet")
    except Exception as e:
        print(f"E-Mail-Versand fehlgeschlagen für Benutzer {user_id}: {e}")
