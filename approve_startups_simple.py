#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from apps.startups.models import Startup

print("Approving all new startups...")

# Get all unapproved startups
unapproved_startups = Startup.objects.filter(is_approved=False)
print(f"Found {unapproved_startups.count()} unapproved startups")

count = 0
for startup in unapproved_startups:
    startup.is_approved = True
    startup.save()
    count += 1
    print(f"Approved: {startup.name}")

print(f"Successfully approved {count} startups!")
print(f"Total approved startups now: {Startup.objects.filter(is_approved=True).count()}")