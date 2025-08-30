from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, UserSerializer
from ..services import send_activation_email

@api_view(['GET'])
@permission_classes([AllowAny])
def test_view(request):
    """
    Einfache Test-View
    """
    return Response({"message": "Test view works!"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Registriert einen neuen Benutzer und sendet eine Aktivierungs-E-Mail
    """
    print("DEBUG: register_user called")
    
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        print("DEBUG: Serializer is valid")
        user = serializer.save()
        print(f"DEBUG: User created with ID {user.id}")
        
        try:
            send_activation_email(user, request)
            print("DEBUG: Activation email sent")  
        except Exception as e:
            print(f"DEBUG: Email error: {e}")

            user.delete()
            return Response({
                'error': 'Fehler beim Versenden der Aktivierungs-E-Mail. Bitte versuchen Sie es erneut.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        user_data = UserSerializer(user).data
        response_data = {
            'user': user_data,
            'token': str(user.activation_token)
        }
        
        print(f"DEBUG: Response data: {response_data}") 
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        print(f"DEBUG: Serializer errors: {serializer.errors}") 
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
