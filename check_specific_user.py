#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from apps.users.models import User

def check_specific_user():
    email = "hruthikrock536@gmail.com"
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
        print(f"[SUCCESS] User found:")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Active: {user.is_active}")
        print(f"  Staff: {user.is_staff}")
        print(f"  Has usable password: {user.has_usable_password()}")
        print(f"  Date joined: {user.date_joined}")
        
        # Test password
        test_password = "newpass123"
        if user.check_password(test_password):
            print(f"[SUCCESS] Password '{test_password}' is correct")
        else:
            print(f"[ERROR] Password '{test_password}' is incorrect")
            
    except User.DoesNotExist:
        print(f"[ERROR] User with email '{email}' does not exist")
        print("\nAvailable users:")
        for user in User.objects.all()[:10]:
            print(f"  - {user.email}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_specific_user()