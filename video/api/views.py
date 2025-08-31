import os
import re
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    LoginSerializer, 
    PasswordResetSerializer,
    PasswordConfirmSerializer,
    VideoSerializer
)
from ..models import CustomUser as User, Video
from ..services import send_activation_email, send_password_reset_email
from .authentication import CustomJWTAuthentication

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
            
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            
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
    authentication_classes = [CustomJWTAuthentication] 
    
    def get_queryset(self):
        """Gibt nur aktive Videos zurück"""
        return Video.objects.filter(is_active=True)

class HLSManifestView(APIView):
    """View für HLS-Manifest - erstellt ein korrektes HLS-Manifest für das Frontend"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]
    
    def get(self, request, movie_id, resolution):
        """Gibt ein HLS-Manifest zurück, das zu den echten Videos weiterleitet"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            if not video.get_video_url():
                return Response({
                    'error': 'Kein Video für diesen Film verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
            

            if video.video_file:
                file_size = video.video_file.size
                estimated_duration = max(1, file_size / (1024 * 1024) * 8)
            else:
                estimated_duration = 60  

            base_url = request.build_absolute_uri('/').rstrip('/')
            manifest_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:{int(estimated_duration)}
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:{estimated_duration:.1f},
{base_url}/api/video/{movie_id}/{resolution}/segment_001.ts
#EXT-X-ENDLIST
"""
            
            response = HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response['Content-Disposition'] = f'attachment; filename="{video.title}_{resolution}.m3u8"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Fehler beim Generieren des HLS-Manifests: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HLSVideoSegmentView(APIView):
    """View für HLS-Video-Segmente - simuliert .ts Segmente"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]
    
    def get(self, request, movie_id, resolution, segment_name):
        """Gibt ein HLS-Video-Segment zurück"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            
            if not video.get_video_url():
                return Response({
                    'error': 'Kein Video für diesen Film verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if video.video_file:
                file_path = video.video_file.path
                file_size = os.path.getsize(file_path)
                
                range_header = request.META.get('HTTP_RANGE', '').strip()
                range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
                
                if range_match:
                    first_byte, last_byte = range_match.groups()
                    first_byte = int(first_byte)
                    last_byte = int(last_byte) if last_byte else file_size - 1
                    
                    if first_byte >= file_size:
                        return Response(status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
                    
                    length = last_byte - first_byte + 1
                    
                    with open(file_path, 'rb') as f:
                        f.seek(first_byte)
                        data = f.read(length)
                    
                    response = HttpResponse(data, content_type='video/mp4', status=status.HTTP_206_PARTIAL_CONTENT)
                    response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
                    response['Content-Length'] = str(length)
                else:
                    response = FileResponse(video.video_file, content_type='video/mp4')
                
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Range'
                response['Accept-Ranges'] = 'bytes'
                response['Content-Disposition'] = f'attachment; filename="{segment_name}"'
                return response
            
            elif video.video_url:
                response = HttpResponseRedirect(video.video_url)
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return response
            
            else:
                return Response({
                    'error': 'Kein Video verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des Video-Segments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VideoStreamView(APIView):
    """View für Video-Streaming - nutzt die vorhandenen Video-Felder"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]
    
    def get(self, request, movie_id, resolution):
        """Gibt das Video zurück (entweder lokale Datei oder URL)"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            
            if not video.get_video_url():
                return Response({
                    'error': 'Kein Video für diesen Film verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if video.video_file:
                return FileResponse(video.video_file, content_type='video/mp4')
            
            elif video.video_url:
                return HttpResponseRedirect(video.video_url)
            
            else:
                return Response({
                    'error': 'Kein Video verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des Videos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VideoView(APIView):
    """Einfache Video-View für direktes MP4-Streaming"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]
    
    def get(self, request, movie_id, resolution):
        """Gibt das Video direkt als MP4-Stream zurück"""
        try:
            video = get_object_or_404(Video, id=movie_id, is_active=True)
            
            if not video.get_video_url():
                return Response({
                    'error': 'Kein Video für diesen Film verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if video.video_file:
                response = FileResponse(video.video_file, content_type='video/mp4')
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Range'
                response['Accept-Ranges'] = 'bytes'
                return response
            
            elif video.video_url:
                response = HttpResponseRedirect(video.video_url)
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return response
            
            else:
                return Response({
                    'error': 'Kein Video verfügbar.'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': f'Fehler beim Laden des Videos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Gibt einen CSRF-Token zurück"""
        from django.middleware.csrf import get_token
        get_token(request)
        return Response({
            'csrf_token': request.META.get('CSRF_COOKIE', ''),
        }, status=status.HTTP_200_OK)