import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from auth_app.models import CustomUser


@pytest.mark.django_db
@pytest.mark.models
class CustomUserModelTests(TestCase):
    """Tests für das CustomUser-Model"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
    
    def test_custom_user_creation(self):
        """Test: CustomUser erstellen"""
        user = CustomUser.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_custom_user_required_fields(self):
        """Test: Erforderliche Felder für CustomUser"""
        with self.assertRaises(TypeError):  
            CustomUser.objects.create_user(
                username='testuser',
                password='testpass123'
            )

        user = CustomUser.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test2@example.com')
        self.assertIsNone(user.username)
    
    def test_custom_user_string_representation(self):
        """Test: String-Repräsentation des CustomUser"""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_custom_user_unique_email(self):
        """Test: Eindeutige E-Mail-Adressen"""
        email_field = CustomUser._meta.get_field('email')
        self.assertTrue(email_field.unique, "E-Mail-Feld sollte unique=True haben")
    
    def test_custom_user_superuser_creation(self):
        """Test: Superuser erstellen"""
        superuser = CustomUser.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
    
    def test_custom_user_get_full_name(self):
        """Test: Vollständiger Name"""
        user = CustomUser.objects.create_user(**self.user_data)
        
        self.assertEqual(user.get_full_name(), 'Test User')
    
    def test_custom_user_get_short_name(self):
        """Test: Kurzer Name"""
        user = CustomUser.objects.create_user(**self.user_data)
        
        self.assertEqual(user.get_short_name(), 'Test')
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        CustomUser.objects.all().delete()
