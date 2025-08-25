#!/usr/bin/env python3
"""
Add Diverse Sample Data
Adds additional diverse content to showcase the platform
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

def add_diverse_sample_data():
    print("Adding diverse sample data...")
    
    # Create more industries
    industries_data = [
        {'name': 'Technology', 'icon': '💻', 'description': 'Technology and software companies'},
        {'name': 'Healthcare', 'icon': '🏥', 'description': 'Healthcare and medical companies'},
        {'name': 'Finance', 'icon': '💰', 'description': 'Financial services and fintech'},
        {'name': 'Education', 'icon': '📚', 'description': 'Educational technology and learning platforms'},
        {'name': 'E-commerce', 'icon': '🛒', 'description': 'Online retail and marketplace platforms'},
        {'name': 'Entertainment', 'icon': '🎬', 'description': 'Media, gaming, and entertainment'},
    ]
    
    industries = {}
    for industry_data in industries_data:
        industry, created = Industry.objects.get_or_create(
            name=industry_data['name'],
            defaults={
                'icon': industry_data['icon'],
                'description': industry_data['description']
            }
        )
        industries[industry.name] = industry
        if created:
            print(f"Created industry: {industry.name}")
    
    # Create diverse users
    users_data = [
        {
            'username': 'sarah_ai_dev',
            'email': 'sarah.ai@example.com',
            'first_name': 'Sarah',
            'last_name': 'Chen',
            'bio': 'AI/ML Engineer passionate about computer vision and deep learning. Building the future of autonomous systems.',
            'location': 'San Francisco, CA'
        },
        {
            'username': 'miguel_product',
            'email': 'miguel.pm@example.com', 
            'first_name': 'Miguel',
            'last_name': 'Rodriguez',
            'bio': 'Product Manager with 8+ years experience. Focus on user-centric design and data-driven decisions.',
            'location': 'Austin, TX'
        },
        {
            'username': 'priya_data_sci',
            'email': 'priya.ds@example.com',
            'first_name': 'Priya',
            'last_name': 'Singh', 
            'bio': 'Data Scientist specializing in predictive analytics and business intelligence.',
            'location': 'New York, NY'
        },
        {
            'username': 'alex_frontend',
            'email': 'alex.fe@example.com',
            'first_name': 'Alex',
            'last_name': 'Johnson',
            'bio': 'Frontend Developer creating beautiful, accessible web experiences with React and Vue.js.',
            'location': 'Seattle, WA'
        },
        {
            'username': 'diana_ux',
            'email': 'diana.ux@example.com',
            'first_name': 'Diana',
            'last_name': 'Kim',
            'bio': 'UX Designer advocating for inclusive design. Turning complex problems into simple solutions.',
            'location': 'Los Angeles, CA'
        },
        {
            'username': 'carlos_devops',
            'email': 'carlos.devops@example.com',
            'first_name': 'Carlos',
            'last_name': 'Martinez',
            'bio': 'DevOps Engineer building scalable cloud infrastructure. Kubernetes and AWS enthusiast.',
            'location': 'Denver, CO'
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
    
    # Create diverse startups
    startups_data = [
        {
            'name': 'NeuroLink AI',
            'description': 'Advanced brain-computer interface technology for medical applications. Helping paralyzed patients regain control.',
            'industry': industries['Technology'],
            'location': 'San Francisco, CA',
            'employee_count': 45,
            'founded_year': 2021,
            'funding_amount': '$15M',
            'is_featured': True
        },
        {
            'name': 'HealthFlow Analytics',
            'description': 'Real-time health data analytics platform for hospitals. Improving patient outcomes through predictive insights.',
            'industry': industries['Healthcare'],
            'location': 'Boston, MA',
            'employee_count': 32,
            'founded_year': 2020,
            'funding_amount': '$8M'
        },
        {
            'name': 'CryptoSafe Wallet',
            'description': 'Next-generation cryptocurrency wallet with military-grade security. Your keys, your crypto, your control.',
            'industry': industries['Finance'],
            'location': 'Miami, FL',
            'employee_count': 28,
            'founded_year': 2022,
            'funding_amount': '$12M',
            'is_featured': True
        },
        {
            'name': 'LearnSphere',
            'description': 'Adaptive learning platform using AI to personalize education. Making quality education accessible to everyone.',
            'industry': industries['Education'],
            'location': 'Chicago, IL',
            'employee_count': 55,
            'founded_year': 2019,
            'funding_amount': '$20M'
        },
        {
            'name': 'EcoMarket',
            'description': 'Sustainable e-commerce marketplace connecting eco-conscious consumers with green brands.',
            'industry': industries['E-commerce'],
            'location': 'Portland, OR',
            'employee_count': 38,
            'founded_year': 2021,
            'funding_amount': '$6M'
        },
        {
            'name': 'StreamVerse',
            'description': 'Virtual reality streaming platform for immersive entertainment experiences. The future of media consumption.',
            'industry': industries['Entertainment'],
            'location': 'Los Angeles, CA',
            'employee_count': 42,
            'founded_year': 2022,
            'funding_amount': '$25M',
            'is_featured': True
        },
        {
            'name': 'GreenTech Solutions',
            'description': 'Smart building technology for energy efficiency. Reducing carbon footprint one building at a time.',
            'industry': industries['Technology'],
            'location': 'Seattle, WA',
            'employee_count': 35,
            'founded_year': 2020,
            'funding_amount': '$10M'
        },
        {
            'name': 'MedBot Assistance',
            'description': 'AI-powered medical assistant for healthcare professionals. Streamlining diagnosis and treatment recommendations.',
            'industry': industries['Healthcare'],
            'location': 'San Diego, CA',
            'employee_count': 29,
            'founded_year': 2021,
            'funding_amount': '$7M'
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
    
    # Create job types if they don't exist
    job_types = {}
    for job_type_name in ['Full-time', 'Part-time', 'Contract', 'Internship']:
        job_type, created = JobType.objects.get_or_create(name=job_type_name)
        job_types[job_type_name] = job_type
    
    # Create diverse jobs
    jobs_data = [
        {
            'title': 'Senior AI Research Engineer',
            'description': 'Join our AI research team to develop cutting-edge neural interfaces. You will work on deep learning models for brain signal processing and contribute to groundbreaking medical technology.',
            'startup': startups[0],  # NeuroLink AI
            'job_type': job_types['Full-time'],
            'experience_level': 'senior',
            'location': 'San Francisco, CA',
            'salary_range': '$150,000 - $200,000',
            'is_remote': False,
            'posted_by': users[0],
            'company_email': 'careers@neurolinkai.com',
            'status': 'active',
            'is_active': True,
            'is_urgent': True
        },
        {
            'title': 'Healthcare Data Analyst',
            'description': 'Analyze healthcare data to identify trends and improve patient outcomes. Work with large datasets and create actionable insights for medical professionals.',
            'startup': startups[1],  # HealthFlow
            'job_type': job_types['Full-time'],
            'experience_level': 'mid',
            'location': 'Remote',
            'salary_range': '$80,000 - $110,000',
            'is_remote': True,
            'posted_by': users[2],
            'company_email': 'jobs@healthflow.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'Blockchain Security Engineer',
            'description': 'Secure our cryptocurrency platform against threats. Experience with smart contracts, cryptography, and security auditing required.',
            'startup': startups[2],  # CryptoSafe
            'job_type': job_types['Full-time'],
            'experience_level': 'senior',
            'location': 'Miami, FL',
            'salary_range': '$130,000 - $170,000',
            'is_remote': True,
            'posted_by': users[1],
            'company_email': 'security@cryptosafe.com',
            'status': 'active',
            'is_active': True,
            'is_urgent': True
        },
        {
            'title': 'Education Technology Designer',
            'description': 'Design engaging learning experiences for our adaptive platform. Create user interfaces that make learning fun and effective for students of all ages.',
            'startup': startups[3],  # LearnSphere
            'job_type': job_types['Full-time'],
            'experience_level': 'mid',
            'location': 'Chicago, IL',
            'salary_range': '$70,000 - $95,000',
            'is_remote': False,
            'posted_by': users[4],
            'company_email': 'design@learnsphere.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'Sustainability Product Manager',
            'description': 'Lead product development for our eco-friendly marketplace. Drive initiatives that make sustainable shopping easier and more accessible.',
            'startup': startups[4],  # EcoMarket
            'job_type': job_types['Full-time'],
            'experience_level': 'mid',
            'location': 'Portland, OR',
            'salary_range': '$90,000 - $120,000',
            'is_remote': True,
            'posted_by': users[1],
            'company_email': 'product@ecomarket.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'VR Content Developer',
            'description': 'Create immersive virtual reality experiences for our streaming platform. Experience with Unity, Unreal Engine, and 3D modeling preferred.',
            'startup': startups[5],  # StreamVerse
            'job_type': job_types['Contract'],
            'experience_level': 'mid',
            'location': 'Los Angeles, CA',
            'salary_range': '$60,000 - $80,000',
            'is_remote': False,
            'posted_by': users[3],
            'company_email': 'content@streamverse.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'IoT Software Engineer',
            'description': 'Develop software for smart building systems. Work with sensors, data processing, and cloud integration to create energy-efficient solutions.',
            'startup': startups[6],  # GreenTech
            'job_type': job_types['Full-time'],
            'experience_level': 'mid',
            'location': 'Seattle, WA',
            'salary_range': '$85,000 - $115,000',
            'is_remote': True,
            'posted_by': users[5],
            'company_email': 'engineering@greentech.com',
            'status': 'active',
            'is_active': True
        },
        {
            'title': 'Machine Learning Intern',
            'description': 'Join our ML team for a summer internship. Work on medical AI projects and gain hands-on experience with healthcare data.',
            'startup': startups[7],  # MedBot
            'job_type': job_types['Internship'],
            'experience_level': 'entry',
            'location': 'San Diego, CA',
            'salary_range': '$25 - $30 per hour',
            'is_remote': False,
            'posted_by': users[0],
            'company_email': 'internships@medbot.com',
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
    
    # Create diverse posts
    posts_data = [
        {
            'title': 'Breaking into AI/ML: My Journey from Bootcamp to Senior Engineer 🚀',
            'content': 'Three years ago, I was a complete beginner in machine learning. Today, I am leading AI research at a cutting-edge startup. Here is what I learned: 1) Start with fundamentals - math matters, 2) Build projects that solve real problems, 3) Contribute to open source, 4) Network genuinely with the community. The key is consistency over perfection. Every day, do something to move forward, even if it is just reading one paper or writing one line of code.',
            'author': users[0]
        },
        {
            'title': 'The Product Manager\'s Dilemma: Features vs. User Experience',
            'content': 'Every PM faces this challenge: stakeholders want more features, but users need better experience. After managing 15+ product launches, here is my framework: 1) Always start with user research, 2) Measure impact, not output, 3) Say no to good ideas that don\'t align with core value, 4) Design for your power users, but onboard for beginners. Remember, a product that tries to do everything usually does nothing well.',
            'author': users[1]
        },
        {
            'title': 'Why I Left Big Tech for a Healthcare Startup',
            'content': 'Two months ago, I left my comfortable job at a FAANG company to join a healthcare startup. Best decision ever. Here is why: 1) Impact is immediate and visible, 2) Every line of code can save lives, 3) Learning opportunities are endless, 4) Team dynamics are incredible. Yes, startups are risky, but the potential to change lives makes it worth it. If you are considering the jump, ask yourself: what legacy do you want to leave?',
            'author': users[2]
        },
        {
            'title': 'Frontend Performance Tips That Actually Matter in 2024',
            'content': 'After optimizing dozens of React apps, here are the techniques that provide the biggest impact: 1) Code splitting at the route level, 2) Lazy loading images with intersection observer, 3) Service workers for caching, 4) Bundle analysis to identify bloat, 5) CDN for static assets. Pro tip: measure before and after every optimization. Sometimes what you think is slow isn\'t the actual bottleneck.',
            'author': users[3]
        },
        {
            'title': 'Designing for Accessibility: It\'s Not Optional Anymore',
            'content': 'Accessibility isn\'t just about compliance - it\'s about creating products everyone can use. As designers, we have a responsibility to build inclusive experiences. Key principles: 1) Design with keyboard navigation in mind, 2) Ensure sufficient color contrast, 3) Write meaningful alt text, 4) Test with screen readers, 5) Include users with disabilities in your research. Remember, accessibility benefits everyone, not just people with disabilities.',
            'author': users[4]
        },
        {
            'title': 'Kubernetes in Production: Lessons from 3 Years of Scaling',
            'content': 'Running K8s in production taught me valuable lessons: 1) Start simple, complexity comes naturally, 2) Monitoring and observability are not optional, 3) Resource limits prevent one bad pod from killing everything, 4) Backup strategies are crucial, 5) Security should be built in from day one. Biggest mistake teams make? Trying to use every K8s feature from the start. Master the basics first.',
            'author': users[5]
        },
        {
            'title': 'The Future of Work: Remote, Hybrid, or Back to Office?',
            'content': 'Having worked in all three models, here are my thoughts: Remote works best for deep work and global talent access. Hybrid is great for collaboration and mentorship. Office is ideal for culture building and spontaneous innovation. The future isn\'t one-size-fits-all - it\'s about matching work style to work type. Companies that figure this out will have a massive talent advantage.',
            'author': users[1]
        },
        {
            'title': 'Building My First Chrome Extension: A Developer\'s Journey',
            'content': 'Just shipped my first Chrome extension! It took 3 weeks of evening coding, but the learning was incredible. Key takeaways: 1) The Chrome extension APIs are well-documented, 2) Content scripts have limited access for security, 3) Background scripts handle persistent tasks, 4) Users care more about utility than fancy UI. Already at 500+ users and growing. Sometimes the best way to learn is to just start building.',
            'author': users[3]
        },
        {
            'title': 'Data Science Ethics: Questions We Should All Be Asking',
            'content': 'As data scientists, we have unprecedented power to influence decisions. With great power comes great responsibility. Questions to ask: 1) Could this model perpetuate existing biases?, 2) Is the data collection transparent and consensual?, 3) How will this algorithm affect different communities?, 4) Can we explain the decision process?, 5) What are the potential misuse cases? Ethics isn\'t a checkbox - it\'s an ongoing conversation.',
            'author': users[2]
        },
        {
            'title': 'Startup Life: The Good, The Bad, and The Reality',
            'content': 'Six months into startup life, here is the unfiltered truth: The Good - incredible learning, direct impact, amazing teammates. The Bad - uncertainty, long hours, constant pressure. The Reality - it\'s not for everyone, and that\'s okay. Before joining a startup, ask yourself: Can you handle ambiguity? Do you thrive in chaos? Are you energized by building from scratch? If yes, you\'ll love it. If no, that\'s perfectly fine too.',
            'author': users[0]
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
            print(f"Created post: {post.title}")
        posts.append(post)
    
    print(f"\nDiverse sample data creation complete!")
    print(f"Added {len([u for u in users if User.objects.filter(username=u.username).exists()])} users")
    print(f"Added {len([s for s in startups if Startup.objects.filter(name=s.name).exists()])} startups") 
    print(f"Added {len([j for j in jobs if Job.objects.filter(title=j.title).exists()])} jobs")
    print(f"Added {len([p for p in posts if Post.objects.filter(title=p.title).exists()])} posts")

if __name__ == '__main__':
    add_diverse_sample_data()