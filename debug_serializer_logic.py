#!/usr/bin/env python
"""
Debug the exact serializer logic to see why jobs might still be auto-approved
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from apps.jobs.models import JobType

def debug_approval_logic():
    print("DEBUGGING JOB APPROVAL LOGIC")
    print("=" * 50)
    
    # Get settings
    job_settings = getattr(settings, 'JOB_POSTING_SETTINGS', {})
    print("Current JOB_POSTING_SETTINGS:")
    for key, value in job_settings.items():
        print(f"  {key}: {value}")
    print()
    
    # Get user info
    User = get_user_model()
    user = User.objects.first()
    
    print(f"Test User: {user.username}")
    print(f"  is_staff: {user.is_staff}")
    print(f"  is_superuser: {user.is_superuser}")
    print()
    
    # Simulate the approval logic from JobCreateSerializer.create()
    auto_approve = job_settings.get('AUTO_APPROVE', True)
    require_review = job_settings.get('REQUIRE_REVIEW', False)
    
    print("Simulating JobCreateSerializer.create() logic:")
    print(f"1. auto_approve = job_settings.get('AUTO_APPROVE', True) = {auto_approve}")
    print(f"2. require_review = job_settings.get('REQUIRE_REVIEW', False) = {require_review}")
    
    should_auto_approve = False
    print(f"3. should_auto_approve = {should_auto_approve} (initial)")
    
    print(f"4. Checking: if not require_review ({not require_review}):")
    if not require_review:
        print("   -> require_review is False, checking auto-approval conditions...")
        
        staff_auto_approve = job_settings.get('AUTO_APPROVE_STAFF', True)
        print(f"   -> AUTO_APPROVE_STAFF = {staff_auto_approve}")
        print(f"   -> User is staff/superuser: {user.is_staff or user.is_superuser}")
        
        if (staff_auto_approve and (user.is_staff or user.is_superuser)):
            should_auto_approve = True
            print(f"   -> STAFF AUTO-APPROVAL TRIGGERED: should_auto_approve = {should_auto_approve}")
        elif auto_approve:
            should_auto_approve = True
            print(f"   -> GENERAL AUTO-APPROVAL TRIGGERED: should_auto_approve = {should_auto_approve}")
        else:
            print("   -> No auto-approval conditions met")
    else:
        print("   -> require_review is True, skipping auto-approval checks")
    
    print(f"5. Final should_auto_approve = {should_auto_approve}")
    
    if should_auto_approve:
        status = 'active'
        is_active = True
        print(f"6. Job will be: status='{status}', is_active={is_active}")
    else:
        status = 'pending'
        is_active = False
        print(f"6. Job will be: status='{status}', is_active={is_active}")
    
    print("\n" + "=" * 50)
    print("EXPECTED BEHAVIOR:")
    if status == 'pending' and not is_active:
        print("✓ CORRECT: Job should require admin approval")
    else:
        print("✗ INCORRECT: Job will be auto-approved")
        
        print("\nISSUE IDENTIFIED:")
        if not require_review and (user.is_staff or user.is_superuser):
            print("-> User is staff/superuser and require_review=False")
            print("-> This triggers auto-approval even with AUTO_APPROVE=False")
            print("-> SOLUTION: Set REQUIRE_REVIEW=True to force all jobs through review")

if __name__ == "__main__":
    debug_approval_logic()