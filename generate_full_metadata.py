#!/usr/bin/env python3
"""
Generate Full Metadata: 10 Users, 100 Startups, 100 Jobs, 100 Posts
Creates the exact numbers requested by the user
"""

import os
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

def generate_full_metadata():
    print("Generating complete metadata set...")
    
    # First, let's complete the 10 users
    print("\n=== GENERATING 10 USERS ===")
    current_meta_users = User.objects.filter(username__in=[
        'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
        'alex_frontend', 'diana_ux', 'carlos_devops'
    ]).count()
    
    print(f"Current meta users: {current_meta_users}")
    
    # Generate 4 more users to reach 10 total
    additional_users_data = [
        {
            'username': 'emma_backend',
            'email': 'emma.backend@example.com',
            'first_name': 'Emma',
            'last_name': 'Wilson',
            'bio': 'Backend Engineer specializing in microservices and distributed systems. Python and Go enthusiast.',
            'location': 'Toronto, Canada'
        },
        {
            'username': 'david_mobile',
            'email': 'david.mobile@example.com',
            'first_name': 'David',
            'last_name': 'Lee',
            'bio': 'Mobile Developer creating cross-platform apps with React Native and Flutter.',
            'location': 'Vancouver, Canada'
        },
        {
            'username': 'sofia_security',
            'email': 'sofia.security@example.com',
            'first_name': 'Sofia',
            'last_name': 'Garcia',
            'bio': 'Cybersecurity Engineer protecting digital assets. Penetration testing and security auditing specialist.',
            'location': 'Mexico City, Mexico'
        },
        {
            'username': 'james_qa',
            'email': 'james.qa@example.com',
            'first_name': 'James',
            'last_name': 'Taylor',
            'bio': 'QA Engineer ensuring software quality through automation and testing frameworks.',
            'location': 'London, UK'
        }
    ]
    
    meta_users = []
    
    # Get existing meta users
    existing_users = User.objects.filter(username__in=[
        'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
        'alex_frontend', 'diana_ux', 'carlos_devops'
    ])
    meta_users.extend(list(existing_users))
    
    # Add new users
    for user_data in additional_users_data:
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
            UserProfile.objects.get_or_create(user=user)
            print(f"Created user: {user.username}")
        meta_users.append(user)
    
    print(f"Total meta users: {len(meta_users)}")
    
    # Generate 100 startups
    print("\n=== GENERATING 100 STARTUPS ===")
    current_startups = Startup.objects.count()
    print(f"Current startups: {current_startups}")
    
    # Ensure we have enough industries
    industries_data = [
        {'name': 'Technology', 'icon': '💻'},
        {'name': 'Healthcare', 'icon': '🏥'},
        {'name': 'Finance', 'icon': '💰'},
        {'name': 'Education', 'icon': '📚'},
        {'name': 'E-commerce', 'icon': '🛒'},
        {'name': 'Entertainment', 'icon': '🎬'},
        {'name': 'Transportation', 'icon': '🚗'},
        {'name': 'Food & Beverage', 'icon': '🍔'},
        {'name': 'Real Estate', 'icon': '🏠'},
        {'name': 'Energy', 'icon': '⚡'},
        {'name': 'Manufacturing', 'icon': '🏭'},
        {'name': 'Agriculture', 'icon': '🌾'},
        {'name': 'Retail', 'icon': '🏪'},
        {'name': 'Travel', 'icon': '✈️'},
        {'name': 'Sports', 'icon': '⚽'},
        {'name': 'Fashion', 'icon': '👕'},
        {'name': 'Media', 'icon': '📺'},
        {'name': 'Gaming', 'icon': '🎮'},
        {'name': 'Consulting', 'icon': '💼'},
        {'name': 'Marketing', 'icon': '📢'},
    ]
    
    industries = []
    for industry_data in industries_data:
        industry, created = Industry.objects.get_or_create(
            name=industry_data['name'],
            defaults={'icon': industry_data['icon']}
        )
        industries.append(industry)
    
    # Startup name templates
    startup_prefixes = [
        'Tech', 'Smart', 'Digital', 'Cyber', 'Cloud', 'Data', 'AI', 'Quantum', 'Nano', 'Bio',
        'Eco', 'Green', 'Blue', 'Red', 'Alpha', 'Beta', 'Next', 'Future', 'Ultra', 'Super',
        'Pro', 'Elite', 'Prime', 'Core', 'Meta', 'Hyper', 'Mega', 'Micro', 'Multi', 'Neo'
    ]
    
    startup_suffixes = [
        'Systems', 'Solutions', 'Technologies', 'Labs', 'Studios', 'Works', 'Hub', 'Center',
        'Platform', 'Network', 'Connect', 'Link', 'Bridge', 'Flow', 'Stream', 'Wave',
        'Spark', 'Boost', 'Drive', 'Force', 'Power', 'Engine', 'Gear', 'Tool', 'Kit',
        'Pro', 'Plus', 'Max', 'Elite', 'Prime', 'Core', 'Edge', 'Peak', 'Apex', 'Zen'
    ]
    
    startup_descriptions = [
        "Innovative technology solutions for modern businesses",
        "Cutting-edge platform transforming industry standards",
        "AI-powered tools for enhanced productivity",
        "Revolutionary approach to digital transformation",
        "Next-generation software for enterprise clients",
        "Advanced analytics and data visualization platform",
        "Seamless integration solutions for complex systems",
        "User-centric design meets powerful functionality",
        "Scalable cloud infrastructure for growing companies",
        "Automated workflows reducing operational overhead"
    ]
    
    locations = [
        'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA', 'Boston, MA',
        'Los Angeles, CA', 'Chicago, IL', 'Denver, CO', 'Miami, FL', 'Portland, OR',
        'Atlanta, GA', 'Dallas, TX', 'Phoenix, AZ', 'San Diego, CA', 'Nashville, TN',
        'Toronto, Canada', 'Vancouver, Canada', 'London, UK', 'Berlin, Germany', 'Amsterdam, Netherlands',
        'Tel Aviv, Israel', 'Singapore', 'Tokyo, Japan', 'Sydney, Australia', 'Bangalore, India'
    ]
    
    funding_amounts = [
        'Bootstrapped', '$100K', '$250K', '$500K', '$1M', '$2M', '$5M', '$10M', '$15M', '$25M'
    ]
    
    # Generate startups to reach 100 total
    startups_needed = 100 - current_startups
    print(f"Need to generate {startups_needed} more startups")
    
    for i in range(startups_needed):
        prefix = random.choice(startup_prefixes)
        suffix = random.choice(startup_suffixes)
        name = f"{prefix}{suffix}"
        
        # Make sure name is unique
        counter = 1
        original_name = name
        while Startup.objects.filter(name=name).exists():
            name = f"{original_name} {counter}"
            counter += 1
        
        startup = Startup.objects.create(
            name=name,
            description=random.choice(startup_descriptions),
            industry=random.choice(industries),
            location=random.choice(locations),
            employee_count=random.randint(5, 200),
            founded_year=random.randint(2018, 2024),
            funding_amount=random.choice(funding_amounts),
            is_featured=random.random() > 0.85,
            is_approved=True,  # Make sure they're approved
            website=f'https://{name.lower().replace(" ", "")}.com'
        )
        
        if (i + 1) % 20 == 0:
            print(f"Generated {i + 1} startups...")
    
    print(f"Total startups now: {Startup.objects.count()}")
    
    # Generate 100 jobs
    print("\n=== GENERATING 100 JOBS ===")
    current_jobs = Job.objects.count()
    print(f"Current jobs: {current_jobs}")
    
    # Ensure job types exist
    job_types_data = ['Full-time', 'Part-time', 'Contract', 'Internship']
    job_types = []
    for job_type_name in job_types_data:
        job_type, created = JobType.objects.get_or_create(name=job_type_name)
        job_types.append(job_type)
    
    # Job title templates
    job_titles = [
        'Software Engineer', 'Senior Software Engineer', 'Lead Software Engineer',
        'Frontend Developer', 'Backend Developer', 'Full Stack Developer',
        'Product Manager', 'Senior Product Manager', 'Product Owner',
        'Data Scientist', 'Data Analyst', 'Data Engineer',
        'DevOps Engineer', 'Site Reliability Engineer', 'Cloud Engineer',
        'UX Designer', 'UI Designer', 'Product Designer',
        'Marketing Manager', 'Digital Marketing Specialist', 'Content Manager',
        'Sales Manager', 'Business Development Manager', 'Account Executive',
        'Customer Success Manager', 'Support Engineer', 'Technical Writer',
        'Security Engineer', 'Network Engineer', 'Systems Administrator',
        'Mobile Developer', 'iOS Developer', 'Android Developer',
        'Machine Learning Engineer', 'AI Research Scientist', 'Data Research Scientist',
        'Quality Assurance Engineer', 'Test Engineer', 'Automation Engineer',
        'Business Analyst', 'Project Manager', 'Scrum Master',
        'Finance Manager', 'HR Generalist', 'Operations Manager'
    ]
    
    salary_ranges = [
        '$40,000 - $60,000', '$50,000 - $70,000', '$60,000 - $80,000', '$70,000 - $90,000',
        '$80,000 - $100,000', '$90,000 - $120,000', '$100,000 - $130,000', '$120,000 - $150,000',
        '$130,000 - $160,000', '$150,000 - $200,000', '$30 - $50 per hour', '$50 - $80 per hour'
    ]
    
    experience_levels = ['entry', 'mid', 'senior', 'lead']
    
    # Get all startups for job assignment
    all_startups = list(Startup.objects.all())
    
    jobs_needed = 100 - current_jobs
    print(f"Need to generate {jobs_needed} more jobs")
    
    for i in range(jobs_needed):
        title = random.choice(job_titles)
        startup = random.choice(all_startups)
        posting_user = random.choice(meta_users)
        
        job = Job.objects.create(
            title=title,
            description=f"Join our team at {startup.name} as a {title}. We're looking for a talented professional to help us build the future of {startup.industry.name.lower()}. This is an excellent opportunity to work with cutting-edge technology and make a real impact in a growing company.",
            startup=startup,
            job_type=random.choice(job_types),
            experience_level=random.choice(experience_levels),
            location=startup.location if random.random() > 0.3 else 'Remote',
            salary_range=random.choice(salary_ranges),
            is_remote=random.random() > 0.4,
            is_urgent=random.random() > 0.8,
            application_deadline=timezone.now() + timedelta(days=random.randint(30, 90)),
            posted_at=timezone.now() - timedelta(days=random.randint(1, 30)),
            posted_by=posting_user,
            company_email=f'hr@{startup.name.lower().replace(" ", "")}.com',
            status='active',
            is_active=True
        )
        
        if (i + 1) % 20 == 0:
            print(f"Generated {i + 1} jobs...")
    
    print(f"Total jobs now: {Job.objects.count()}")
    
    # Generate 100 posts
    print("\n=== GENERATING 100 POSTS ===")
    current_posts = Post.objects.count()
    print(f"Current posts: {current_posts}")
    
    # Post title and content templates
    post_templates = [
        ("Just shipped a major feature!", "After weeks of development, our team successfully launched a game-changing feature. The collaboration and dedication from everyone involved was incredible."),
        ("Lessons learned from scaling our platform", "Growing from 100 to 10,000 users taught us valuable lessons about architecture, performance, and user experience. Here's what we discovered."),
        ("The importance of code reviews", "Good code reviews have transformed our development process. They catch bugs, share knowledge, and improve code quality across the team."),
        ("Remote work productivity tips", "After working remotely for 2+ years, here are the strategies that have helped me stay productive and maintain work-life balance."),
        ("Building inclusive teams", "Diversity in tech teams consistently leads to better products and innovative solutions. Creating inclusive environments should be every company's priority."),
        ("Career growth in tech", "Reflecting on my journey from junior to senior developer. The key lessons that accelerated my career growth and opened new opportunities."),
        ("The future of AI in development", "AI tools are transforming how we write code, but human creativity and problem-solving remain irreplaceable. Here's how to embrace both."),
        ("Debugging horror stories", "Sometimes the most frustrating bugs teach us the most valuable lessons. Sharing a recent debugging adventure that took 3 days to solve."),
        ("Open source contributions", "Contributing to open source projects has been one of the best decisions for my career. Here's how to get started and make meaningful contributions."),
        ("Tech conference highlights", "Just returned from an amazing tech conference. The keynotes on quantum computing and sustainable technology were mind-blowing."),
        ("Startup life realities", "6 months into startup life: the good, the challenging, and everything in between. It's definitely not for everyone, but I love it."),
        ("Mentorship matters", "Being mentored early in my career was transformative. Now I'm paying it forward by mentoring junior developers. The impact goes both ways."),
        ("API design best practices", "Well-designed APIs are the backbone of modern applications. Here are the principles that guide our API development process."),
        ("Testing strategies that work", "A comprehensive testing strategy has saved us countless hours and prevented numerous production issues. Here's our approach."),
        ("Work-life balance in tech", "Burnout is real in our industry. Here are the practices that help me maintain energy and passion for coding while staying healthy."),
        ("Database optimization tips", "Query performance can make or break user experience. Sharing some database optimization techniques that dramatically improved our app speed."),
        ("Security first development", "Security isn't an afterthought - it's a fundamental part of good software design. Essential practices every developer should know."),
        ("The power of documentation", "Good documentation is a force multiplier for development teams. It saves time, reduces confusion, and helps onboard new team members."),
        ("Continuous learning strategies", "Technology evolves rapidly. Here's how I stay current with new frameworks, languages, and industry trends."),
        ("Building scalable systems", "Lessons learned from architecting systems that handle millions of requests. Planning for scale from day one is crucial.")
    ]
    
    posts_needed = 100 - current_posts
    print(f"Need to generate {posts_needed} more posts")
    
    for i in range(posts_needed):
        title_template, content_template = random.choice(post_templates)
        author = random.choice(meta_users)
        
        # Add some variation to the content
        variations = [
            " What has your experience been with this?",
            " I'd love to hear your thoughts and experiences.",
            " Has anyone else encountered similar challenges?",
            " Always learning from the community's insights.",
            " The tech community's shared knowledge is invaluable."
        ]
        
        if random.random() > 0.5:
            content_template += random.choice(variations)
        
        post = Post.objects.create(
            title=title_template,
            content=content_template,
            author=author,
            created_at=timezone.now() - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )
        
        if (i + 1) % 20 == 0:
            print(f"Generated {i + 1} posts...")
    
    print(f"Total posts now: {Post.objects.count()}")
    
    # Final summary
    print("\n=== FINAL SUMMARY ===")
    print(f"Users: {len(meta_users)} (meta users)")
    print(f"Total Users in DB: {User.objects.count()}")
    print(f"Startups: {Startup.objects.count()}")
    print(f"Jobs: {Job.objects.count()}")
    print(f"Posts: {Post.objects.count()}")
    print(f"Industries: {Industry.objects.count()}")
    
    print("\n✅ Full metadata generation complete!")

if __name__ == '__main__':
    generate_full_metadata()