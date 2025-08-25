#!/usr/bin/env python3
"""
Script to create test users for the platform
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

def create_test_users():
    """Create some test users for the platform"""
    
    test_users = [
        {
            'username': 'VasanthKumar',
            'email': 'vasanth@example.com',
            'first_name': 'Vasanth',
            'last_name': 'Kumar N',
            'password': 'testpass123'
        },
        {
            'username': 'SarahTech',
            'email': 'sarah@example.com', 
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'password': 'testpass123'
        },
        {
            'username': 'DevMike',
            'email': 'mike@example.com',
            'first_name': 'Michael',
            'last_name': 'Chen', 
            'password': 'testpass123'
        },
        {
            'username': 'TechFounder',
            'email': 'founder@example.com',
            'first_name': 'Alex',
            'last_name': 'Smith',
            'password': 'testpass123'
        }
    ]
    
    created_count = 0
    
    for user_data in test_users:
        # Check if user already exists
        if User.objects.filter(username=user_data['username']).exists():
            print(f"User {user_data['username']} already exists, skipping...")
            continue
            
        if User.objects.filter(email=user_data['email']).exists():
            print(f"Email {user_data['email']} already exists, skipping...")
            continue
        
        # Create the user
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            password=user_data['password']
        )
        user.is_active = True
        user.save()
        
        print(f"Created user: {user.username} (ID: {user.id})")
        created_count += 1
    
    print(f"\nCreated {created_count} new test users")
    print(f"Total users in database: {User.objects.count()}")

if __name__ == '__main__':
    print("Creating test users for StartLinker...")
    create_test_users()
    print("Done!")