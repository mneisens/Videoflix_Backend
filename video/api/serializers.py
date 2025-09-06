import os
from rest_framework import serializers
from django.conf import settings
from ..models import Video


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for Video objects with intelligent thumbnail processing
    """
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 
            'created_at', 
            'title', 
            'description', 
            'thumbnail_url', 
            'category'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_thumbnail_url(self, obj):
        """
        Returns thumbnail URL with the following priority:
        1. External thumbnail URL (highest priority)
        2. Manually uploaded thumbnail
        3. Auto-generated video frame
        4. Category-specific default thumbnail
        """
        try:
            if obj.thumbnail_url:
                return obj.thumbnail_url
            
            if obj.thumbnail:
                return self._build_absolute_url(obj.thumbnail.url)
            
            auto_thumbnail = self._get_auto_thumbnail_url(obj.id)
            if auto_thumbnail:
                return auto_thumbnail
            
            return self._get_default_thumbnail_url(obj.category)
            
        except Exception as e:
            return self._get_default_thumbnail_url(obj.category)
    
    def _build_absolute_url(self, relative_url):
        """Builds an absolute URL from a relative URL"""
        if relative_url.startswith('http'):
            return relative_url
        
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        return f"{base_url}{relative_url}"
    
    def _get_auto_thumbnail_url(self, video_id):
        """Checks if an auto-generated thumbnail exists"""
        auto_thumbnail_path = f"thumbnails/video_{video_id}_thumbnail.jpg"
        full_path = os.path.join(settings.MEDIA_ROOT, auto_thumbnail_path)
        
        if os.path.exists(full_path):
            base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            return f"{base_url}/media/{auto_thumbnail_path}"
        
        return None
    
    def _get_default_thumbnail_url(self, category):
        """
        Returns a default thumbnail URL based on the category
        """
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        
        category_thumbnails = {
            'action': 'action.svg',
            'comedy': 'comedy.svg', 
            'drama': 'drama.svg',
        }
        
        thumbnail_file = category_thumbnails.get(category, 'default.svg')
        return f"{base_url}/static/images/default_thumbnails/{thumbnail_file}"
