"""
Comprehensive Metadata Generation Script for StartLinker Platform

This Django management command generates realistic test data including:
- 10 diverse users with complete profiles
- 100 startups across different industries
- 100 job postings from various startups
- 100 posts from the 10 users

Usage:
    python manage.py generate_metadata

This script creates realistic, diverse data to showcase the platform's features.
"""

import random
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
import uuid

# Import all necessary models
from apps.startups.models import Startup, Industry, UserProfile
from apps.jobs.models import Job, JobType
from apps.posts.models import Post

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate comprehensive metadata: 10 users, 100 startups, 100 jobs, 100 posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before generating new metadata',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write(self.style.WARNING('Cleaning existing data...'))
            self.clean_existing_data()

        try:
            self.stdout.write(self.style.SUCCESS('Starting comprehensive metadata generation...'))
            
            # Generate data in order (without transaction to prevent rollback on timeout)
            users = self.generate_users()
            startups = self.generate_startups()
            jobs = self.generate_jobs(startups)
            posts = self.generate_posts(users)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated:\n'
                    f'- {len(users)} users\n'
                    f'- {len(startups)} startups\n'
                    f'- {len(jobs)} jobs\n'
                    f'- {len(posts)} posts'
                )
            )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating metadata: {str(e)}'))
            raise CommandError(f'Metadata generation failed: {str(e)}')

    def clean_existing_data(self):
        """Clean existing test data"""
        Post.objects.filter(title__contains='[META]').delete()
        Job.objects.filter(title__contains='[META]').delete()
        Startup.objects.filter(name__contains='[META]').delete()
        User.objects.filter(username__startswith='meta_').delete()
        self.stdout.write(self.style.SUCCESS('Existing metadata cleaned.'))

    def generate_users(self):
        """Generate 10 diverse users with complete profiles"""
        self.stdout.write('Generating 10 diverse users...')
        
        users_data = [
            {
                'username': 'meta_sarah_c',
                'email': 'sarah.chen@example.com',
                'first_name': 'Sarah',
                'last_name': 'Chen',
                'bio': 'AI/ML Engineer passionate about developing intelligent solutions. Currently working on computer vision projects.',
                'location': 'San Francisco, CA',
                'experience_level': 'Senior',
                'skills': ['Python', 'TensorFlow', 'Computer Vision', 'Machine Learning', 'Deep Learning']
            },
            {
                'username': 'meta_rajesh_p',
                'email': 'rajesh.patel@example.com',
                'first_name': 'Rajesh',
                'last_name': 'Patel',
                'bio': 'Full-stack developer with expertise in React and Node.js. Building scalable web applications.',
                'location': 'Bangalore, India',
                'experience_level': 'Mid Level',
                'skills': ['React', 'Node.js', 'JavaScript', 'MongoDB', 'AWS']
            },
            {
                'username': 'meta_emily_j',
                'email': 'emily.johnson@example.com',
                'first_name': 'Emily',
                'last_name': 'Johnson',
                'bio': 'Product Manager focused on user experience and growth. Leading cross-functional teams to deliver innovative products.',
                'location': 'New York, NY',
                'experience_level': 'Senior',
                'skills': ['Product Management', 'User Research', 'Analytics', 'Agile', 'Leadership']
            },
            {
                'username': 'meta_carlos_r',
                'email': 'carlos.rodriguez@example.com',
                'first_name': 'Carlos',
                'last_name': 'Rodriguez',
                'bio': 'DevOps engineer specializing in cloud infrastructure and automation. Passionate about scalable systems.',
                'location': 'Austin, TX',
                'experience_level': 'Mid Level',
                'skills': ['Docker', 'Kubernetes', 'AWS', 'Terraform', 'CI/CD']
            },
            {
                'username': 'meta_aisha_w',
                'email': 'aisha.williams@example.com',
                'first_name': 'Aisha',
                'last_name': 'Williams',
                'bio': 'UX/UI Designer creating intuitive and accessible digital experiences. Advocate for inclusive design practices.',
                'location': 'Los Angeles, CA',
                'experience_level': 'Mid Level',
                'skills': ['UI/UX Design', 'Figma', 'User Research', 'Prototyping', 'Accessibility']
            },
            {
                'username': 'meta_david_k',
                'email': 'david.kim@example.com',
                'first_name': 'David',
                'last_name': 'Kim',
                'bio': 'Data scientist with experience in predictive analytics and business intelligence. Turning data into insights.',
                'location': 'Seattle, WA',
                'experience_level': 'Senior',
                'skills': ['Data Science', 'Python', 'SQL', 'Machine Learning', 'Tableau']
            },
            {
                'username': 'meta_nina_p',
                'email': 'nina.peterson@example.com',
                'first_name': 'Nina',
                'last_name': 'Peterson',
                'bio': 'Marketing specialist with focus on digital growth and customer acquisition. Building brands that matter.',
                'location': 'Chicago, IL',
                'experience_level': 'Mid Level',
                'skills': ['Digital Marketing', 'SEO', 'Content Strategy', 'Analytics', 'Social Media']
            },
            {
                'username': 'meta_alex_t',
                'email': 'alex.thompson@example.com',
                'first_name': 'Alex',
                'last_name': 'Thompson',
                'bio': 'Blockchain developer working on DeFi protocols and smart contracts. Exploring the future of finance.',
                'location': 'Miami, FL',
                'experience_level': 'Mid Level',
                'skills': ['Solidity', 'Web3', 'Smart Contracts', 'DeFi', 'Ethereum']
            },
            {
                'username': 'meta_priya_s',
                'email': 'priya.sharma@example.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'bio': 'Cybersecurity analyst protecting digital assets. Specialized in threat detection and incident response.',
                'location': 'Boston, MA',
                'experience_level': 'Mid Level',
                'skills': ['Cybersecurity', 'Penetration Testing', 'SIEM', 'Risk Assessment', 'Compliance']
            },
            {
                'username': 'meta_james_w',
                'email': 'james.wilson@example.com',
                'first_name': 'James',
                'last_name': 'Wilson',
                'bio': 'Mobile app developer creating cross-platform solutions. Passionate about mobile user experiences.',
                'location': 'Portland, OR',
                'experience_level': 'Senior',
                'skills': ['React Native', 'Flutter', 'iOS', 'Android', 'Mobile Development']
            }
        ]

        users = []
        for user_data in users_data:
            # Create user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password='testpass123'
            )
            
            # Update user profile fields
            user.bio = user_data['bio']
            user.location = user_data['location']
            user.save()
            
            # Create or update the UserProfile for premium status tracking
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            users.append(user)
            self.stdout.write(f'Created user: {user.username}')

        return users

    def generate_startups(self):
        """Generate 100 diverse startups across different industries"""
        self.stdout.write('Generating 100 startups...')
        
        # First, ensure industries exist
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
        ]
        
        industries = []
        for industry_data in industries_data:
            industry, created = Industry.objects.get_or_create(
                name=industry_data['name'],
                defaults={'icon': industry_data['icon']}
            )
            industries.append(industry)

        # Startup templates organized by industry
        startup_templates = {
            'Technology': [
                ('AI Vision Systems', 'Advanced computer vision solutions for autonomous vehicles and robotics'),
                ('CloudSync Pro', 'Enterprise cloud synchronization and backup solutions'),
                ('DevTools Plus', 'Next-generation development tools for modern software teams'),
                ('SecureNet Analytics', 'AI-powered cybersecurity threat detection and prevention'),
                ('DataFlow Solutions', 'Real-time data processing and analytics platform'),
                ('MobileFirst Labs', 'Cross-platform mobile application development framework'),
                ('QuantumCode', 'Quantum computing software development platform'),
                ('EdgeCompute Tech', 'Edge computing solutions for IoT and 5G networks'),
                ('BlockchainBridge', 'Interoperability solutions for blockchain networks'),
                ('NeuralNet Studios', 'Deep learning model development and deployment tools'),
            ],
            'Healthcare': [
                ('HealthTrack Digital', 'Personal health monitoring and analytics platform'),
                ('MedConnect Portal', 'Telemedicine and remote patient monitoring solutions'),
                ('BioData Analytics', 'Genomic data analysis and personalized medicine platform'),
                ('CareCoordinator', 'Healthcare workflow optimization and patient management'),
                ('TherapyBot AI', 'AI-assisted mental health therapy and support'),
                ('PharmTrack Systems', 'Pharmaceutical supply chain and inventory management'),
                ('VitalSigns Monitor', 'Wearable health monitoring and emergency response'),
                ('MedRecord Secure', 'Blockchain-based medical records management'),
                ('RehabTech Solutions', 'Virtual reality physical therapy and rehabilitation'),
                ('HealthInsights Pro', 'Population health analytics and disease prediction'),
            ],
            'Finance': [
                ('CryptoWallet Pro', 'Multi-currency cryptocurrency wallet and exchange'),
                ('InvestSmart AI', 'AI-powered investment advisory and portfolio management'),
                ('LendingBridge', 'P2P lending platform with smart contract integration'),
                ('PayFlow Systems', 'Digital payment processing for small businesses'),
                ('RiskAssess Analytics', 'Financial risk assessment and fraud detection'),
                ('TradingDesk Elite', 'Professional trading platform with advanced analytics'),
                ('CreditScore Plus', 'Alternative credit scoring using machine learning'),
                ('InsureTech Solutions', 'Digital insurance platform and claims processing'),
                ('WealthManage Pro', 'Automated wealth management and financial planning'),
                ('RegTech Compliance', 'Regulatory compliance automation for financial institutions'),
            ],
            'Education': [
                ('LearnFlow Academy', 'Personalized online learning platform with AI tutoring'),
                ('SkillBridge Connect', 'Professional skill development and certification platform'),
                ('EduAnalytics Pro', 'Student performance analytics and learning optimization'),
                ('VirtualLab Systems', 'Virtual laboratory experiments for STEM education'),
                ('LanguageAI Tutor', 'AI-powered language learning and conversation practice'),
                ('CampusConnect Hub', 'University campus management and student services'),
                ('MicroLearn Platform', 'Bite-sized learning modules for busy professionals'),
                ('TeacherTools Suite', 'Digital classroom management and assessment tools'),
                ('StudyBuddy Network', 'Peer-to-peer study groups and collaboration platform'),
                ('EduVR Experiences', 'Virtual reality educational content and experiences'),
            ],
            'E-commerce': [
                ('ShopSmart AI', 'AI-powered personalized shopping recommendations'),
                ('LogisticsFlow Pro', 'End-to-end e-commerce fulfillment and logistics'),
                ('MarketPlace Builder', 'Multi-vendor marketplace creation and management'),
                ('CustomerInsights Hub', 'E-commerce customer behavior analytics and insights'),
                ('InventoryMaster', 'Automated inventory management and demand forecasting'),
                ('PaymentGateway Plus', 'Secure payment processing with fraud protection'),
                ('RetailAnalytics Pro', 'Retail performance analytics and business intelligence'),
                ('SocialCommerce', 'Social media integration for e-commerce platforms'),
                ('SupplyChain Optimizer', 'AI-optimized supply chain management'),
                ('ConversionBoost', 'E-commerce conversion rate optimization tools'),
            ],
            'Entertainment': [
                ('StreamTech Studios', 'Live streaming platform with interactive features'),
                ('GameDev Engine', 'Cross-platform game development framework'),
                ('ContentCreator Hub', 'Tools and platform for digital content creators'),
                ('VirtualEvents Pro', 'Virtual event hosting and audience engagement'),
                ('MusicStream Analytics', 'Music streaming analytics and artist insights'),
                ('VideoEdit AI', 'AI-powered video editing and content optimization'),
                ('PodcastPlatform Plus', 'Podcast hosting, distribution, and monetization'),
                ('ARExperience Studio', 'Augmented reality content creation platform'),
                ('SportsAnalytics Pro', 'Advanced sports performance analytics and insights'),
                ('DigitalCinema Tech', 'Digital cinema production and distribution tools'),
            ],
            'Transportation': [
                ('RideShare Optimizer', 'AI-optimized ride-sharing and fleet management'),
                ('LogisticTrack Pro', 'Real-time logistics tracking and route optimization'),
                ('AutonomousFleet', 'Autonomous vehicle fleet management platform'),
                ('ParkingSmart Solutions', 'Smart parking management and reservation system'),
                ('DeliveryDrone Network', 'Drone delivery network and management platform'),
                ('PublicTransit Hub', 'Smart public transportation management system'),
                ('CarShare Connect', 'Peer-to-peer car sharing platform'),
                ('FreightOptimizer', 'Freight logistics optimization and matching'),
                ('MobilityInsights', 'Urban mobility analytics and planning tools'),
                ('BikeShare Systems', 'Smart bike sharing network management'),
            ],
            'Food & Beverage': [
                ('FoodDelivery Express', 'Hyper-local food delivery and ghost kitchen platform'),
                ('NutriTrack AI', 'AI-powered nutrition tracking and meal planning'),
                ('RestaurantTech Hub', 'Restaurant management and ordering system'),
                ('FarmToTable Connect', 'Direct connection between farms and consumers'),
                ('FoodSafety Monitor', 'Food safety tracking and compliance management'),
                ('RecipeShare Community', 'Social recipe sharing and cooking platform'),
                ('MealPrep Solutions', 'Automated meal preparation and subscription service'),
                ('BeverageCraft Analytics', 'Craft beverage production and quality analytics'),
                ('KitchenBot Systems', 'Automated kitchen equipment and food preparation'),
                ('DietaryMatch Platform', 'Dietary restriction matching for restaurants'),
            ],
            'Real Estate': [
                ('PropertyTech Solutions', 'Digital property management and tenant services'),
                ('RealEstate Analytics', 'Market analysis and property valuation platform'),
                ('VirtualTour Studio', 'Virtual reality property tours and showcases'),
                ('InvestmentProperty Hub', 'Real estate investment analysis and marketplace'),
                ('SmartBuilding Systems', 'IoT-enabled building automation and management'),
                ('RentalMatch Platform', 'AI-powered rental property matching service'),
                ('ConstructionTech Pro', 'Construction project management and analytics'),
                ('PropertyInsights AI', 'Predictive analytics for real estate markets'),
                ('HomeBuyer Assistant', 'AI-powered home buying guidance and support'),
                ('CommercialSpace Hub', 'Commercial real estate leasing and management'),
            ],
            'Energy': [
                ('SolarTech Optimizer', 'Solar panel efficiency monitoring and optimization'),
                ('EnergyGrid Analytics', 'Smart grid management and energy distribution'),
                ('GreenEnergy Marketplace', 'Renewable energy trading and marketplace'),
                ('BatteryTech Solutions', 'Advanced battery management and storage systems'),
                ('EnergyEfficiency Hub', 'Building energy efficiency monitoring and optimization'),
                ('WindPower Analytics', 'Wind energy production forecasting and optimization'),
                ('SmartMeter Systems', 'IoT-enabled energy consumption monitoring'),
                ('CarbonTrack Platform', 'Carbon footprint tracking and offset marketplace'),
                ('EnergyStorage Pro', 'Grid-scale energy storage management platform'),
                ('CleanTech Innovation', 'Clean technology development and deployment'),
            ]
        }

        locations = [
            'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA', 'Boston, MA',
            'Los Angeles, CA', 'Chicago, IL', 'Denver, CO', 'Miami, FL', 'Portland, OR',
            'Atlanta, GA', 'Dallas, TX', 'Phoenix, AZ', 'San Diego, CA', 'Nashville, TN'
        ]

        funding_amounts = [
            '$100K', '$250K', '$500K', '$1M', '$2.5M', '$5M', '$10M', '$25M', '$50M'
        ]

        startups = []
        startup_count = 0
        
        for industry in industries:
            industry_templates = startup_templates.get(industry.name, [])
            for name_template, description_template in industry_templates:
                if startup_count >= 100:
                    break
                    
                startup = Startup.objects.create(
                    name=f'[META] {name_template}',
                    description=description_template,
                    industry=industry,
                    location=random.choice(locations),
                    employee_count=random.randint(5, 500),
                    founded_year=random.randint(2018, 2024),
                    funding_amount=random.choice(funding_amounts) if random.random() > 0.3 else 'Bootstrapped',
                    is_featured=random.random() > 0.85,
                    website=f'https://{name_template.lower().replace(" ", "")}.com'
                )
                
                startups.append(startup)
                startup_count += 1
                
                if startup_count % 10 == 0:
                    self.stdout.write(f'Created {startup_count} startups...')
                    
            if startup_count >= 100:
                break

        self.stdout.write(f'Generated {len(startups)} startups')
        return startups

    def generate_jobs(self, startups):
        """Generate 100 job postings from various startups"""
        self.stdout.write('Generating 100 jobs...')
        
        # Get the generated users for job posting
        generated_users = User.objects.filter(username__startswith='meta_')
        
        # Ensure job types and experience levels exist
        job_types_data = [
            'Full-time', 'Part-time', 'Contract', 'Internship', 'Remote'
        ]
        
        experience_levels_data = [
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'), 
            ('senior', 'Senior Level'),
            ('lead', 'Lead/Principal')
        ]
        
        job_types = []
        for job_type_name in job_types_data:
            job_type, created = JobType.objects.get_or_create(name=job_type_name)
            job_types.append(job_type)

        job_templates = [
            ('Senior Software Engineer', 'Lead development of scalable web applications using modern technologies. Experience with React, Node.js, and cloud platforms required.'),
            ('Product Manager', 'Drive product strategy and roadmap. Work with engineering, design, and marketing teams to deliver exceptional user experiences.'),
            ('Data Scientist', 'Analyze complex datasets to drive business insights. Experience with Python, SQL, and machine learning frameworks required.'),
            ('UX/UI Designer', 'Create intuitive and beautiful user interfaces. Proficiency in Figma, user research, and design systems required.'),
            ('DevOps Engineer', 'Build and maintain CI/CD pipelines. Experience with Docker, Kubernetes, and cloud platforms required.'),
            ('Marketing Specialist', 'Develop and execute marketing campaigns. Experience with digital marketing, analytics, and content creation.'),
            ('Frontend Developer', 'Build responsive web applications using React and modern JavaScript. Strong CSS and HTML skills required.'),
            ('Backend Developer', 'Develop robust APIs and services. Experience with Node.js, Python, or Java and database design.'),
            ('Mobile Developer', 'Create native or cross-platform mobile applications. Experience with React Native or Flutter preferred.'),
            ('Sales Manager', 'Drive revenue growth through strategic sales initiatives. Experience in B2B sales and relationship building.'),
            ('Customer Success Manager', 'Ensure customer satisfaction and retention. Experience with SaaS products and customer relationship management.'),
            ('Security Engineer', 'Implement and maintain security protocols. Experience with penetration testing and security frameworks.'),
            ('AI/ML Engineer', 'Develop machine learning models and AI solutions. Experience with TensorFlow, PyTorch, and data pipelines.'),
            ('Quality Assurance Engineer', 'Ensure software quality through testing and automation. Experience with testing frameworks and CI/CD.'),
            ('Business Analyst', 'Analyze business processes and requirements. Experience with data analysis and stakeholder management.'),
            ('Technical Writer', 'Create clear technical documentation. Experience with API documentation and developer tools.'),
            ('HR Generalist', 'Support all aspects of human resources. Experience with recruiting, employee relations, and compliance.'),
            ('Financial Analyst', 'Perform financial analysis and modeling. Experience with Excel, financial reporting, and budgeting.'),
            ('Operations Manager', 'Optimize business operations and processes. Experience with project management and process improvement.'),
            ('Content Marketing Manager', 'Develop content strategy and create engaging content. Experience with SEO, social media, and analytics.'),
        ]

        skills_by_role = {
            'Engineer': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Git'],
            'Manager': ['Leadership', 'Project Management', 'Strategy', 'Communication', 'Analytics'],
            'Designer': ['Figma', 'Sketch', 'UI/UX', 'Prototyping', 'User Research', 'Design Systems'],
            'Analyst': ['SQL', 'Python', 'Excel', 'Analytics', 'Data Visualization', 'Statistics'],
            'Marketing': ['SEO', 'Content Marketing', 'Social Media', 'Analytics', 'Campaign Management'],
        }

        salary_ranges = [
            '$60,000 - $80,000', '$70,000 - $90,000', '$80,000 - $100,000', '$90,000 - $120,000',
            '$100,000 - $130,000', '$120,000 - $150,000', '$130,000 - $160,000', '$150,000 - $200,000'
        ]

        jobs = []
        for i in range(100):
            title, description = random.choice(job_templates)
            startup = random.choice(startups)
            
            # Determine skills based on role type
            role_type = 'Engineer' if 'Engineer' in title or 'Developer' in title else \
                       'Manager' if 'Manager' in title else \
                       'Designer' if 'Designer' in title else \
                       'Analyst' if 'Analyst' in title else \
                       'Marketing' if 'Marketing' in title else 'Engineer'
                       
            job_skills = random.sample(skills_by_role[role_type], k=random.randint(3, 5))
            
            # Choose a random user to post the job
            posting_user = random.choice(generated_users)
            
            job = Job.objects.create(
                title=f'[META] {title}',
                description=f'{description}\n\nWe are looking for a talented professional to join our growing team at {startup.name}. This is an excellent opportunity to work with cutting-edge technology and make a real impact.',
                startup=startup,
                job_type=random.choice(job_types),
                experience_level=random.choice([choice[0] for choice in experience_levels_data]),
                location=startup.location if random.random() > 0.3 else 'Remote',
                salary_range=random.choice(salary_ranges),
                is_remote=random.random() > 0.4,
                is_urgent=random.random() > 0.8,
                application_deadline=timezone.now() + datetime.timedelta(days=random.randint(30, 90)),
                posted_at=timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
                posted_by=posting_user,
                company_email=f'hr@{startup.name.lower().replace(" ", "").replace("[META]", "").strip()}.com',
                status='active',
                is_active=True
            )
            
            jobs.append(job)
            
            if (i + 1) % 20 == 0:
                self.stdout.write(f'Created {i + 1} jobs...')

        self.stdout.write(f'Generated {len(jobs)} jobs')
        return jobs

    def generate_posts(self, users):
        """Generate 100 posts from the 10 users"""
        self.stdout.write('Generating 100 posts...')
        
        post_templates = [
            # Tech & Development
            ('Just shipped a major feature update! 🚀', 'After weeks of development, we finally released our new AI-powered analytics dashboard. The team worked incredibly hard to make this happen. #tech #ai #development'),
            ('Debugging session turned into a learning marathon', 'Spent 6 hours tracking down a memory leak, but learned so much about performance optimization in the process. Sometimes the best learning comes from the toughest problems. #debugging #learning #coding'),
            ('Open source contribution feels amazing!', 'Just had my first PR merged into a major open source project. Contributing back to the community that has given me so much. #opensource #coding #community'),
            
            # Career & Growth
            ('Celebrating a career milestone today! 🎉', 'Just got promoted to Senior Developer after 3 years of hard work. Grateful for all the mentors and teammates who supported my journey. #career #growth #grateful'),
            ('The importance of continuous learning', 'Started learning a new framework this week. Staying curious and adapting to new technologies is what keeps this field exciting. #learning #technology #growth'),
            ('Networking tip that actually works', 'The best networking happens when you focus on helping others first. Be genuinely interested in people and their projects. #networking #career #advice'),
            
            # Industry Insights
            ('The future of remote work is here', 'After 2 years of fully remote work, I can confidently say it has made me more productive and balanced. The key is setting clear boundaries. #remotework #productivity #worklife'),
            ('AI is transforming how we work', 'Seeing AI tools accelerate development workflows is incredible. But human creativity and problem-solving remain irreplaceable. #ai #future #technology'),
            ('Diversity in tech matters more than ever', 'Working in diverse teams has consistently led to better products and innovative solutions. We need to keep pushing for inclusive workplaces. #diversity #inclusion #tech'),
            
            # Project Showcases
            ('Weekend project turned into something special', 'Built a small tool to help track my daily habits. Sometimes side projects become the most rewarding work. Code is on GitHub! #sideproject #coding #habits'),
            ('Demo day was a huge success! 🎯', 'Presented our startup idea to investors today. The feedback was incredible and we are excited about the next steps. #startup #demo #entrepreneurship'),
            ('Launching our beta version next week', 'Months of development and testing are finally paying off. Beta users, get ready for something amazing! #product #launch #beta'),
            
            # Learning & Education
            ('Attended an amazing tech conference today', 'The keynote on quantum computing blew my mind. Also made some great connections with fellow developers. #conference #learning #networking'),
            ('Mentorship moments that matter', 'Had a great mentoring session with a junior developer today. Teaching others always helps me learn too. #mentorship #teaching #growth'),
            ('Book recommendation for developers', 'Just finished reading "Clean Code" - a must-read for any serious developer. The principles in this book will change how you write code. #books #coding #learning'),
            
            # Challenges & Solutions
            ('When imposter syndrome hits hard', 'Had one of those days where I questioned everything. But talking to my team reminded me that we all feel this way sometimes. You belong here. #impostersyndrome #mentalhealth #support'),
            ('Problem-solving breakthrough moment', 'Stared at this algorithm problem for hours, then the solution clicked during my morning walk. Sometimes stepping away is the best debugging tool. #problemsolving #algorithms #breakthrough'),
            ('Code review feedback that changed everything', 'A senior dev provided feedback that completely shifted my approach to architecture. Grateful for teams that prioritize learning and growth. #codereview #feedback #learning'),
            
            # Community & Culture
            ('Hackathon weekend was incredible! 💡', 'Built a prototype in 48 hours with an amazing team. Win or lose, the experience and friendships made it worthwhile. #hackathon #teamwork #innovation'),
            ('The power of tech communities', 'Local developer meetup tonight was inspiring. Nothing beats face-to-face conversations about code and ideas. #community #meetup #developers'),
            ('Giving back through tech education', 'Volunteered to teach coding to high school students today. Their enthusiasm and quick learning reminded me why I love this field. #education #volunteer #coding'),
        ]
        
        posts = []
        post_count = 0
        
        for i in range(100):
            user = random.choice(users)
            title, content = random.choice(post_templates)
            
            # Add some variety to posts
            if random.random() > 0.7:  # 30% chance of longer posts
                content += f"\n\nWhat are your thoughts on this? I'd love to hear different perspectives from the community. Always learning from others' experiences!"
            
            post = Post.objects.create(
                title=f'[META] {title}',
                content=content,
                author=user,
                created_at=timezone.now() - datetime.timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            )
            
            posts.append(post)
            post_count += 1
            
            if post_count % 20 == 0:
                self.stdout.write(f'Created {post_count} posts...')

        self.stdout.write(f'Generated {len(posts)} posts')
        return posts