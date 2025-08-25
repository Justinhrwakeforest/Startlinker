#!/usr/bin/env python3
import os
import django
import random
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.posts.models import Post

User = get_user_model()

# Bulk create posts
meta_users = list(User.objects.filter(username__in=[
    'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
    'alex_frontend', 'diana_ux', 'carlos_devops',
    'emma_backend', 'david_mobile', 'sofia_security', 'james_qa'
]))

current_count = Post.objects.count()
needed = 100 - current_count

print(f"Creating {needed} posts...")

posts_to_create = []
titles = [
    "Tech Innovation", "Development Best Practices", "Team Collaboration", "Code Quality",
    "Performance Optimization", "Security Implementation", "User Experience Design", "API Development",
    "Database Management", "Testing Strategies", "DevOps Automation", "Project Management",
    "Career Growth", "Learning Resources", "Industry Trends", "Problem Solving",
    "Productivity Tips", "Tool Recommendations", "Architecture Decisions", "Debugging Techniques"
]

contents = [
    "Sharing insights from recent project work and key lessons learned.",
    "Best practices that have improved our development process significantly.", 
    "Practical approaches that deliver real value for development teams.",
    "Important considerations for modern software development practices.",
    "Strategies that have proven effective in our day-to-day work."
]

for i in range(needed):
    posts_to_create.append(Post(
        title=f"{random.choice(titles)} - {i+1}",
        content=random.choice(contents),
        author=random.choice(meta_users),
        created_at=timezone.now() - timedelta(days=random.randint(1, 30))
    ))

Post.objects.bulk_create(posts_to_create, batch_size=50)
print(f"Total posts now: {Post.objects.count()}")