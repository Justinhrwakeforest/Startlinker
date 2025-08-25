#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from apps.startups.models import Startup
from apps.jobs.models import Job
from apps.posts.models import Post

print("=== DEBUGGING API DATA DISCREPANCY ===")

print("\n--- ALL STARTUPS IN DATABASE ---")
all_startups = Startup.objects.all()
print(f"Total in DB: {all_startups.count()}")
for s in all_startups:
    print(f"- ID: {s.id}, Name: {s.name}, Approved: {s.is_approved}, Featured: {s.is_featured}")

print("\n--- STARTUP FILTERING ANALYSIS ---")
approved_startups = Startup.objects.filter(is_approved=True)
print(f"Approved startups: {approved_startups.count()}")

featured_startups = Startup.objects.filter(is_featured=True)
print(f"Featured startups: {featured_startups.count()}")

print("\n--- JOBS ANALYSIS ---")
active_jobs = Job.objects.filter(status='active')
print(f"Active jobs: {active_jobs.count()}")

inactive_jobs = Job.objects.exclude(status='active')
print(f"Inactive jobs: {inactive_jobs.count()}")

print("\n--- POSTS ANALYSIS ---")
all_posts = Post.objects.all()
print(f"All posts: {all_posts.count()}")

print("\n--- CHECKING API FILTERS ---")
print("Likely the startups API is filtering by is_approved=True")
print("Let's check what the default filters might be...")