from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from .models import Video
from .api.serializers import VideoSerializer


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
        self.assertEqual(video.description, "Test Description")
        self.assertEqual(video.category, "action")
        self.assertEqual(video.duration, 120)
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
    
    def test_video_category_choices(self):
        """Test: Kategorie-Auswahl"""
        video = Video.objects.create(
            title="Category Video",
            description="Category Description",
            category="comedy"
        )
        
        self.assertEqual(video.category, "comedy")
        self.assertIn(video.category, [choice[0] for choice in Video.CATEGORY_CHOICES])
    
    def test_video_file_upload(self):
        """Test: Video-Datei-Upload"""
        video = Video.objects.create(
            title="File Video",
            description="File Description",
            video_file=self.video_file
        )
        
        self.assertTrue(video.video_file)
        self.assertEqual(video.video_file.name, f"videos/{self.video_file.name}")
    
    def test_video_url_field(self):
        """Test: Video-URL-Feld"""
        video = Video.objects.create(
            title="URL Video",
            description="URL Description",
            video_url="https://example.com/video.mp4"
        )
        
        self.assertEqual(video.video_url, "https://example.com/video.mp4")
    
    def test_video_ordering(self):
        """Test: Videos werden nach created_at sortiert"""
        video1 = Video.objects.create(
            title="First Video",
            description="First Description"
        )
        
        video2 = Video.objects.create(
            title="Second Video",
            description="Second Description"
        )
        
        videos = list(Video.objects.all())
        self.assertEqual(videos[0], video2)  # Neueste zuerst
        self.assertEqual(videos[1], video1)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            if video.poster:
                video.poster.delete(save=False)
            if video.background:
                video.background.delete(save=False)
        Video.objects.all().delete()


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
            'id', 'title', 'description', 'category', 'thumbnail', 'thumbnail_url',
            'poster', 'background', 'video_file', 'video_url', 'duration',
            'is_active', 'created_at', 'updated_at'
        }
        
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_video_serializer_data_accuracy(self):
        """Test: Serialisierte Daten sind korrekt"""
        serializer = VideoSerializer(self.video)
        data = serializer.data
        
        self.assertEqual(data['title'], "Test Video")
        self.assertEqual(data['description'], "Test Description")
        self.assertEqual(data['category'], "action")
        self.assertEqual(data['duration'], 120)
        self.assertTrue(data['is_active'])
    
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
            'category': 'comedy',
            'duration': 150
        }
        
        serializer = VideoSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Ungültige Daten
        invalid_data = {
            'title': '',  # Leerer Titel
            'category': 'invalid_category'  # Ungültige Kategorie
        }
        
        serializer = VideoSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            if video.poster:
                video.poster.delete(save=False)
            if video.background:
                video.background.delete(save=False)
        Video.objects.all().delete()


