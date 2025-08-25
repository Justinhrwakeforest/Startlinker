#!/usr/bin/env python3
"""
Complete Remaining Data: Finish the 100 jobs and 100 posts
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
from apps.startups.models import Startup
from apps.jobs.models import Job, JobType
from apps.posts.models import Post

User = get_user_model()

def complete_remaining_data():
    print("Completing remaining data to reach exact targets...")
    
    # Get meta users
    meta_users = list(User.objects.filter(username__in=[
        'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
        'alex_frontend', 'diana_ux', 'carlos_devops',
        'emma_backend', 'david_mobile', 'sofia_security', 'james_qa'
    ]))
    
    print(f"Using {len(meta_users)} meta users for content creation")
    
    # Complete jobs to 100
    current_jobs = Job.objects.count()
    print(f"\n=== COMPLETING JOBS ({current_jobs}/100) ===")
    
    if current_jobs < 100:
        jobs_needed = 100 - current_jobs
        print(f"Need {jobs_needed} more jobs")
        
        job_types = list(JobType.objects.all())
        all_startups = list(Startup.objects.all())
        
        job_titles = [
            'Junior Software Developer', 'Senior Backend Engineer', 'Technical Lead',
            'Frontend Specialist', 'React Developer', 'Vue.js Developer',
            'Product Marketing Manager', 'Growth Product Manager', 'Technical Product Manager',
            'Senior Data Scientist', 'ML Operations Engineer', 'Analytics Engineer',
            'Cloud Infrastructure Engineer', 'Platform Engineer', 'Release Engineer',
            'Senior UX Researcher', 'Visual Designer', 'Design Systems Engineer',
            'Performance Marketing Manager', 'SEO Specialist', 'Social Media Manager',
            'Enterprise Sales Representative', 'Strategic Account Manager', 'Sales Engineer',
            'Customer Experience Manager', 'Technical Account Manager', 'Implementation Specialist',
            'Information Security Analyst', 'Compliance Engineer', 'Security Architect',
            'React Native Developer', 'Swift Developer', 'Kotlin Developer',
            'Computer Vision Engineer', 'NLP Engineer', 'Robotics Engineer',
            'Senior Test Engineer', 'Performance Test Engineer', 'Security Test Engineer',
            'Technical Program Manager', 'Engineering Manager', 'Agile Coach',
            'Corporate Development Manager', 'People Operations Specialist', 'Facilities Manager'
        ]
        
        experience_levels = ['entry', 'mid', 'senior', 'lead']
        salary_ranges = [
            '$45,000 - $65,000', '$55,000 - $75,000', '$65,000 - $85,000', '$75,000 - $95,000',
            '$85,000 - $105,000', '$95,000 - $125,000', '$105,000 - $135,000', '$125,000 - $155,000',
            '$135,000 - $170,000', '$155,000 - $210,000', '$35 - $55 per hour', '$55 - $85 per hour'
        ]
        
        for i in range(jobs_needed):
            title = random.choice(job_titles)
            startup = random.choice(all_startups)
            posting_user = random.choice(meta_users)
            
            Job.objects.create(
                title=title,
                description=f"We're seeking a {title} to join {startup.name}. You'll work on innovative projects in {startup.industry.name.lower()} and help drive our mission forward. Great opportunity for growth in a dynamic environment.",
                startup=startup,
                job_type=random.choice(job_types),
                experience_level=random.choice(experience_levels),
                location=startup.location if random.random() > 0.4 else 'Remote',
                salary_range=random.choice(salary_ranges),
                is_remote=random.random() > 0.5,
                is_urgent=random.random() > 0.85,
                application_deadline=timezone.now() + timedelta(days=random.randint(20, 80)),
                posted_at=timezone.now() - timedelta(days=random.randint(1, 25)),
                posted_by=posting_user,
                company_email=f'careers@{startup.name.lower().replace(" ", "")}.com',
                status='active',
                is_active=True
            )
            
            if (i + 1) % 10 == 0:
                print(f"Added {i + 1} jobs...")
        
        print(f"Total jobs now: {Job.objects.count()}")
    
    # Complete posts to 100
    current_posts = Post.objects.count()
    print(f"\n=== COMPLETING POSTS ({current_posts}/100) ===")
    
    if current_posts < 100:
        posts_needed = 100 - current_posts
        print(f"Need {posts_needed} more posts")
        
        # Extended post templates
        post_templates = [
            ("Tech stack decisions that changed everything", "Choosing the right technology stack can make or break a project. Here's how we evaluated and selected our current architecture."),
            ("Incident response lessons learned", "Last week's production incident taught us valuable lessons about monitoring, alerting, and crisis communication."),
            ("The art of technical writing", "Clear technical documentation is a superpower. Here are the principles that have improved our team's communication."),
            ("Performance optimization deep dive", "Shaving 2 seconds off our page load time resulted in 15% higher conversion rates. Here's what we optimized."),
            ("Building a culture of code quality", "Code quality isn't just about following rules - it's about creating sustainable, maintainable systems."),
            ("The evolution of our deployment pipeline", "From manual deployments to fully automated CI/CD - here's how we transformed our release process."),
            ("Data-driven product development", "Using analytics and user feedback to guide feature development has dramatically improved our success rate."),
            ("Scaling team communication", "As we grew from 5 to 50 engineers, our communication patterns had to evolve. Here's what worked and what didn't."),
            ("The importance of developer experience", "Investing in developer productivity tools and workflows has been our best decision for team happiness and velocity."),
            ("Learning from failure", "Our biggest product flop taught us more than any success. Sometimes you have to fail fast and fail forward."),
            ("The future of remote collaboration", "Distributed teams are here to stay. These tools and practices have made our remote collaboration more effective than in-person."),
            ("Breaking down technical debt", "Technical debt is inevitable, but how you manage it determines your long-term success. Here's our approach."),
            ("User research that changed our roadmap", "One week of user interviews completely shifted our product priorities. Customer feedback is invaluable."),
            ("Building accessible applications", "Accessibility isn't optional - it's a fundamental requirement. Here's how we built accessibility into our development process."),
            ("The psychology of code reviews", "Good code reviews require both technical skill and emotional intelligence. Creating a positive review culture is crucial."),
            ("Monitoring and observability best practices", "You can't improve what you don't measure. Building comprehensive monitoring changed how we operate."),
            ("Cross-functional collaboration wins", "Breaking down silos between engineering, design, and product has accelerated our delivery and improved quality."),
            ("The hidden costs of technical shortcuts", "That quick hack from last quarter is now costing us weeks of refactoring. Sometimes slow is fast."),
            ("Building for international markets", "Expanding globally taught us about localization, performance across regions, and cultural considerations in product design."),
            ("The impact of pair programming", "Pair programming felt slow at first, but the knowledge sharing and code quality improvements have been worth it."),
            ("Database design principles", "Good database design is the foundation of scalable applications. These principles have served us well."),
            ("API versioning strategies", "Breaking changes are inevitable, but how you handle them determines customer satisfaction and developer adoption."),
            ("The journey to microservices", "Moving from monolith to microservices was challenging but ultimately improved our team autonomy and system resilience."),
            ("Security by design", "Security can't be bolted on later - it needs to be considered from the first line of code."),
            ("The value of hackathons", "Internal hackathons have produced some of our best features and strongest team bonds. Innovation needs dedicated time."),
            ("Building a learning culture", "Encouraging experimentation and learning from mistakes has made our team more innovative and resilient."),
            ("The science of A/B testing", "Proper experimental design and statistical analysis have prevented us from making costly product mistakes."),
            ("Optimizing for mobile performance", "Mobile users expect fast, smooth experiences. Here's how we optimized our app for performance across devices."),
            ("The art of saying no", "Product management is as much about what you don't build as what you do. Learning to prioritize ruthlessly is essential."),
            ("Building developer communities", "Open sourcing our tools and engaging with the developer community has brought unexpected benefits and partnerships."),
        ]
        
        # Shuffle to get variety
        available_templates = post_templates * 3  # Multiply to have enough variety
        random.shuffle(available_templates)
        
        for i in range(posts_needed):
            title_template, content_template = available_templates[i % len(available_templates)]
            author = random.choice(meta_users)
            
            # Add some variation
            variations = [
                " What's been your experience?",
                " I'd love to hear different perspectives.",
                " Anyone else faced similar challenges?",
                " The community's insights are always valuable.",
                " Learning from each other's experiences.",
                " What would you have done differently?",
                " Curious about your team's approach.",
                " These lessons took time to learn.",
                " Hope this helps others avoid similar pitfalls.",
                " The journey continues!"
            ]
            
            if random.random() > 0.3:
                content_template += random.choice(variations)
            
            Post.objects.create(
                title=title_template,
                content=content_template,
                author=author,
                created_at=timezone.now() - timedelta(
                    days=random.randint(1, 45),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            )
            
            if (i + 1) % 15 == 0:
                print(f"Added {i + 1} posts...")
        
        print(f"Total posts now: {Post.objects.count()}")
    
    # Final verification
    print(f"\n=== FINAL VERIFICATION ===")
    total_users = User.objects.count()
    meta_user_count = User.objects.filter(username__in=[
        'sarah_ai_dev', 'miguel_product', 'priya_data_sci', 
        'alex_frontend', 'diana_ux', 'carlos_devops',
        'emma_backend', 'david_mobile', 'sofia_security', 'james_qa'
    ]).count()
    
    print(f"✅ Meta Users: {meta_user_count}/10")
    print(f"✅ Total Users: {total_users}")
    print(f"✅ Startups: {Startup.objects.count()}/100")
    print(f"✅ Jobs: {Job.objects.count()}/100") 
    print(f"✅ Posts: {Post.objects.count()}/100")
    
    if (Startup.objects.count() >= 100 and 
        Job.objects.count() >= 100 and 
        Post.objects.count() >= 100 and 
        meta_user_count >= 10):
        print("\n🎉 SUCCESS: All targets reached!")
    else:
        print(f"\n⚠️ Still need to reach targets")

if __name__ == '__main__':
    complete_remaining_data()