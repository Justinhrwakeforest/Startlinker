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

print("=== FINAL METADATA STATUS ===")

# Count meta users
meta_users = User.objects.filter(username__in=[
    'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
    'alex_frontend', 'diana_ux', 'carlos_devops',
    'emma_backend', 'david_mobile', 'sofia_security', 'james_qa'
])

print(f"Meta Users: {meta_users.count()}/10")
print(f"Startups: {Startup.objects.count()}/100")
print(f"Jobs: {Job.objects.count()}/100") 
print(f"Posts: {Post.objects.count()}/100")

# Check targets
all_complete = (
    meta_users.count() >= 10 and
    Startup.objects.count() >= 100 and
    Job.objects.count() >= 100 and
    Post.objects.count() >= 100
)

if all_complete:
    print("\n🎉 ALL TARGETS REACHED!")
else:
    print(f"\n⚠️ Still working on targets")

print(f"\nView at http://localhost:3000")