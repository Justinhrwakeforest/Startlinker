#!/usr/bin/env python
"""Create sample notifications for testing"""
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.notifications.models import Notification

User = get_user_model()

def create_sample_notifications():
    """Create sample notifications for testing"""
    
    # Get the first user (hruthik) to receive notifications
    try:
        user = User.objects.get(username='hruthik')
    except User.DoesNotExist:
        print("User 'hruthik' not found. Please ensure the user exists.")
        return
    
    # Get or create a sender user
    sender, _ = User.objects.get_or_create(
        username='john_doe',
        defaults={
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
    )
    
    # Clear existing notifications for clean testing
    Notification.objects.filter(recipient=user).delete()
    print(f"Cleared existing notifications for {user.username}")
    
    # Create various types of notifications
    notifications_data = [
        {
            'notification_type': 'follow_user',
            'title': 'New Follower',
            'message': 'John Doe started following you',
            'sender': sender,
            'is_read': False,
            'created_at': timezone.now() - timedelta(minutes=5)
        },
        {
            'notification_type': 'like_startup',
            'title': 'Startup Liked',
            'message': 'Your startup "TechVentures" received a new like',
            'sender': sender,
            'is_read': False,
            'startup_id': 1,
            'created_at': timezone.now() - timedelta(hours=1)
        },
        {
            'notification_type': 'comment_post',
            'title': 'New Comment',
            'message': 'John Doe commented on your post: "Great insights!"',
            'sender': sender,
            'is_read': False,
            'post_id': 1,
            'created_at': timezone.now() - timedelta(hours=2)
        },
        {
            'notification_type': 'job_application',
            'title': 'New Job Application',
            'message': 'You have a new application for "Senior Developer" position',
            'sender': sender,
            'is_read': True,
            'job_id': 1,
            'read_at': timezone.now() - timedelta(hours=1),
            'created_at': timezone.now() - timedelta(hours=3)
        },
        {
            'notification_type': 'mention',
            'title': 'You were mentioned',
            'message': '@hruthik Check out this amazing startup idea!',
            'sender': sender,
            'is_read': False,
            'created_at': timezone.now() - timedelta(hours=4)
        },
        {
            'notification_type': 'startup_approved',
            'title': 'Startup Approved',
            'message': 'Your startup "InnovateTech" has been approved and is now live!',
            'is_read': False,
            'startup_id': 2,
            'created_at': timezone.now() - timedelta(days=1)
        },
        {
            'notification_type': 'rating_startup',
            'title': 'New Rating',
            'message': 'Your startup received a 5-star rating!',
            'sender': sender,
            'is_read': False,
            'startup_id': 1,
            'created_at': timezone.now() - timedelta(days=1, hours=5)
        },
        {
            'notification_type': 'system',
            'title': 'Welcome to StartLinker!',
            'message': 'Complete your profile to get more visibility',
            'is_read': True,
            'read_at': timezone.now() - timedelta(days=2),
            'created_at': timezone.now() - timedelta(days=3)
        }
    ]
    
    # Create notifications
    created_count = 0
    for notif_data in notifications_data:
        created_at = notif_data.pop('created_at')
        read_at = notif_data.pop('read_at', None)
        
        notification = Notification.objects.create(
            recipient=user,
            **notif_data
        )
        
        # Update the created_at field (bypass auto_now_add)
        Notification.objects.filter(id=notification.id).update(
            created_at=created_at,
            read_at=read_at
        )
        
        created_count += 1
        print(f"Created notification: {notification.title}")
    
    print(f"\nSuccessfully created {created_count} sample notifications for user '{user.username}'")
    
    # Display summary
    total = Notification.objects.filter(recipient=user).count()
    unread = Notification.objects.filter(recipient=user, is_read=False).count()
    print(f"\nNotification Summary:")
    print(f"  Total: {total}")
    print(f"  Unread: {unread}")
    print(f"  Read: {total - unread}")

if __name__ == '__main__':
    create_sample_notifications()