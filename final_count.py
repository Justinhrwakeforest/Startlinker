#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.startups.models import Startup, Industry
from apps.jobs.models import Job
from apps.posts.models import Post

User = get_user_model()

print("=== FINAL DATABASE CONTENT ===")
print(f"Total Users: {User.objects.count()}")
print(f"Total Industries: {Industry.objects.count()}")
print(f"Total Startups: {Startup.objects.count()}")
print(f"Total Jobs: {Job.objects.count()}")
print(f"Total Posts: {Post.objects.count()}")

print("\n=== NEW DIVERSE USERS ===")
diverse_users = User.objects.filter(username__in=['sarah_ai_dev', 'miguel_product', 'priya_data_sci', 'alex_frontend', 'diana_ux', 'carlos_devops'])
for u in diverse_users:
    print(f"- {u.first_name} {u.last_name} (@{u.username}) - {u.location}")
    print(f"  {u.bio[:80]}...")

print("\n=== NEW DIVERSE STARTUPS ===")
new_startups = ['NeuroLink AI', 'HealthFlow Analytics', 'CryptoSafe Wallet', 'LearnSphere', 'EcoMarket', 'StreamVerse', 'GreenTech Solutions', 'MedBot Assistance']
for startup_name in new_startups:
    try:
        s = Startup.objects.get(name=startup_name)
        print(f"- {s.name} ({s.industry.name}) - {s.location}")
        print(f"  {s.employee_count} employees, Founded {s.founded_year}, Funding: {s.funding_amount}")
    except Startup.DoesNotExist:
        continue

print("\n=== RECENT POSTS ===")
recent_posts = Post.objects.order_by('-created_at')[:10]
for p in recent_posts:
    print(f"- {p.title[:60]}... by {p.author.first_name} {p.author.last_name}")