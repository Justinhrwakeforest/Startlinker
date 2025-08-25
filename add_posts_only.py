#!/usr/bin/env python3
"""
Add Posts Only
Adds remaining posts without emoji issues
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

def add_posts():
    print("Adding posts...")
    
    # Get our diverse users
    users = User.objects.filter(username__in=['sarah_ai_dev', 'miguel_product', 'priya_data_sci', 'alex_frontend', 'diana_ux', 'carlos_devops'])
    
    if not users.exists():
        print("No diverse users found!")
        return
    
    users = list(users)
    
    # Create diverse posts without emojis
    posts_data = [
        {
            'title': 'The Product Manager\'s Dilemma: Features vs. User Experience',
            'content': 'Every PM faces this challenge: stakeholders want more features, but users need better experience. After managing 15+ product launches, here is my framework: 1) Always start with user research, 2) Measure impact, not output, 3) Say no to good ideas that don\'t align with core value, 4) Design for your power users, but onboard for beginners. Remember, a product that tries to do everything usually does nothing well.',
            'author': users[1]  # miguel_product
        },
        {
            'title': 'Why I Left Big Tech for a Healthcare Startup',
            'content': 'Two months ago, I left my comfortable job at a FAANG company to join a healthcare startup. Best decision ever. Here is why: 1) Impact is immediate and visible, 2) Every line of code can save lives, 3) Learning opportunities are endless, 4) Team dynamics are incredible. Yes, startups are risky, but the potential to change lives makes it worth it. If you are considering the jump, ask yourself: what legacy do you want to leave?',
            'author': users[2]  # priya_data_sci
        },
        {
            'title': 'Frontend Performance Tips That Actually Matter in 2024',
            'content': 'After optimizing dozens of React apps, here are the techniques that provide the biggest impact: 1) Code splitting at the route level, 2) Lazy loading images with intersection observer, 3) Service workers for caching, 4) Bundle analysis to identify bloat, 5) CDN for static assets. Pro tip: measure before and after every optimization. Sometimes what you think is slow isn\'t the actual bottleneck.',
            'author': users[3]  # alex_frontend
        },
        {
            'title': 'Designing for Accessibility: It\'s Not Optional Anymore',
            'content': 'Accessibility isn\'t just about compliance - it\'s about creating products everyone can use. As designers, we have a responsibility to build inclusive experiences. Key principles: 1) Design with keyboard navigation in mind, 2) Ensure sufficient color contrast, 3) Write meaningful alt text, 4) Test with screen readers, 5) Include users with disabilities in your research. Remember, accessibility benefits everyone, not just people with disabilities.',
            'author': users[4]  # diana_ux
        },
        {
            'title': 'Kubernetes in Production: Lessons from 3 Years of Scaling',
            'content': 'Running K8s in production taught me valuable lessons: 1) Start simple, complexity comes naturally, 2) Monitoring and observability are not optional, 3) Resource limits prevent one bad pod from killing everything, 4) Backup strategies are crucial, 5) Security should be built in from day one. Biggest mistake teams make? Trying to use every K8s feature from the start. Master the basics first.',
            'author': users[5]  # carlos_devops
        },
        {
            'title': 'The Future of Work: Remote, Hybrid, or Back to Office?',
            'content': 'Having worked in all three models, here are my thoughts: Remote works best for deep work and global talent access. Hybrid is great for collaboration and mentorship. Office is ideal for culture building and spontaneous innovation. The future isn\'t one-size-fits-all - it\'s about matching work style to work type. Companies that figure this out will have a massive talent advantage.',
            'author': users[1]  # miguel_product
        },
        {
            'title': 'Building My First Chrome Extension: A Developer\'s Journey',
            'content': 'Just shipped my first Chrome extension! It took 3 weeks of evening coding, but the learning was incredible. Key takeaways: 1) The Chrome extension APIs are well-documented, 2) Content scripts have limited access for security, 3) Background scripts handle persistent tasks, 4) Users care more about utility than fancy UI. Already at 500+ users and growing. Sometimes the best way to learn is to just start building.',
            'author': users[3]  # alex_frontend
        },
        {
            'title': 'Data Science Ethics: Questions We Should All Be Asking',
            'content': 'As data scientists, we have unprecedented power to influence decisions. With great power comes great responsibility. Questions to ask: 1) Could this model perpetuate existing biases?, 2) Is the data collection transparent and consensual?, 3) How will this algorithm affect different communities?, 4) Can we explain the decision process?, 5) What are the potential misuse cases? Ethics isn\'t a checkbox - it\'s an ongoing conversation.',
            'author': users[2]  # priya_data_sci
        },
        {
            'title': 'Startup Life: The Good, The Bad, and The Reality',
            'content': 'Six months into startup life, here is the unfiltered truth: The Good - incredible learning, direct impact, amazing teammates. The Bad - uncertainty, long hours, constant pressure. The Reality - it\'s not for everyone, and that\'s okay. Before joining a startup, ask yourself: Can you handle ambiguity? Do you thrive in chaos? Are you energized by building from scratch? If yes, you\'ll love it. If no, that\'s perfectly fine too.',
            'author': users[0]  # sarah_ai_dev
        }
    ]
    
    posts = []
    for i, post_data in enumerate(posts_data):
        post, created = Post.objects.get_or_create(
            title=post_data['title'],
            author=post_data['author'],
            defaults={
                'content': post_data['content'],
                'created_at': timezone.now() - timedelta(days=random.randint(1, 14))
            }
        )
        if created:
            print(f"Created post: {post.title[:50]}...")
        posts.append(post)
    
    print(f"Posts creation complete! Added {len([p for p in posts if Post.objects.filter(title=p.title).exists()])} posts")

if __name__ == '__main__':
    add_posts()