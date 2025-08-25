from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.conf import settings

User = get_user_model()


def get_private_storage():
    """Get the appropriate storage backend for private files"""
    if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
        from startup_hub.storage import PrivateMediaStorage
        return PrivateMediaStorage()
    return None


class PitchDeckAnalysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='analyses'
    )
    deck_file = models.FileField(
        upload_to='pitch_decks/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text='PDF file only, max 25MB',
        storage=get_private_storage()
    )
    original_filename = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    analysis_result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pitch Deck Analysis'
        verbose_name_plural = 'Pitch Deck Analyses'
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename} ({self.status})"
    
    @property
    def is_file_available(self):
        return self.file_deleted_at is None and bool(self.deck_file)
