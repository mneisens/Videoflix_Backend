from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer, PasswordResetSerializer, PasswordConfirmSerializer
from ..services import send_activation_email, send_password_reset_email
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
import uuid

User = get_user_model()

class TestView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({"message": "Test view works!"}, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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

class ActivateAccountView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, uidb64, token):
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

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
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

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh-Token fehlt.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            response = Response({
                'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'
            }, status=status.HTTP_200_OK)
            
            jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
            
            response.delete_cookie(
                jwt_settings.get('AUTH_COOKIE', 'access_token'),
                path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
                domain=jwt_settings.get('AUTH_COOKIE_DOMAIN', None)
            )
            
            response.delete_cookie(
                jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
                path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
                domain=jwt_settings.get('AUTH_COOKIE_DOMAIN', None)
            )
            
            return response
            
        except TokenError:
            return Response({
                'error': 'Ungültiger Refresh-Token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Fehler beim Logout.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh-Token fehlt.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            
            response = Response({
                'detail': 'Token refreshed',
                'access': new_access_token
            }, status=status.HTTP_200_OK)
            
            jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
            
            response.set_cookie(
                jwt_settings.get('AUTH_COOKIE', 'access_token'),
                new_access_token,
                httponly=jwt_settings.get('AUTH_COOKIE_HTTP_ONLY', True),
                secure=jwt_settings.get('AUTH_COOKIE_SECURE', False),
                samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
                max_age=jwt_settings.get('ACCESS_TOKEN_LIFETIME', 3600).total_seconds(),
                path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
                domain=jwt_settings.get('AUTH_COOKIE_DOMAIN', None)
            )
            
            return response
            
        except TokenError:
            return Response({
                'error': 'Ungültiger Refresh-Token.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'error': 'Fehler beim Token-Refresh.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        reset_token = user.generate_password_reset_token()
        
        try:
            send_password_reset_email(user, request)
        except Exception as e:
            return Response({
                'error': 'Fehler beim Versenden der E-Mail. Bitte versuchen Sie es erneut.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'detail': 'An email has been sent to reset your password.'
        }, status=status.HTTP_200_OK)

class PasswordConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token):
        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user_id = int(uidb64)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': 'Benutzer nicht gefunden.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if str(user.password_reset_token) != token:
                return Response({
                    'error': 'Ungültiger Passwort-Reset-Token.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if user.is_password_reset_token_expired():
                return Response({
                    'error': 'Passwort-Reset-Token ist abgelaufen. Bitte fordern Sie einen neuen an.'
                }, status=status.HTTP_400_BAD_REQUEST)
          
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            
       
            user.clear_password_reset_token()
            
            user.save()
            
            return Response({
                'detail': 'Your Password has been successfully reset.'
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                'error': 'Ungültige Benutzer-ID.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Fehler bei der Passwort-Änderung.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)