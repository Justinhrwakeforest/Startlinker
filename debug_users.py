#!/usr/bin/env python3
"""
Debug script to check users in database
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=== DATABASE USERS DEBUG ===")
print(f"Total users in database: {User.objects.count()}")
print(f"Active users: {User.objects.filter(is_active=True).count()}")
print()

print("All users:")
for user in User.objects.all().order_by('id'):
    print(f"  ID {user.id}: {user.username} ({user.first_name} {user.last_name}) - Active: {user.is_active}")

print()
print("Checking user ID 2 specifically...")
try:
    user2 = User.objects.get(id=2)
    print(f"User ID 2 exists: {user2.username} - Active: {user2.is_active}")
except User.DoesNotExist:
    print("User ID 2 does not exist in database")

# Check if there are any gaps in user IDs
user_ids = list(User.objects.values_list('id', flat=True).order_by('id'))
print(f"User IDs in database: {user_ids}")

print("=== END DEBUG ===")