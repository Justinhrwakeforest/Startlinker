#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from apps.users.models import User

def check_users():
    users = User.objects.all()
    print(f'Total users: {users.count()}')
    
    if users.count() == 0:
        print("No users found in database!")
        print("The database migration probably didn't transfer user data.")
        return
    
    print("\nExisting users:")
    for user in users[:10]:
        print(f'  - Email: {user.email}')
        print(f'    Username: {user.username}')
        print(f'    Active: {user.is_active}')
        print(f'    Staff: {user.is_staff}')
        print(f'    Date joined: {user.date_joined}')
        print()

if __name__ == '__main__':
    check_users()