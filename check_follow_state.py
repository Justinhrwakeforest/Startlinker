#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.users.social_models import UserFollow
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Check testuser's current relationships
testuser = User.objects.get(username='testuser')
following_relations = UserFollow.objects.filter(follower=testuser).select_related('following')

print(f'testuser following_count field: {testuser.following_count}')
print(f'Actual following relationships: {following_relations.count()}')

print('\nCurrent following list:')
for i, relation in enumerate(following_relations, 1):
    user = relation.following
    display_name = f'{user.first_name} {user.last_name}'.strip() or user.username
    print(f'{i}. {user.username} ({display_name}) - ID: {user.id}')

# Check if Hruthik Rock relationship exists
try:
    hruthik = User.objects.get(username='hruthik')
    hruthik_relation = UserFollow.objects.filter(follower=testuser, following=hruthik).exists()
    print(f'\nHruthik Rock (hruthik) relationship exists: {hruthik_relation}')
    if hruthik_relation:
        print('Hruthik Rock should be included in the count')
    else:
        print('Hruthik Rock relationship missing from database')
except User.DoesNotExist:
    print('Hruthik user not found')

# Fix the count to match reality
actual_count = following_relations.count()
if testuser.following_count != actual_count:
    with connection.cursor() as cursor:
        cursor.execute('UPDATE users_user SET following_count = %s WHERE id = %s', [actual_count, testuser.id])
        print(f'\nFixed following count: {testuser.following_count} -> {actual_count}')
    
    # Refresh to show new count
    testuser.refresh_from_db()
    print(f'New count: {testuser.following_count}')
else:
    print(f'\nCount is already correct: {actual_count}')