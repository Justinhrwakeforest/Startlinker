#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.users.social_models import UserFollow
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Fix testuser's count
testuser = User.objects.get(username='testuser')
actual_following = UserFollow.objects.filter(follower=testuser).count()

print(f'testuser following_count: {testuser.following_count}')
print(f'Actual relationships: {actual_following}')

if testuser.following_count != actual_following:
    with connection.cursor() as cursor:
        cursor.execute('UPDATE users_user SET following_count = %s WHERE id = %s', [actual_following, testuser.id])
        print(f'Fixed count: {testuser.following_count} -> {actual_following}')
else:
    print('Count already correct')