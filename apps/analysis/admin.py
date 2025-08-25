from django.contrib import admin
from .models import PitchDeckAnalysis


@admin.register(PitchDeckAnalysis)
class PitchDeckAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'original_filename', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'original_filename']
    readonly_fields = ['created_at', 'updated_at', 'analysis_result', 'error_message']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'original_filename', 'deck_file', 'status')
        }),
        ('Analysis Results', {
            'fields': ('analysis_result', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'file_deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent accidental deletion of analyses
        return request.user.is_superuser
