import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from video.models import Video
from video.api.serializers import VideoSerializer


@pytest.mark.django_db
@pytest.mark.serializers
class VideoSerializerTests(TestCase):
    """Tests für den VideoSerializer"""
    
    def setUp(self):
        self.video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"fake video content",
            content_type="video/mp4"
        )
        
        self.video = Video.objects.create(
            title="Test Video",
            description="Test Description",
            category="action",
            duration=120,
            is_active=True
        )
    
    def test_video_serializer_fields(self):
        """Test: Alle erwarteten Felder sind im Serializer vorhanden"""
        serializer = VideoSerializer(self.video)
        data = serializer.data
        
        expected_fields = {
            'id', 'title', 'description', 'category', 'duration',
            'thumbnail_url', 'poster_url', 'background_url',
            'video_url', 'direct_video_url', 'created_at', 'updated_at'
        }
        
        # Prüfe, dass alle erwarteten Felder vorhanden sind
        for field in expected_fields:
            self.assertIn(field, data, f"Feld '{field}' fehlt im Serializer")
    
    def test_video_serializer_data_accuracy(self):
        """Test: Serialisierte Daten sind korrekt"""
        serializer = VideoSerializer(self.video)
        data = serializer.data
        
        self.assertEqual(data['title'], "Test Video")
        self.assertEqual(data['description'], "Test Description")
        self.assertEqual(data['duration'], 120)
        self.assertEqual(data['category'], "action")
        # is_active ist nicht im Serializer enthalten
    
    def test_video_serializer_with_local_video_file(self):
        """Test: Serializer mit lokaler Video-Datei"""
        local_video = Video.objects.create(
            title="Local Video",
            description="Local Description",
            video_file=self.video_file,
            is_active=True
        )
        
        serializer = VideoSerializer(local_video)
        data = serializer.data
        
        # video_url sollte HLS-URL generieren
        self.assertIn('720p', data['video_url'])
        self.assertIn('index.m3u8', data['video_url'])
        self.assertIn(str(local_video.id), data['video_url'])
    
    def test_video_serializer_with_external_video_url(self):
        """Test: Serializer mit externer Video-URL"""
        external_video = Video.objects.create(
            title="External Video",
            description="External Description",
            video_url="https://external.com/video.mp4",
            is_active=True
        )
        
        serializer = VideoSerializer(external_video)
        data = serializer.data
        
        # video_url sollte externe URL zurückgeben
        self.assertEqual(data['video_url'], "https://external.com/video.mp4")
    
    def test_video_serializer_without_video_source(self):
        """Test: Serializer ohne Video-Quelle"""
        no_video = Video.objects.create(
            title="No Video",
            description="No Video Description",
            is_active=True
        )
        
        serializer = VideoSerializer(no_video)
        data = serializer.data
        
        # video_url sollte None sein
        self.assertIsNone(data['video_url'])
    
    def test_video_serializer_validation(self):
        """Test: Serializer-Validierung"""
        # Gültige Daten
        valid_data = {
            'title': 'Valid Video',
            'description': 'Valid Description',
            'duration': 150,
            'category': 'comedy'
        }
        
        serializer = VideoSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Ungültige Daten
        invalid_data = {
            'title': '',  # Leerer Titel
            'description': '',  # Leere Beschreibung
        }
        
        serializer = VideoSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('description', serializer.errors)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
        Video.objects.all().delete()
