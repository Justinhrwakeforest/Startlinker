#!/usr/bin/env python
"""
Script to synchronize follower/following counts with actual database relationships
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.users.social_models import UserFollow
from django.contrib.auth import get_user_model

User = get_user_model()

def sync_follower_counts():
    """Synchronize all user follower/following counts with actual relationships"""
    users = User.objects.all()
    updated_count = 0
    
    for user in users:
        actual_following = UserFollow.objects.filter(follower=user).count()
        actual_followers = UserFollow.objects.filter(following=user).count()
        
        if user.following_count != actual_following or user.follower_count != actual_followers:
            print(f'Fixing {user.username}: following {user.following_count} -> {actual_following}, followers {user.follower_count} -> {actual_followers}')
            user.following_count = actual_following
            user.follower_count = actual_followers
            user.save(update_fields=['following_count', 'follower_count'])
            updated_count += 1
    
    print(f'Synchronized counts for {updated_count} users')
    return updated_count

if __name__ == '__main__':
    sync_follower_counts()