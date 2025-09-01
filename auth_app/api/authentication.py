from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings


class CustomJWTAuthentication(JWTAuthentication):
    """
    Benutzerdefinierte JWT-Authentication, die sowohl Cookies als auch Authorization-Header unterstützt
    """
    
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token
        
        access_token = request.COOKIES.get('access_token')
        if access_token:
            try:
                validated_token = self.get_validated_token(access_token)
                return self.get_user(validated_token), validated_token
            except (InvalidToken, TokenError):
                pass
        
        return None
    
    def get_validated_token(self, raw_token):
        """
        Validiert den Token und gibt ihn zurück
        """
        try:
            return AccessToken(raw_token)
        except (InvalidToken, TokenError) as e:
            raise InvalidToken(str(e))