class VideoListViewTests(APITestCase):
    """Tests für die VideoListView"""
    
    def setUp(self):
        self.video1 = Video.objects.create(
            title="Test Video 1",
            description="Test Description 1",
            category="action",
            duration=120,
            is_active=True
        )
        
        self.video2 = Video.objects.create(
            title="Test Video 2",
            description="Test Description 2",
            category="comedy",
            duration=90,
            is_active=True
        )
        
        self.inactive_video = Video.objects.create(
            title="Inactive Video",
            description="Inactive Description",
            category="drama",
            duration=150,
            is_active=False
        )
    
    def test_video_list_get(self):
        """Test: GET-Request für Video-Liste"""
        url = reverse('video-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Nur aktive Videos
        
        video_titles = [video['title'] for video in response.data]
        self.assertIn("Test Video 1", video_titles)
        self.assertIn("Test Video 2", video_titles)
        self.assertNotIn("Inactive Video", video_titles)
    
    def test_video_list_empty(self):
        """Test: Leere Video-Liste"""
        Video.objects.all().delete()
        
        url = reverse('video-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_video_list_options(self):
        """Test: OPTIONS-Request für Video-Liste"""
        url = reverse('video-list')
        response = self.client.options(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class HLSManifestViewTests(APITestCase):
    """Tests für die HLSManifestView"""
    
    def setUp(self):
        self.video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"fake video content",
            content_type="video/mp4"
        )
        
        self.video = Video.objects.create(
            title="HLS Test Video",
            description="HLS Test Description",
            video_file=self.video_file,
            is_active=True
        )
        
        self.external_video = Video.objects.create(
            title="External Video",
            description="External Description",
            video_url="https://external.com/video.mp4",
            is_active=True
        )
    
    @patch('video.api.views.ensure_hls_stream')
    def test_hls_manifest_with_local_video(self, mock_ensure_hls):
        """Test: HLS-Manifest mit lokaler Video-Datei"""
        mock_ensure_hls.return_value = {
            'success': True,
            'playlist': '/fake/path/playlist.m3u8'
        }
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.000000,
segment_000.ts
#EXT-X-ENDLIST
"""
            
            url = reverse('hls-manifest', kwargs={'movie_id': self.video.id, 'resolution': '480p'})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'application/vnd.apple.mpegurl')
            self.assertIn('segment_000.ts', response.content.decode())
    
    def test_hls_manifest_with_external_video(self):
        """Test: HLS-Manifest mit externer Video-URL"""
        url = reverse('hls-manifest', kwargs={'movie_id': self.external_video.id, 'resolution': '480p'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/vnd.apple.mpegurl')
        self.assertIn('https://external.com/video.mp4', response.content.decode())
    
    def test_hls_manifest_video_not_found(self):
        """Test: HLS-Manifest für nicht existierendes Video"""
        url = reverse('hls-manifest', kwargs={'movie_id': 99999, 'resolution': '480p'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_hls_manifest_inactive_video(self):
        """Test: HLS-Manifest für inaktives Video"""
        self.video.is_active = False
        self.video.save()
        
        url = reverse('hls-manifest', kwargs={'movie_id': self.video.id, 'resolution': '480p'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            if video.poster:
                video.poster.delete(save=False)
            if video.background:
                video.background.delete(save=False)
        Video.objects.all().delete()


class HLSVideoSegmentViewTests(APITestCase):
    """Tests für die HLSVideoSegmentView"""
    
    def setUp(self):
        self.video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"fake video content",
            content_type="video/mp4"
        )
        
        self.video = Video.objects.create(
            title="Segment Test Video",
            description="Segment Test Description",
            video_file=self.video_file,
            is_active=True
        )
    
    @patch('video.api.views.get_hls_segments')
    def test_hls_segment_view(self, mock_get_segments):
        """Test: HLS-Segment-View"""
        mock_get_segments.return_value = {
            'success': True,
            'segments': ['/fake/path/segment_000.ts']
        }
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"fake segment content"
            
            url = reverse('hls-segment', kwargs={
                'movie_id': self.video.id, 
                'resolution': '480p', 
                'segment_name': 'segment_000.ts'
            })
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'video/mp2t')
            self.assertEqual(response.content, b"fake segment content")
    
    def test_hls_segment_video_not_found(self):
        """Test: HLS-Segment für nicht existierendes Video"""
        url = reverse('hls-segment', kwargs={
            'movie_id': 99999, 
            'resolution': '480p', 
            'segment_name': 'segment_000.ts'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_hls_segment_inactive_video(self):
        """Test: HLS-Segment für inaktives Video"""
        self.video.is_active = False
        self.video.save()
        
        url = reverse('hls-segment', kwargs={
            'movie_id': self.video.id, 
            'resolution': '480p', 
            'segment_name': 'segment_000.ts'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            if video.poster:
                video.poster.delete(save=False)
            if video.background:
                video.background.delete(save=False)
        Video.objects.all().delete()
