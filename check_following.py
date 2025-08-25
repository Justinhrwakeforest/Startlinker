#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.users.social_models import UserFollow
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Check testuser's actual relationships
testuser = User.objects.get(username='testuser')
following_relations = UserFollow.objects.filter(follower=testuser).select_related('following')

print(f'testuser current following_count field: {testuser.following_count}')
print(f'Actual following relationships: {following_relations.count()}')

print('\nCurrent following list:')
for i, relation in enumerate(following_relations, 1):
    user = relation.following
    display_name = f'{user.first_name} {user.last_name}'.strip() or user.username
    print(f'{i}. {user.username} - {display_name}')

# Fix count to match actual relationships
actual_count = following_relations.count()
if testuser.following_count != actual_count:
    with connection.cursor() as cursor:
        cursor.execute('UPDATE users_user SET following_count = %s WHERE id = %s', [actual_count, testuser.id])
        print(f'\nFixed testuser following count: {testuser.following_count} -> {actual_count}')
else:
    print(f'\nCount is already correct: {actual_count}')