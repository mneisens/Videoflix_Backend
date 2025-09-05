from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at', 'is_active', 'duration']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['delete_selected_videos', 'clear_video_cache']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Media', {
            'fields': ('thumbnail_url', 'video_file', 'duration')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    
    
    
    def delete_selected_videos(self, request, queryset):
        """Löscht ausgewählte Videos und leert den Cache"""
        from django.core.cache import cache
        
        count = queryset.count()
        queryset.delete()
        
        cache.delete('video_list_public')
        
        self.message_user(request, f"{count} Videos wurden gelöscht und Cache wurde geleert.")
    
    delete_selected_videos.short_description = "Ausgewählte Videos löschen und Cache leeren"
    
    def clear_video_cache(self, request, queryset):
        """Leert den Video-Cache manuell"""
        from django.core.cache import cache
        
        cache.delete('video_list_public')
        self.message_user(request, "Video-Cache wurde geleert.")
    
    clear_video_cache.short_description = "Video-Cache leeren"


