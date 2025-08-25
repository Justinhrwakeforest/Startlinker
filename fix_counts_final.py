#!/usr/bin/env python
"""
Script to fix follower/following counts
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.users.social_models import UserFollow
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def fix_all_counts():
    """Fix all user follower/following counts"""
    
    # Update testuser's following count to match reality (5 relationships)
    with connection.cursor() as cursor:
        cursor.execute('UPDATE users_user SET following_count = 5 WHERE username = %s', ['testuser'])
        print('Updated testuser following count to 5')
    
    # Update all users' counts to match actual relationships
    users = User.objects.all()
    for user in users:
        actual_following = UserFollow.objects.filter(follower=user).count()
        actual_followers = UserFollow.objects.filter(following=user).count()
        
        # Update if counts don't match
        if user.following_count != actual_following or user.follower_count != actual_followers:
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE users_user SET following_count = %s, follower_count = %s WHERE id = %s',
                    [actual_following, actual_followers, user.id]
                )
                print(f'Updated {user.username}: following {user.following_count} -> {actual_following}, followers {user.follower_count} -> {actual_followers}')
    
    print('All counts synchronized!')

if __name__ == '__main__':
    fix_all_counts()