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
    actions = ['create_hls_segments', 'create_hls_segments_all']
    
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
        """Erstellt HLS-Segmente für ausgewählte Videos"""
        from .services import create_hls_stream
        
        success_count = 0
        error_count = 0
        
        for video in queryset:
            if video.video_file:
                try:
                    resolutions = ['480p', '720p', '1080p']
                    for resolution in resolutions:
                        result = create_hls_stream(video.video_file.path, video.id, resolution)
                        if result['success']:
                            success_count += 1
                        else:
                            error_count += 1
                except Exception as e:
                    error_count += 1
            else:
                error_count += 1
        
        if error_count == 0:
            self.message_user(request, f" HLS-Segmente für {success_count} Videos erfolgreich erstellt!")
        else:
            self.message_user(request, f" HLS-Segmente erstellt: {success_count} erfolgreich, {error_count} fehlgeschlagen")
    
    create_hls_segments.short_description = "HLS-Segmente für ausgewählte Videos erstellen"
    
    def create_hls_segments_all(self, request, queryset):
        """Erstellt HLS-Segmente für alle Videos"""
        from .services import create_hls_stream
        
        all_videos = Video.objects.filter(video_file__isnull=False)
        success_count = 0
        error_count = 0
        
        for video in all_videos:
            try:
                resolutions = ['480p', '720p', '1080p']
                for resolution in resolutions:
                    result = create_hls_stream(video.video_file.path, video.id, resolution)
                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1
            except Exception as e:
                error_count += 1
        
        if error_count == 0:
            self.message_user(request, f"HLS-Segmente für alle {success_count} Videos erfolgreich erstellt!")
        else:
            self.message_user(request, f"HLS-Segmente erstellt: {success_count} erfolgreich, {error_count} fehlgeschlagen")
    
    create_hls_segments_all.short_description = "HLS-Segmente für alle Videos erstellen"


