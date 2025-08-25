#!/usr/bin/env python
"""Create a test user for testing profile upload"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from apps.users.models import User

def create_test_user():
    """Create or get a test user"""
    test_email = "testuser@example.com"
    test_username = "testuser"
    test_password = "TestPassword123!"
    
    try:
        # Check if user exists by username or email
        user = User.objects.get(username=test_username)
        print(f"Test user already exists: {test_username}")
        # Update password and email just in case
        user.email = test_email
        user.set_password(test_password)
        user.save()
    except User.DoesNotExist:
        try:
            # Check by email
            user = User.objects.get(email=test_email)
            print(f"Test user already exists with email: {test_email}")
            # Update password just in case
            user.set_password(test_password)
            user.save()
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=test_username,
                email=test_email,
                password=test_password,
                first_name="Test",
                last_name="User"
            )
            print(f"Created new test user: {test_email}")
    
    print(f"\nTest user credentials:")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    print(f"Username: {test_username}")
    
    return user

if __name__ == "__main__":
    create_test_user()