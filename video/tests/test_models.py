import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from video.models import Video


@pytest.mark.django_db
@pytest.mark.models
class VideoModelTests(TestCase):
    """Tests für das Video-Model"""
    
    def setUp(self):
        self.video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"fake video content",
            content_type="video/mp4"
        )
    
    def test_video_creation(self):
        """Test: Video erstellen"""
        video = Video.objects.create(
            title="Test Video",
            description="Test Description",
            category="action",
            duration=120,
            is_active=True
        )
        
        self.assertEqual(video.title, "Test Video")
        self.assertEqual(video.duration, 120)
        self.assertEqual(video.category, "action")
        self.assertTrue(video.is_active)
    
    def test_video_default_values(self):
        """Test: Standardwerte werden korrekt gesetzt"""
        video = Video.objects.create(
            title="Default Video",
            description="Default Description"
        )
        
        self.assertIsNone(video.duration)
        self.assertEqual(video.category, "other")
        self.assertTrue(video.is_active)
    
    def test_video_string_representation(self):
        """Test: String-Repräsentation"""
        video = Video.objects.create(
            title="String Video",
            description="String Description"
        )
        
        self.assertEqual(str(video), "String Video")
    
    def test_video_active_filter(self):
        """Test: Aktive Videos filtern"""
        Video.objects.create(
            title="Active Video",
            description="Active Description",
            is_active=True
        )
        
        Video.objects.create(
            title="Inactive Video",
            description="Inactive Description",
            is_active=False
        )
        
        active_videos = Video.objects.filter(is_active=True)
        self.assertEqual(active_videos.count(), 1)
        self.assertEqual(active_videos.first().title, "Active Video")
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
        Video.objects.all().delete()
