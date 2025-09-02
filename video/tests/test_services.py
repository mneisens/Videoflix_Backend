import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from video.models import Video
from video.services import create_hls_stream, get_hls_segments, ensure_hls_stream


@pytest.mark.django_db
@pytest.mark.services
class VideoServicesTests(TestCase):
    """Tests für die Video-Services"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = os.path.join(self.temp_dir, 'test_video.mp4')
        
        with open(self.test_video_path, 'wb') as f:
            f.write(b"fake video content for testing")
        
        self.video = Video.objects.create(
            title="Service Test Video",
            description="Service Test Description",
            is_active=True
        )
    
    def tearDown(self):
        if os.path.exists(self.test_video_path):
            os.remove(self.test_video_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls')
        if os.path.exists(hls_dir):
            import shutil
            shutil.rmtree(hls_dir)
        
        Video.objects.all().delete()
    
    @patch('video.services.subprocess.run')
    def test_create_hls_stream_success(self, mock_subprocess):
        """Test: HLS-Stream erfolgreich erstellen"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = create_hls_stream(self.test_video_path, self.video.id, '720p')
        
        self.assertTrue(result['success'])
        self.assertIn('playlist_path', result)
        self.assertIn('output_dir', result)
        
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        
        self.assertEqual(call_args[0], 'ffmpeg')
        self.assertIn('-f', call_args)
        self.assertIn('hls', call_args)
        self.assertIn('-hls_time', call_args)
        self.assertIn('10', call_args)
    
    @patch('video.services.subprocess.run')
    def test_create_hls_stream_ffmpeg_failure(self, mock_subprocess):
        """Test: HLS-Stream-Erstellung schlägt fehl"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "FFmpeg error: Invalid input file"
        mock_subprocess.return_value = mock_result
        
        result = create_hls_stream(self.test_video_path, self.video.id, '720p')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('FFmpeg error', result['error'])
    
    def test_get_hls_segments_existing_stream(self):
        """Test: HLS-Segmente für existierenden Stream abrufen"""
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(self.video.id), '720p')
        os.makedirs(hls_dir, exist_ok=True)
        
        playlist_path = os.path.join(hls_dir, 'playlist.m3u8')
        with open(playlist_path, 'w') as f:
            f.write("""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.000000,
segment_000.ts
#EXT-X-ENDLIST
""")
        
        segment_path = os.path.join(hls_dir, 'segment_000.ts')
        with open(segment_path, 'wb') as f:
            f.write(b"fake segment content")
        
        result = get_hls_segments(self.video.id, '720p')
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['playlist'], playlist_path)
        self.assertEqual(len(result['segments']), 1)
        self.assertEqual(result['segment_count'], 1)
    
    def test_get_hls_segments_nonexistent_stream(self):
        """Test: HLS-Segmente für nicht existierenden Stream abrufen"""
        result = get_hls_segments(self.video.id, '720p')
        
        self.assertIsNone(result)
    
    def test_ensure_hls_stream_existing_stream(self):
        """Test: HLS-Stream sicherstellen - existierender Stream"""
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(self.video.id), '720p')
        os.makedirs(hls_dir, exist_ok=True)

        playlist_path = os.path.join(hls_dir, 'playlist.m3u8')
        with open(playlist_path, 'w') as f:
            f.write("""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.000000,
segment_000.ts
#EXT-X-ENDLIST
""")
        
        result = ensure_hls_stream(self.test_video_path, self.video.id, '720p')
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['playlist'], playlist_path)
    
    @patch('video.services.create_hls_stream')
    def test_ensure_hls_stream_create_new_stream(self, mock_create_stream):
        """Test: HLS-Stream sicherstellen - neuen Stream erstellen"""
        mock_create_stream.return_value = {
            'success': True,
            'playlist_path': '/fake/path/playlist.m3u8',
            'output_dir': '/fake/path/output'
        }
        
        result = ensure_hls_stream(self.test_video_path, self.video.id, '720p')
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['playlist_path'], '/fake/path/playlist.m3u8')
        
        mock_create_stream.assert_called_once_with(self.test_video_path, self.video.id, '720p')
