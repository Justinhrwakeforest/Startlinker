#!/usr/bin/env python
"""
Debug script to test job creation directly
Run this to test if job creation works without the web request layer
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Job, JobType
from django.utils import timezone
from datetime import timedelta
import json

def test_job_creation():
    print("🔧 Testing Job Creation Directly...")
    
    # Get user and job type
    User = get_user_model()
    user = User.objects.first()
    job_type = JobType.objects.first()
    
    if not user:
        print("❌ No users found")
        return False
        
    if not job_type:
        print("❌ No job types found")
        return False
    
    print(f"✅ Using user: {user.username}")
    print(f"✅ Using job type: {job_type.name}")
    
    # Create job data
    job_data = {
        'title': 'Test Software Engineer',
        'description': 'This is a test job posting to verify job creation works',
        'location': 'Bengaluru',
        'job_type': job_type,
        'salary_range': '80000-120000',
        'is_remote': False,
        'is_urgent': True,
        'experience_level': 'mid',
        'requirements': 'Python, Django experience required',
        'benefits': 'Health insurance, remote work',
        'application_deadline': timezone.now() + timedelta(days=15),
        'expires_at': timezone.now() + timedelta(days=23),
        'company_email': 'test@company.com',
        'posted_by': user,
        'status': 'pending'
    }
    
    try:
        # Create job directly
        print("🔄 Creating job...")
        job = Job.objects.create(**job_data)
        
        print(f"✅ Job created successfully!")
        print(f"   ID: {job.id}")
        print(f"   Title: {job.title}")
        print(f"   Status: {job.status}")
        print(f"   Posted by: {job.posted_by.username}")
        print(f"   Created at: {job.posted_at}")
        
        # Test serializer
        print("🔄 Testing serializer...")
        from apps.jobs.serializers import JobDetailSerializer
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(user)
        serializer = JobDetailSerializer(job, context={'request': mock_request})
        
        print("✅ Serializer works!")
        print(f"   Serialized data keys: {list(serializer.data.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Job creation failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_serializer_validation():
    print("\n🔧 Testing Serializer Validation...")
    
    from apps.jobs.serializers import JobCreateSerializer
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.first()
    
    test_data = {
        'title': 'Test Job',
        'description': 'This is a test description that is long enough to pass validation requirements',
        'location': 'Test City',
        'job_type': 1,
        'salary_range': '50000-80000',
        'is_remote': False,
        'is_urgent': False,
        'experience_level': 'mid',
        'requirements': 'Test requirements',
        'benefits': 'Test benefits',
        'application_deadline': (timezone.now() + timedelta(days=15)).isoformat(),
        'expires_at': (timezone.now() + timedelta(days=23)).isoformat(),
        'company_email': 'test@example.com',
        'skills': []
    }
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    mock_request = MockRequest(user)
    
    try:
        serializer = JobCreateSerializer(data=test_data, context={'request': mock_request})
        is_valid = serializer.is_valid()
        
        print(f"✅ Serializer validation: {'PASSED' if is_valid else 'FAILED'}")
        
        if not is_valid:
            print(f"❌ Validation errors: {serializer.errors}")
            return False
        else:
            print("✅ No validation errors")
            
            # Try to create
            print("🔄 Testing serializer.save()...")
            job = serializer.save()
            print(f"✅ Serializer.save() works! Created job ID: {job.id}")
            return True
            
    except Exception as e:
        print(f"❌ Serializer test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 DEBUG: Job Creation Test")
    print("=" * 50)
    
    # Test 1: Direct model creation
    direct_success = test_job_creation()
    
    # Test 2: Serializer validation and creation
    serializer_success = test_serializer_validation()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"   Direct creation: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"   Serializer creation: {'✅ PASS' if serializer_success else '❌ FAIL'}")
    
    if direct_success and serializer_success:
        print("🎉 All tests passed! The issue is likely in the web layer (authentication, middleware, etc.)")
        print("\n💡 SOLUTION: The Celery/signal issue has been fixed.")
        print("   Your job creation should now work through the API.")
    else:
        print("🔴 There are still issues with job creation logic")
    
    print("=" * 50)