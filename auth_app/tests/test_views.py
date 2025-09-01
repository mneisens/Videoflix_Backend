import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from auth_app.models import CustomUser


@pytest.mark.django_db
@pytest.mark.views
class AuthViewTests(APITestCase):
    """Tests für die Auth-Views"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword',
            is_active=True
        )
    
    def test_user_registration(self):
        """Test: Benutzerregistrierung"""
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirmed_password': 'newpass123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = CustomUser.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertFalse(user.is_active)  
    
    def test_user_login(self):
        """Test: Benutzer-Login"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test: Login mit ungültigen Anmeldedaten"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_csrf_token(self):
        """Test: CSRF-Token abrufen"""
        url = reverse('csrf_token')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrfToken', response.data)
    
    def test_user_logout(self):
        """Test: Benutzer-Logout"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('logout')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        CustomUser.objects.all().delete()
