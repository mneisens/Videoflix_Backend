from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Video

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('activation_token', 'activation_token_created', 'password_reset_token', 'password_reset_token_created')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('email',)}),
    )

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at', 'is_active', 'duration']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
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

admin.site.register(CustomUser, CustomUserAdmin)
