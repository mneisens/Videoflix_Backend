from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer, PasswordResetSerializer, PasswordConfirmSerializer, VideoSerializer
from ..services import send_activation_email, send_password_reset_email
from ..models import Video
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
        try:
            from django.middleware.csrf import get_token
            get_token(request)
            
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
                'token': str(user.activation_token),
                'message': 'Registrierung erfolgreich! Bitte überprüfen Sie Ihre E-Mail.'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Registrierungsfehler: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

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
                frontend_url = "http://localhost:5500"
                if request.get_host().startswith('127.0.0.1'):
                    frontend_url = "http://127.0.0.1:5500"
                
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(f"{frontend_url}/pages/auth/login.html?message=already_activated")
            
    
            user.is_active = True
            user.clear_activation_token() 
            user.save()
            

            frontend_url = "http://localhost:5500"
            if request.get_host().startswith('127.0.0.1'):
                frontend_url = "http://127.0.0.1:5500"
            
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(f"{frontend_url}/pages/auth/login.html?message=activation_success")
            
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
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, email=email, password=password)
            
            if user is None:
                return Response({
                    'error': 'Ungültige Anmeldedaten.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    'error': 'Konto ist nicht aktiviert. Bitte aktivieren Sie Ihr Konto zuerst.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            refresh = RefreshToken.for_user(user)
            
            response = Response({
                'detail': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email
                },
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh) 
            }, status=status.HTTP_200_OK)
            
            response.set_cookie(
                'access_token',
                str(refresh.access_token),
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
            )
            
            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
            )
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Login-Fehler: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if not refresh_token:
                return Response({
                    'error': 'Refresh-Token fehlt.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response({
                'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'
            }, status=status.HTTP_200_OK)
            
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
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
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if not refresh_token:
                return Response({
                    'error': 'Refresh-Token fehlt.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            
            response = Response({
                'detail': 'Token refreshed',
                'access': str(token.access_token)
            }, status=status.HTTP_200_OK)
            
            response.set_cookie(
                'access_token',
                str(token.access_token),
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
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
            
            # Neues Passwort setzen
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            
            # Token löschen
            user.clear_password_reset_token()
            
            user.save()
            
            return Response({
                'message': 'Passwort erfolgreich geändert!'
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                'error': 'Ungültige Benutzer-ID.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Fehler bei der Passwort-Änderung.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VideoListView(generics.ListAPIView):
    """View für die Video-Liste"""
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 
    
    def get_queryset(self):
        """Gibt nur aktive Videos zurück"""
        return Video.objects.filter(is_active=True)

class HLSMasterPlaylistView(APIView):
    """View für HLS Master Playlist"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, movie_id, resolution):
        """Gibt die HLS Master Playlist für ein Video zurück"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            available_resolutions = ['1080p', '720p', '480p', '360p']
            
            if resolution not in available_resolutions:
                return Response({
                    'error': f'Auflösung {resolution} ist nicht verfügbar. Verfügbare Auflösungen: {", ".join(available_resolutions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            playlist_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2"
/api/video/{movie_id}/1080p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720,CODECS="avc1.64001f,mp4a.40.2"
/api/video/{movie_id}/720p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480,CODECS="avc1.64001e,mp4a.40.2"
/api/video/{movie_id}/480p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.64001e,mp4a.40.2"
/api/video/{movie_id}/360p/index.m3u8
"""
            
            response = HttpResponse(playlist_content, content_type='application/vnd.apple.mpegurl')
            response['Content-Disposition'] = f'attachment; filename="{video.title}_{resolution}_master.m3u8"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Fehler beim Generieren der HLS Master Playlist: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HLSVideoSegmentView(APIView):
    """View für HLS Video Segmente"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, movie_id, resolution, segment):
        """Gibt ein HLS Video Segment zurück"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            available_resolutions = ['1080p', '720p', '480p', '360p']
            
            if resolution not in available_resolutions:
                return Response({
                    'error': f'Auflösung {resolution} ist nicht verfügbar. Verfügbare Auflösungen: {", ".join(available_resolutions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not segment.endswith('.ts') or not segment.startswith('segment_'):
                return Response({
                    'error': 'Ungültiges Segment-Format. Erwartet: segment_XXX.ts'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            segment_content = f"""# Mock HLS Video Segment für {video.title} - {resolution}
# Segment: {segment}
# Video ID: {movie_id}
# Dies ist ein Demo-Segment. In der Praxis würde hier ein echtes .ts Video-Segment stehen.
"""
            
            response = HttpResponse(segment_content, content_type='video/mp2t')
            response['Content-Disposition'] = f'attachment; filename="{segment}"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des Video-Segments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DebugView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Debug-View um zu sehen, was das Frontend sendet"""
        return Response({
            'received_data': request.data,
            'headers': dict(request.headers),
            'method': request.method,
            'content_type': request.content_type,
        }, status=status.HTTP_200_OK)

class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Gibt einen CSRF-Token zurück"""
        from django.middleware.csrf import get_token
        get_token(request)
        return Response({
            'csrf_token': request.META.get('CSRF_COOKIE', ''),
        }, status=status.HTTP_200_OK)