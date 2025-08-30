from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer
from ..services import send_activation_email
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import uuid

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def test_view(request):
    return Response({"message": "Test view works!"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        try:
            send_activation_email(user, request)
        except Exception as e:
            user.delete()
            return Response({
                'error': 'Fehler beim Versenden der Aktivierungs-E-Mail. Bitte versuchen Sie es erneut.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        user_data = UserSerializer(user).data
        response_data = {
            'user': user_data,
            'token': str(user.activation_token)
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def activate_account(request, uidb64, token):
    try:
        user_id = int(uidb64)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'Benutzer nicht gefunden.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if str(user.activation_token) != token:
            return Response({
                'error': 'Ungültiger Aktivierungstoken.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_activation_token_expired():
            return Response({
                'error': 'Aktivierungstoken ist abgelaufen. Bitte registrieren Sie sich erneut.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_active:
            return Response({
                'message': 'Konto ist bereits aktiviert.'
            }, status=status.HTTP_200_OK)
        
        user.is_active = True
        user.save()
        
        return Response({
            'message': 'Account successfully activated.'
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Ungültige Benutzer-ID.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': 'Fehler bei der Kontoaktivierung.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, email=email, password=password)
        
        if user is None:
            return Response({
                'error': 'Ungültige E-Mail oder Passwort.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'Konto ist nicht aktiviert. Bitte aktivieren Sie Ihr Konto über den E-Mail-Link.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'detail': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.email
            }
        }, status=status.HTTP_200_OK)
        
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        
        response.set_cookie(
            jwt_settings.get('AUTH_COOKIE', 'access_token'),
            str(refresh.access_token),
            httponly=jwt_settings.get('AUTH_COOKIE_HTTP_ONLY', True),
            secure=jwt_settings.get('AUTH_COOKIE_SECURE', False),
            samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
            max_age=jwt_settings.get('ACCESS_TOKEN_LIFETIME', 3600).total_seconds(),
            path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
            domain=jwt_settings.get('AUTH_COOKIE_DOMAIN', None)
        )
        
        response.set_cookie(
            jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
            str(refresh),
            httponly=jwt_settings.get('AUTH_COOKIE_HTTP_ONLY', True),
            secure=jwt_settings.get('AUTH_COOKIE_SECURE', False),
            samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
            max_age=jwt_settings.get('REFRESH_TOKEN_LIFETIME', 86400).total_seconds(),
            path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
            domain=jwt_settings.get('AUTH_COOKIE_DOMAIN', None)
        )
        
        return response
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
