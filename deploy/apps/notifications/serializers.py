# apps/notifications/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    sender_info = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display', 'title', 'message',
            'is_read', 'created_at', 'read_at', 'time_ago', 'sender_info', 'url',
            'startup_id', 'post_id', 'job_id', 'comment_id', 'extra_data'
        ]
        read_only_fields = ['created_at', 'read_at']
    
    def get_sender_info(self, obj):
        if obj.sender:
            return {
                'id': obj.sender.id,
                'username': obj.sender.username,
                'display_name': obj.sender.get_full_name() or obj.sender.username,
                'avatar_url': obj.sender.get_avatar_url() if hasattr(obj.sender, 'get_avatar_url') else None
            }
        return None
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    def get_url(self, obj):
        return obj.get_url()


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_on_like', 'email_on_comment', 'email_on_follow', 'email_on_mention',
            'email_on_job_application', 'email_on_approval',
            'push_on_like', 'push_on_comment', 'push_on_follow', 'push_on_mention',
            'push_on_job_application', 'push_on_approval',
            'inapp_on_like', 'inapp_on_comment', 'inapp_on_follow', 'inapp_on_mention',
            'inapp_on_job_application', 'inapp_on_approval'
        ]