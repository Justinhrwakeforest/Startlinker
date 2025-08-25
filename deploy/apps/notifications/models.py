# apps/notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like_startup', 'Startup Liked'),
        ('comment_startup', 'Startup Comment'),
        ('rating_startup', 'Startup Rating'),
        ('like_post', 'Post Liked'),
        ('comment_post', 'Post Comment'),
        ('job_application', 'Job Application'),
        ('startup_approved', 'Startup Approved'),
        ('startup_rejected', 'Startup Rejected'),
        ('job_approved', 'Job Approved'),
        ('job_rejected', 'Job Rejected'),
        ('claim_approved', 'Claim Approved'),
        ('claim_rejected', 'Claim Rejected'),
        ('follow_user', 'User Follow'),
        ('mention', 'Mention'),
        ('system', 'System Notification'),
    ]
    
    # Core fields
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional related objects (for deep linking)
    startup_id = models.PositiveIntegerField(null=True, blank=True)
    post_id = models.PositiveIntegerField(null=True, blank=True)
    job_id = models.PositiveIntegerField(null=True, blank=True)
    comment_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional data as JSON
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_url(self):
        """Get the URL this notification should link to"""
        if self.startup_id:
            return f"/startups/{self.startup_id}"
        elif self.post_id:
            return f"/posts/{self.post_id}"
        elif self.job_id:
            return f"/jobs/{self.job_id}"
        return "/notifications"
    
    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, sender=None, **kwargs):
        """Helper method to create notifications"""
        return cls.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            startup_id=kwargs.get('startup_id'),
            post_id=kwargs.get('post_id'),
            job_id=kwargs.get('job_id'),
            comment_id=kwargs.get('comment_id'),
            extra_data=kwargs.get('extra_data', {})
        )


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notifications
    email_on_like = models.BooleanField(default=True)
    email_on_comment = models.BooleanField(default=True)
    email_on_follow = models.BooleanField(default=True)
    email_on_mention = models.BooleanField(default=True)
    email_on_job_application = models.BooleanField(default=True)
    email_on_approval = models.BooleanField(default=True)
    
    # Push notifications
    push_on_like = models.BooleanField(default=True)
    push_on_comment = models.BooleanField(default=True)
    push_on_follow = models.BooleanField(default=True)
    push_on_mention = models.BooleanField(default=True)
    push_on_job_application = models.BooleanField(default=False)
    push_on_approval = models.BooleanField(default=True)
    
    # In-app notifications
    inapp_on_like = models.BooleanField(default=True)
    inapp_on_comment = models.BooleanField(default=True)
    inapp_on_follow = models.BooleanField(default=True)
    inapp_on_mention = models.BooleanField(default=True)
    inapp_on_job_application = models.BooleanField(default=True)
    inapp_on_approval = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"