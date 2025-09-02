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
            url = obj.get_thumbnail_url()
            if url and not url.startswith('http'):
                return f"{settings.SITE_URL}{url}" if hasattr(settings, 'SITE_URL') else url
            return url
        except Exception:
            return None
