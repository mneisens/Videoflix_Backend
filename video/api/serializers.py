from rest_framework import serializers
from ..models import Video
from django.conf import settings

class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()
    background_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    direct_video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 
            'created_at', 
            'title', 
            'description', 
            'thumbnail_url', 
            'poster_url',
            'background_url',
            'video_url',
            'direct_video_url',
            'category',
            'duration',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_thumbnail_url(self, obj):
        url = obj.get_thumbnail_url()
        if url and not url.startswith('http'):
            return f"{settings.SITE_URL}{url}" if hasattr(settings, 'SITE_URL') else url
        return url
    
    def get_poster_url(self, obj):
        url = obj.get_poster_url()
        if url and not url.startswith('http'):
            return f"{settings.SITE_URL}{url}" if hasattr(settings, 'SITE_URL') else url
        return url
    
    def get_background_url(self, obj):
        url = obj.get_background_url()
        if url and not url.startswith('http'):
            return f"{settings.SITE_URL}{url}" if hasattr(settings, 'SITE_URL') else url
        return url
    
    def get_video_url(self, obj):
        """Gibt die HLS-URL für das Video zurück"""
        if obj.video_file:
            return f"{settings.SITE_URL}/api/video/{obj.id}/720p/index.m3u8"
        elif obj.video_url and not obj.video_url.startswith('http://localhost:8000') and not obj.video_url.startswith('http://127.0.0.1:8000'):
            return obj.video_url
        else:
            return None
    
    def get_direct_video_url(self, obj):
        """Gibt die direkte Video-URL zurück"""
        if obj.video_file or obj.video_url:
            return f"{settings.SITE_URL}/api/video/{obj.id}/direct/"
        return None
