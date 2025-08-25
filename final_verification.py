#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.users.social_models import UserFollow
from django.contrib.auth import get_user_model

User = get_user_model()

# Final verification
testuser = User.objects.get(username='testuser')
following_relations = UserFollow.objects.filter(follower=testuser)

print('FINAL VERIFICATION:')
print(f'Database following_count field: {testuser.following_count}')
print(f'Actual relationships count: {following_relations.count()}')
print(f'Counts match: {testuser.following_count == following_relations.count()}')

print('\nUsers being followed:')
for i, relation in enumerate(following_relations.select_related('following'), 1):
    user = relation.following
    display_name = f'{user.first_name} {user.last_name}'.strip() or user.username
    print(f'{i}. {user.username} ({display_name})')
    
print(f'\nExpected display: Header = {following_relations.count()}, List = {following_relations.count()} users')