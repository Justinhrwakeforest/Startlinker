#!/usr/bin/env python
"""
Check the most recent jobs in the database to see their status
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from apps.jobs.models import Job
from django.utils import timezone

def check_recent_jobs():
    print("CHECKING MOST RECENT JOBS IN DATABASE")
    print("=" * 50)
    
    # Get the 10 most recent jobs
    recent_jobs = Job.objects.order_by('-posted_at')[:10]
    
    print(f"Found {recent_jobs.count()} recent jobs:")
    print()
    
    for job in recent_jobs:
        print(f"Job ID {job.id}:")
        print(f"  Title: {job.title[:50]}...")
        print(f"  Status: {job.status}")
        print(f"  Active: {job.is_active}")
        print(f"  Posted by: {job.posted_by.username}")
        print(f"  Posted at: {job.posted_at}")
        print(f"  Approved by: {job.approved_by}")
        print(f"  Approved at: {job.approved_at}")
        
        # Check if this job was auto-approved
        if job.status == 'active' and job.is_active and job.approved_by:
            print("  >> AUTO-APPROVED")
        elif job.status == 'pending' and not job.is_active:
            print("  >> REQUIRES APPROVAL")
        else:
            print(f"  >> UNUSUAL STATUS: {job.status}, active={job.is_active}")
        
        print()
    
    # Summary
    pending_count = recent_jobs.filter(status='pending').count()
    active_count = recent_jobs.filter(status='active').count()
    
    print("SUMMARY:")
    print(f"Recent jobs pending approval: {pending_count}")
    print(f"Recent jobs already active: {active_count}")
    
    if pending_count > active_count:
        print("\nGOOD: More jobs are pending than active")
        print("This suggests the approval workflow is working")
    elif active_count > pending_count:
        print("\nPROBLEM: More jobs are active than pending")
        print("This suggests jobs are still being auto-approved")
    else:
        print("\nMIXED RESULTS")

if __name__ == "__main__":
    check_recent_jobs()