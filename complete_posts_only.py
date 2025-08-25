#!/usr/bin/env python3
"""
Complete Posts Only - Just finish the posts to reach 100
"""

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

def complete_posts_only():
    print("Completing posts to reach 100...")
    
    # Get meta users
    meta_users = list(User.objects.filter(username__in=[
        'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
        'alex_frontend', 'diana_ux', 'carlos_devops',
        'emma_backend', 'david_mobile', 'sofia_security', 'james_qa'
    ]))
    
    current_posts = Post.objects.count()
    print(f"Current posts: {current_posts}")
    
    if current_posts < 100:
        posts_needed = 100 - current_posts
        print(f"Need {posts_needed} more posts")
        
        # Simple post templates
        titles = [
            "Code review best practices", "Remote work productivity", "Tech stack evolution",
            "Performance optimization wins", "Team collaboration tools", "Learning from failures",
            "API design principles", "Database optimization", "Security implementation",
            "Testing strategies", "DevOps automation", "User experience insights",
            "Product development cycle", "Agile methodology", "Technical debt management",
            "Monitoring and alerts", "Scalability patterns", "Code quality metrics",
            "Innovation processes", "Team building", "Problem solving approach",
            "Technology trends", "Industry insights", "Career development",
            "Skill improvement", "Project management", "Communication strategies",
            "Leadership lessons", "Mentorship experience", "Conference learnings",
            "Open source contribution", "Side project updates", "Tool recommendations",
            "Debugging techniques", "Architecture decisions", "Performance testing",
            "Security auditing", "Data analysis", "Machine learning applications",
            "Mobile development", "Web technologies", "Cloud platforms"
        ]
        
        contents = [
            "Sharing insights from recent project experience and what worked well for our team.",
            "Key lessons learned that have improved our development process and team productivity.",
            "Practical tips and strategies that have made a real difference in our workflow.",
            "Reflecting on challenges overcome and solutions that proved most effective.",
            "Best practices discovered through trial and error, now part of our standard approach.",
            "Important considerations when implementing new technologies or methodologies.",
            "Real-world experiences and outcomes from applying theoretical concepts.",
            "Valuable feedback from the community has shaped our understanding of this topic.",
            "Continuous improvement mindset leads to better results and team satisfaction.",
            "Collaboration and knowledge sharing drive innovation and problem-solving success."
        ]
        
        for i in range(posts_needed):
            title = random.choice(titles)
            content = random.choice(contents)
            author = random.choice(meta_users)
            
            Post.objects.create(
                title=title,
                content=content,
                author=author,
                created_at=timezone.now() - timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            )
            
            if (i + 1) % 10 == 0:
                print(f"Added {i + 1} posts...")
        
        print(f"Total posts now: {Post.objects.count()}")
    
    print(f"✅ COMPLETE: Posts: {Post.objects.count()}/100")

if __name__ == '__main__':
    complete_posts_only()