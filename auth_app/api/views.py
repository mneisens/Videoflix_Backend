from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect
from django.conf import settings
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    LoginSerializer, 
    PasswordResetSerializer,
    PasswordConfirmSerializer
)
from ..models import CustomUser as User
from ..services import send_activation_email, send_password_reset_email
from ..utils import (
    get_user_by_id, validate_activation_token, activate_user, redirect_to_login,
    authenticate_user, create_login_response, set_auth_cookies,
    blacklist_refresh_token, create_logout_response, clear_auth_cookies,
    get_refresh_token, create_refresh_response, set_access_token_cookie,
    validate_password_reset_token, reset_user_password
)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            send_activation_email(user, request)
            
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
            user = get_user_by_id(uidb64)
            if isinstance(user, Response):
                return user
            
            validation_error = validate_activation_token(user, token)
            if validation_error:
                return validation_error
            
            if user.is_active:
                return Response({'message': 'Account already activated.'}, status=status.HTTP_200_OK)
            
            activate_user(user)
            return redirect_to_login(request)
            
        except Exception as e:
            return Response({'error': f'Fehler bei der Kontenaktivierung: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            user = authenticate_user(serializer, request)
            if isinstance(user, Response):
                return user
            
            refresh = RefreshToken.for_user(user)
            response = create_login_response(user, refresh)
            set_auth_cookies(response, refresh)
            
            return response
            
        except Exception as e:
            return Response({'error': f'Login-Fehler: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(generics.GenericAPIView):
    permission_classes = [AllowAny]  
    
    def post(self, request):
        try:
            blacklist_refresh_token(request)
            response = create_logout_response()
            clear_auth_cookies(response)
            return response
            
        except Exception as e:
            response = create_logout_response()
            clear_auth_cookies(response)
            return response

class TokenRefreshView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            refresh_token = get_refresh_token(request)
            if isinstance(refresh_token, Response):
                return refresh_token
            
            token = RefreshToken(refresh_token)
            response = create_refresh_response(token)
            set_access_token_cookie(response, token)
            
            return response
            
        except TokenError:
            return Response({'error': 'Ungültiger Refresh-Token.'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': f'Token-Refresh-Fehler: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Token generieren bevor E-Mail gesendet wird
        user.generate_password_reset_token()
        
        try:
            send_password_reset_email(user, request)
        except Exception as e:
            return Response({'error': 'Fehler beim Versenden der E-Mail. Bitte versuchen Sie es erneut.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)

class PasswordConfirmView(generics.GenericAPIView):
    serializer_class = PasswordConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = get_user_by_id(uidb64)
            if isinstance(user, Response):
                return user
            
            validation_error = validate_password_reset_token(user, token)
            if validation_error:
                return validation_error
            
            reset_user_password(user, serializer.validated_data['new_password'])
            
            return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Passwort-Reset-Fehler: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token})
