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
    PasswordConfirmSerializer
)
from ..models import CustomUser as User
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
                return Response({
                    'message': 'Account already activated.'
                }, status=status.HTTP_200_OK)
            
            user.is_active = True
            user.clear_activation_token() 
            user.save()      
            frontend_url = "http://localhost:5500"
            
            if request.get_host().startswith('127.0.0.1'):
                frontend_url = "http://127.0.0.1:5500"
            
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(f"{frontend_url}/pages/auth/login.html?message=activation_success")
            
        except Exception as e:
            return Response({
                'error': f'Fehler bei der Kontenaktivierung: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
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
                'detail': 'Login successful!',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(generics.GenericAPIView):
    permission_classes = [AllowAny]  
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    pass

            response = Response({
                'detail': 'Logout successful! All tokens will be deleted.'
            }, status=status.HTTP_200_OK)
            
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except Exception as e:
            response = Response({
                'detail': 'Logout completed. Cookies cleared.'
            }, status=status.HTTP_200_OK)
            
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response

class TokenRefreshView(generics.GenericAPIView):
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
                'error': f'Token-Refresh-Fehler: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
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

class PasswordConfirmView(generics.GenericAPIView):
    serializer_class = PasswordConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data)
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
                'detail': 'Password has been reset successfully.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Passwort-Reset-Fehler: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token})
