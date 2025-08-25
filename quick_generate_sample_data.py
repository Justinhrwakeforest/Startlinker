#!/usr/bin/env python3
"""
Quick Sample Data Generator
Creates a smaller set of sample data to verify the system works
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.startups.models import Startup, Industry, UserProfile
from apps.jobs.models import Job, JobType
from apps.posts.models import Post

User = get_user_model()

def create_sample_data():
    print("Creating sample data...")
    
    # Create industries first
    tech_industry, created = Industry.objects.get_or_create(
        name='Technology',
        defaults={'icon': '💻', 'description': 'Technology and software companies'}
    )
    
    health_industry, created = Industry.objects.get_or_create(
        name='Healthcare', 
        defaults={'icon': '🏥', 'description': 'Healthcare and medical companies'}
    )
    
    # Create 3 sample users
    users_data = [
        {
            'username': 'john_dev',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Developer',
            'bio': 'Software developer passionate about creating innovative solutions.',
            'location': 'San Francisco, CA'
        },
        {
            'username': 'sara_pm',
            'email': 'sara@example.com', 
            'first_name': 'Sara',
            'last_name': 'Manager',
            'bio': 'Product manager focused on user experience and growth.',
            'location': 'New York, NY'
        },
        {
            'username': 'mike_data',
            'email': 'mike@example.com',
            'first_name': 'Mike',
            'last_name': 'Analyst', 
            'bio': 'Data scientist turning data into insights.',
            'location': 'Seattle, WA'
        }
    ]
    
    users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'bio': user_data['bio'],
                'location': user_data['location']
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Create profile
            UserProfile.objects.get_or_create(user=user)
            print(f"Created user: {user.username}")
        users.append(user)
    
    # Create 5 sample startups
    startups_data = [
        {
            'name': 'TechFlow Solutions',
            'description': 'Building the next generation of workflow automation tools.',
            'industry': tech_industry,
            'location': 'San Francisco, CA',
            'employee_count': 25,
            'founded_year': 2022,
            'funding_amount': '$2M'
        },
        {
            'name': 'HealthTrack AI',
            'description': 'AI-powered health monitoring and analytics platform.',
            'industry': health_industry,
            'location': 'Boston, MA',
            'employee_count': 15,
            'founded_year': 2023,
            'funding_amount': '$1M'
        },
        {
            'name': 'DataViz Pro',
            'description': 'Advanced data visualization and business intelligence tools.',
            'industry': tech_industry,
            'location': 'Seattle, WA',
            'employee_count': 30,
            'founded_year': 2021,
            'funding_amount': '$5M'
        },
        {
            'name': 'MobileFirst Labs',
            'description': 'Cross-platform mobile development framework and tools.',
            'industry': tech_industry,
            'location': 'Austin, TX',
            'employee_count': 20,
            'founded_year': 2022,
            'funding_amount': '$3M'
        },
        {
            'name': 'CloudSync Enterprise',
            'description': 'Enterprise cloud synchronization and backup solutions.',
            'industry': tech_industry,
            'location': 'Denver, CO',
            'employee_count': 40,
            'founded_year': 2020,
            'funding_amount': '$10M'
        }
    ]
    
    startups = []
    for startup_data in startups_data:
        startup, created = Startup.objects.get_or_create(
            name=startup_data['name'],
            defaults=startup_data
        )
        if created:
            print(f"Created startup: {startup.name}")
        startups.append(startup)
    
    # Create job types
    job_type_full, created = JobType.objects.get_or_create(name='Full-time')
    job_type_contract, created = JobType.objects.get_or_create(name='Contract')
    
    # Create 5 sample jobs
    jobs_data = [
        {
            'title': 'Senior Software Engineer',
            'description': 'We are looking for a senior software engineer to join our team and help build the next generation of our platform.',
            'startup': startups[0],
            'job_type': job_type_full,
            'experience_level': 'senior',
            'location': 'San Francisco, CA',
            'salary_range': '$120,000 - $150,000',
            'is_remote': False,
            'posted_by': users[0],
            'company_email': 'hr@techflow.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'Product Manager',
            'description': 'Join our product team to drive strategy and roadmap for our health monitoring platform.',
            'startup': startups[1],
            'job_type': job_type_full,
            'experience_level': 'mid',
            'location': 'Remote',
            'salary_range': '$90,000 - $120,000',
            'is_remote': True,
            'posted_by': users[1],
            'company_email': 'jobs@healthtrack.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'Data Scientist',
            'description': 'Help us turn complex data into actionable insights for our business intelligence platform.',
            'startup': startups[2],
            'job_type': job_type_full,
            'experience_level': 'mid',
            'location': 'Seattle, WA',
            'salary_range': '$100,000 - $130,000',
            'is_remote': False,
            'posted_by': users[2],
            'company_email': 'careers@datavizpro.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'Frontend Developer',
            'description': 'Build beautiful and responsive user interfaces for our mobile development tools.',
            'startup': startups[3],
            'job_type': job_type_contract,
            'experience_level': 'mid',
            'location': 'Austin, TX',
            'salary_range': '$70,000 - $90,000',
            'is_remote': True,
            'posted_by': users[0],
            'company_email': 'hello@mobilefirst.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'DevOps Engineer',
            'description': 'Manage and scale our cloud infrastructure to support enterprise customers.',
            'startup': startups[4],
            'job_type': job_type_full,
            'experience_level': 'senior',
            'location': 'Denver, CO',
            'salary_range': '$110,000 - $140,000',
            'is_remote': False,
            'posted_by': users[1],
            'company_email': 'team@cloudsync.com',
            'status': 'active',
            'is_active': True
        }
    ]
    
    jobs = []
    for job_data in jobs_data:
        job, created = Job.objects.get_or_create(
            title=job_data['title'],
            startup=job_data['startup'],
            defaults=job_data
        )
        if created:
            print(f"Created job: {job.title} at {job.startup.name}")
        jobs.append(job)
    
    # Create 5 sample posts
    posts_data = [
        {
            'title': 'Just shipped a major feature update! 🚀',
            'content': 'After weeks of development, we finally released our new dashboard. The team worked incredibly hard to make this happen. Excited to see user feedback!',
            'author': users[0]
        },
        {
            'title': 'The future of product management',
            'content': 'Working in product management has taught me that the best products come from truly understanding user needs. Always start with the problem, not the solution.',
            'author': users[1]
        },
        {
            'title': 'Data insights that changed everything',
            'content': 'Sometimes a simple data visualization can reveal patterns that completely shift your business strategy. Data science is not just about algorithms - it is about storytelling.',
            'author': users[2]
        },
        {
            'title': 'Remote work productivity tips',
            'content': 'After 2 years of remote work, here are my top tips: 1) Set clear boundaries, 2) Have a dedicated workspace, 3) Take regular breaks, 4) Communicate proactively with your team.',
            'author': users[0]
        },
        {
            'title': 'Building inclusive teams',
            'content': 'Diversity in tech teams consistently leads to better products and more innovative solutions. We need to keep pushing for inclusive workplaces where everyone can thrive.',
            'author': users[1]
        }
    ]
    
    posts = []
    for post_data in posts_data:
        post, created = Post.objects.get_or_create(
            title=post_data['title'],
            author=post_data['author'],
            defaults={
                'content': post_data['content'],
                'created_at': timezone.now() - timedelta(days=random.randint(1, 10))
            }
        )
        if created:
            print(f"Created post: {post.title}")
        posts.append(post)
    
    print(f"\nSample data creation complete!")
    print(f"Created {len(users)} users, {len(startups)} startups, {len(jobs)} jobs, {len(posts)} posts")
    
    return users, startups, jobs, posts

if __name__ == '__main__':
    create_sample_data()