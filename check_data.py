#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.startups.models import Startup
from apps.jobs.models import Job
from apps.posts.models import Post

User = get_user_model()

print("=== CURRENT DATABASE CONTENT ===")
print(f"Total Users: {User.objects.count()}")
print(f"Total Startups: {Startup.objects.count()}")
print(f"Total Jobs: {Job.objects.count()}")
print(f"Total Posts: {Post.objects.count()}")

print("\n=== USERS ===")
for u in User.objects.all()[:10]:
    print(f"- {u.username} ({u.email})")

print("\n=== STARTUPS ===")
for s in Startup.objects.all()[:10]:
    print(f"- {s.name}")

print("\n=== JOBS ===")
for j in Job.objects.all()[:10]:
    startup_name = j.startup.name if j.startup else "Independent"
    print(f"- {j.title} at {startup_name}")

print("\n=== POSTS ===")
for p in Post.objects.all()[:10]:
    print(f"- {p.title} by {p.author.username}")