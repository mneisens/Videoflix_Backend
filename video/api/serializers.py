from rest_framework import serializers
from ..models import Video
from django.conf import settings

class VideoSerializer(serializers.ModelSerializer):
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
        try:
            if obj.thumbnail:
                if not obj.thumbnail.url.startswith('http'):
                    base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
                    return f"{base_url}{obj.thumbnail.url}"
                else:
                    return obj.thumbnail.url
            
            if obj.thumbnail_url:
                return obj.thumbnail_url
            
            auto_thumbnail_path = f"thumbnails/video_{obj.id}_thumbnail.jpg"
            import os
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, auto_thumbnail_path)):
                base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
                return f"{base_url}/media/{auto_thumbnail_path}"
            
            return self._get_default_thumbnail_url(obj.category)
        except Exception as e:
            print(f"Fehler in get_thumbnail_url für Video {obj.id}: {e}")
            return self._get_default_thumbnail_url(obj.category)
    
    def _get_default_thumbnail_url(self, category):
        """Gibt eine Standard-Thumbnail-URL basierend auf der Kategorie zurück"""
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        
        category_thumbnails = {
            'action': f"{base_url}/static/images/default_thumbnails/action.svg",
            'comedy': f"{base_url}/static/images/default_thumbnails/comedy.svg", 
            'drama': f"{base_url}/static/images/default_thumbnails/drama.svg",
            'horror': f"{base_url}/static/images/default_thumbnails/default.svg",
            'romance': f"{base_url}/static/images/default_thumbnails/default.svg",
            'sci-fi': f"{base_url}/static/images/default_thumbnails/default.svg",
            'thriller': f"{base_url}/static/images/default_thumbnails/default.svg",
            'documentary': f"{base_url}/static/images/default_thumbnails/default.svg",
            'animation': f"{base_url}/static/images/default_thumbnails/default.svg",
        }
        
        return category_thumbnails.get(category, f"{base_url}/static/images/default_thumbnails/default.svg")
