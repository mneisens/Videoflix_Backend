from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at', 'is_active', 'duration', 'video_preview']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'video_preview']
    actions = ['create_hls_segments', 'create_hls_segments_all', 'delete_selected_videos', 'clear_video_cache']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Media', {
            'fields': ('thumbnail_url', 'video_file', 'duration', 'video_preview')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def video_preview(self, obj):
        """Zeigt eine Vorschau des Videos an"""
        if obj.video_file:
            video_url = obj.video_file.url
            return format_html(
                '<video width="320" height="180" controls>'
                '<source src="{}" type="video/mp4">'
                'Ihr Browser unterstützt keine Video-Wiedergabe.'
                '</video>'
                '<br><small>Video: {}</small>',
                video_url, obj.video_file.name
            )
        elif obj.video_url:
            return format_html(
                '<video width="320" height="180" controls>'
                '<source src="{}" type="video/mp4">'
                'Ihr Browser unterstützt keine Video-Wiedergabe.'
                '</video>'
                '<br><small>URL: {}</small>',
                obj.video_url, obj.video_url
            )
        else:
            return "Kein Video verfügbar"
    
    video_preview.short_description = 'Video Vorschau'
    
    def get_urls(self):
        """Fügt benutzerdefinierte URLs für Video-Vorschau hinzu"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:video_id>/preview/',
                self.admin_site.admin_view(self.video_preview_view),
                name='video_preview',
            ),
        ]
        return custom_urls + urls
    
    def video_preview_view(self, request, video_id):
        """Zeigt eine Vollbild-Video-Vorschau"""
        try:
            video = Video.objects.get(id=video_id)
            context = {
                'video': video,
                'title': f'Video Vorschau: {video.title}',
            }
            return render(request, 'admin/video/video_preview.html', context)
        except Video.DoesNotExist:
            return JsonResponse({'error': 'Video nicht gefunden'}, status=404)
    
    def create_hls_segments(self, request, queryset):
        """Erstellt HLS-Segmente asynchron für ausgewählte Videos"""
        from .tasks import process_multiple_resolutions
        
        success_count = 0
        error_count = 0
        
        for video in queryset:
            if video.video_file:
                try:
                    # HLS-Segmente asynchron erstellen
                    process_multiple_resolutions.delay(video.id, ['480p', '720p', '1080p'])
                    success_count += 1
                except Exception as e:
                    error_count += 1
            else:
                error_count += 1
        
        if error_count == 0:
            self.message_user(request, f"HLS-Segmente für {success_count} Videos werden asynchron erstellt!")
        else:
            self.message_user(request, f"HLS-Segmente werden erstellt: {success_count} Videos in Queue, {error_count} fehlgeschlagen")
    
    create_hls_segments.short_description = "HLS-Segmente für ausgewählte Videos erstellen"
    
    def create_hls_segments_all(self, request, queryset):
        """Erstellt HLS-Segmente asynchron für alle Videos"""
        from .tasks import process_multiple_resolutions
        
        all_videos = Video.objects.filter(video_file__isnull=False)
        success_count = 0
        error_count = 0
        
        for video in all_videos:
            try:
                # HLS-Segmente asynchron erstellen
                process_multiple_resolutions.delay(video.id, ['480p', '720p', '1080p'])
                success_count += 1
            except Exception as e:
                error_count += 1
        
        if error_count == 0:
            self.message_user(request, f"HLS-Segmente für alle {success_count} Videos werden asynchron erstellt!")
        else:
            self.message_user(request, f"HLS-Segmente werden erstellt: {success_count} Videos in Queue, {error_count} fehlgeschlagen")
    
    create_hls_segments_all.short_description = "HLS-Segmente für alle Videos erstellen"
    
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


