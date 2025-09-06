"""
Helper functions for the Auth app
"""
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import CustomUser as User


def get_user_by_id(uidb64):
    """
    Retrieves a user by ID
    """
    try:
        user_id = int(uidb64)
        return User.objects.get(id=user_id)
    except (ValueError, User.DoesNotExist):
        return Response({'error': 'Benutzer nicht gefunden.'}, status=status.HTTP_400_BAD_REQUEST)


def validate_activation_token(user, token):
    """
    Validates the activation token
    """
    if str(user.activation_token) != token:
        return Response({'error': 'Ungültiger Aktivierungstoken.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if user.is_activation_token_expired():
        return Response({'error': 'Aktivierungstoken ist abgelaufen. Bitte registrieren Sie sich erneut.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return None


def activate_user(user):
    """
    Activates a user
    """
    user.is_active = True
    user.clear_activation_token()
    user.save()


def redirect_to_login(request):
    """
    Creates a redirect to the login page
    """
    frontend_url = "http://localhost:5500"
    if request.get_host().startswith('127.0.0.1'):
        frontend_url = "http://127.0.0.1:5500"
    return HttpResponseRedirect(f"{frontend_url}/pages/auth/login.html?message=activation_success")


def authenticate_user(serializer, request):
    """
    Authenticates a user
    """
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    user = authenticate(request, email=email, password=password)
    
    if user is None:
        return Response({'error': 'Ungültige Anmeldedaten.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({'error': 'Konto ist nicht aktiviert. Bitte aktivieren Sie Ihr Konto zuerst.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    return user


def create_login_response(user, refresh):
    """
    Creates a login response
    """
    from .api.serializers import UserSerializer
    return Response({
        'detail': 'Login successful!',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    }, status=status.HTTP_200_OK)


def set_auth_cookies(response, refresh):
    """
    Sets the authentication cookies
    """
    set_access_token_cookie(response, refresh)
    set_refresh_token_cookie(response, refresh)


def set_access_token_cookie(response, refresh):
    """
    Sets the access token cookie
    """
    response.set_cookie(
        'access_token',
        str(refresh.access_token),
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
    )


def set_refresh_token_cookie(response, refresh):
    """
    Sets the refresh token cookie
    """
    response.set_cookie(
        'refresh_token',
        str(refresh),
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
    )


def blacklist_refresh_token(request):
    """
    Blacklists the refresh token
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass


def create_logout_response():
    """
    Creates a logout response
    """
    return Response({'detail': 'Logout successful! All tokens will be deleted.'}, status=status.HTTP_200_OK)


def clear_auth_cookies(response):
    """
    Clears the authentication cookies
    """
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')


def get_refresh_token(request):
    """
    Retrieves the refresh token from cookies
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({'error': 'Refresh-Token fehlt.'}, status=status.HTTP_400_BAD_REQUEST)
    return refresh_token


def create_refresh_response(token):
    """
    Creates a token refresh response
    """
    return Response({
        'detail': 'Token refreshed',
        'access': str(token.access_token)
    }, status=status.HTTP_200_OK)


def validate_password_reset_token(user, token):
    """
    Validates the password reset token
    """
    if str(user.password_reset_token) != token:
        return Response({'error': 'Ungültiger Passwort-Reset-Token.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if user.is_password_reset_token_expired():
        return Response({'error': 'Passwort-Reset-Token ist abgelaufen. Bitte fordern Sie einen neuen an.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return None


def reset_user_password(user, new_password):
    """
    Sets a new password for the user
    """
    user.set_password(new_password)
    user.clear_password_reset_token()
    user.save()
