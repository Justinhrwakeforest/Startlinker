#!/usr/bin/env python
"""
Simple verification that job approval workflow is working
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.conf import settings
from apps.jobs.models import Job

def verify_settings():
    job_settings = getattr(settings, 'JOB_POSTING_SETTINGS', {})
    
    print("VERIFICATION: Job Approval Settings")
    print("=" * 40)
    print(f"AUTO_APPROVE: {job_settings.get('AUTO_APPROVE', 'DEFAULT: True')}")
    print(f"REQUIRE_REVIEW: {job_settings.get('REQUIRE_REVIEW', 'DEFAULT: False')}")
    print()
    
    # Check the most recently created jobs
    recent_jobs = Job.objects.order_by('-posted_at')[:3]
    
    print("VERIFICATION: Recent Job Status")
    print("=" * 40)
    for job in recent_jobs:
        print(f"Job ID {job.id}: '{job.title[:30]}...'")
        print(f"  Status: {job.status}")
        print(f"  Active: {job.is_active}")
        print(f"  Auto-approved: {'Yes' if job.approved_by else 'No'}")
        print()
    
    # Check if jobs are going to pending status
    pending_jobs = Job.objects.filter(status='pending').count()
    active_jobs = Job.objects.filter(status='active').count()
    
    print("SUMMARY:")
    print(f"Jobs pending approval: {pending_jobs}")
    print(f"Jobs already active: {active_jobs}")
    
    if job_settings.get('AUTO_APPROVE') is False and job_settings.get('REQUIRE_REVIEW') is True:
        print("\nSTATUS: Job approval workflow is CORRECTLY CONFIGURED")
        print("- Jobs will now require admin approval before being published")
        print("- Users will see jobs in 'pending' status after submission")
    else:
        print("\nSTATUS: Job approval workflow needs attention")

if __name__ == "__main__":
    verify_settings()