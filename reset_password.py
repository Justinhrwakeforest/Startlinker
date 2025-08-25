#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from apps.users.models import User

def reset_password():
    email = "hruthikrock536@gmail.com"
    new_password = "newpass123"
    
    try:
        user = User.objects.get(email=email)
        print(f"Found user: {user.email}")
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        print(f"Password successfully reset to: {new_password}")
        
        # Verify the password works
        if user.check_password(new_password):
            print("Password verification: SUCCESS")
        else:
            print("Password verification: FAILED")
            
    except User.DoesNotExist:
        print(f"User with email '{email}' does not exist")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    reset_password()