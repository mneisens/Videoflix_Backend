import pytest
from unittest.mock import patch
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from video.models import Video


@pytest.mark.django_db
@pytest.mark.views
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
        url = reverse('video_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) 
        
        video_titles = [video['title'] for video in response.data]
        self.assertIn("Test Video 1", video_titles)
        self.assertIn("Test Video 2", video_titles)
        self.assertNotIn("Inactive Video", video_titles)
    
    def test_video_list_empty(self):
        """Test: Leere Video-Liste"""
        Video.objects.all().delete()
        
        url = reverse('video_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_video_list_options(self):
        """Test: OPTIONS-Request für Video-Liste"""
        url = reverse('video_list')
        response = self.client.options(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@pytest.mark.django_db
@pytest.mark.views
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
            
            url = reverse('hls_manifest', kwargs={'movie_id': self.video.id, 'resolution': '480p'})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'application/vnd.apple.mpegurl')
            self.assertIn('segment_000.ts', response.content.decode())
    
    def test_hls_manifest_with_external_video(self):
        """Test: HLS-Manifest mit externer Video-URL"""
        url = reverse('hls_manifest', kwargs={'movie_id': self.external_video.id, 'resolution': '480p'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/vnd.apple.mpegurl')
        self.assertIn('https://external.com/video.mp4', response.content.decode())
    
    def test_hls_manifest_video_not_found(self):
        """Test: HLS-Manifest für nicht existierendes Video"""
        url = reverse('hls_manifest', kwargs={'movie_id': 99999, 'resolution': '480p'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_hls_manifest_inactive_video(self):
        """Test: HLS-Manifest für inaktives Video"""
        self.video.is_active = False
        self.video.save()
        
        url = reverse('hls_manifest', kwargs={'movie_id': self.video.id, 'resolution': '480p'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
        Video.objects.all().delete()


@pytest.mark.django_db
@pytest.mark.views
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

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"fake segment content"
            
            url = reverse('hls_segment', kwargs={
                'movie_id': self.video.id, 
                'resolution': '480p', 
                'segment_name': 'segment_000.ts'
            })
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_hls_segment_video_not_found(self):
        """Test: HLS-Segment für nicht existierendes Video"""
        url = reverse('hls_segment', kwargs={
            'movie_id': 99999, 
            'resolution': '480p', 
            'segment_name': 'segment_000.ts'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_hls_segment_inactive_video(self):
        """Test: HLS-Segment für inaktives Video"""
        self.video.is_active = False
        self.video.save()
        
        url = reverse('hls_segment', kwargs={
            'movie_id': self.video.id, 
            'resolution': '480p', 
            'segment_name': 'segment_000.ts'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def tearDown(self):
        """Test-Daten aufräumen"""
        for video in Video.objects.all():
            if video.video_file:
                video.video_file.delete(save=False)
        Video.objects.all().delete()
