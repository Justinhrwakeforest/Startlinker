#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

def debug_admin_blocking():
    print("DEBUGGING ADMIN BLOCKING")
    print("=" * 30)
    
    from apps.users.profanity_filter import contains_offensive_word
    
    result = contains_offensive_word('admin')
    print(f"contains_offensive_word('admin'): {result}")
    
    if result[0]:
        print(f"Reason: Found word '{result[1]}'")
    
    # Test with serializer
    from apps.users.serializers import UserRegistrationSerializer
    
    test_data = {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'Admin',
        'last_name': 'User'
    }
    
    serializer = UserRegistrationSerializer(data=test_data)
    print(f"\nSerializer valid: {serializer.is_valid()}")
    if not serializer.is_valid():
        print(f"Errors: {dict(serializer.errors)}")

if __name__ == "__main__":
    debug_admin_blocking()