#!/usr/bin/env python
"""
Simple test setup for startlinker.com
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from apps.startups.models import Industry
from apps.jobs.models import JobType

User = get_user_model()

def setup_test_data():
    """Create test data for testing"""
    print("Setting up test data...")
    
    # Create test user
    try:
        # First try to get existing user
        user = User.objects.filter(email='test@startlinker.com').first()
        
        if not user:
            # Create new user with unique username
            import uuid
            unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
            user = User.objects.create(
                email='test@startlinker.com',
                username=unique_username,
                first_name='Test',
                last_name='User',
                is_active=True,
            )
            created = True
        else:
            created = False
        
        if created:
            user.set_password('Test@123456')
            user.save()
            print(f"[OK] Created test user: {user.email}")
        else:
            print(f"[OK] Test user already exists: {user.email}")
            
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        print(f"[OK] Token: {token.key}")
        
    except Exception as e:
        print(f"[ERROR] Creating test user: {e}")
        return False
    
    # Create industries if they don't exist
    industries = [
        "Technology", "Healthcare", "Finance", "Education", "E-commerce",
        "Marketing", "Real Estate", "Transportation", "Food & Beverage", "Entertainment"
    ]
    
    for industry_name in industries:
        industry, created = Industry.objects.get_or_create(
            name=industry_name,
            defaults={'slug': industry_name.lower().replace(' ', '-').replace('&', 'and')}
        )
        if created:
            print(f"[OK] Created industry: {industry_name}")
    
    # Create job types if they don't exist
    job_types = [
        ("Full-time", "full_time"),
        ("Part-time", "part_time"),
        ("Contract", "contract"),
        ("Internship", "internship"),
        ("Freelance", "freelance")
    ]
    
    for name, slug in job_types:
        job_type, created = JobType.objects.get_or_create(
            name=name,
            defaults={'slug': slug}
        )
        if created:
            print(f"[OK] Created job type: {name}")
    
    print("\n" + "=" * 50)
    print("TEST DATA SETUP COMPLETE!")
    print("=" * 50)
    print("\nTest Credentials:")
    print(f"  Email: test@startlinker.com")
    print(f"  Password: Test@123456")
    print(f"  Token: {token.key}")
    print("\nYou can now test the API with these credentials.")
    
    return True

if __name__ == "__main__":
    setup_test_data()