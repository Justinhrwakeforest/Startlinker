# apps/core/management/commands/load_social_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
import random
import json

from apps.users.social_models import (
    UserFollow, Story, StartupCollaboration, CollaborationItem,
    Achievement, UserAchievement, ScheduledPost
)
from apps.startups.models import Startup
from apps.posts.models import Post

User = get_user_model()

class Command(BaseCommand):
    help = 'Load sample data for social features (Collaborations, Achievements, Scheduler)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading sample social features data...')
        
        # Get or create sample users
        self.users = self.get_or_create_users()
        
        # Get existing startups
        self.startups = list(Startup.objects.all()[:20])
        
        if not self.startups:
            self.stdout.write(self.style.WARNING('No startups found. Please load startup data first.'))
            return
        
        # Load data
        self.create_achievements()
        self.create_collaborations()
        self.create_scheduled_posts()
        self.create_user_follows()
        self.create_stories()
        self.assign_achievements_to_users()
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded social features sample data!'))

    def get_or_create_users(self):
        """Get existing users or create sample ones"""
        users = list(User.objects.all()[:10])
        
        if len(users) < 5:
            # Create some sample users if needed
            sample_users = [
                {'username': 'sarah_chen', 'first_name': 'Sarah', 'last_name': 'Chen', 'email': 'sarah@example.com'},
                {'username': 'alex_kumar', 'first_name': 'Alex', 'last_name': 'Kumar', 'email': 'alex@example.com'},
                {'username': 'maria_garcia', 'first_name': 'Maria', 'last_name': 'Garcia', 'email': 'maria@example.com'},
                {'username': 'james_wilson', 'first_name': 'James', 'last_name': 'Wilson', 'email': 'james@example.com'},
                {'username': 'priya_patel', 'first_name': 'Priya', 'last_name': 'Patel', 'email': 'priya@example.com'},
            ]
            
            for user_data in sample_users:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'is_active': True,
                    }
                )
                if created:
                    user.set_password('password123')
                    user.save()
                    users.append(user)
                    self.stdout.write(f'Created user: {user.username}')
        
        return users

    def create_achievements(self):
        """Create sample achievements"""
        self.stdout.write('Creating achievements...')
        
        achievements_data = [
            # Profile Achievements
            {
                'name': 'First Steps',
                'slug': 'first-steps',
                'description': 'Complete your basic profile information',
                'category': 'profile',
                'rarity': 'common',
                'icon': '👤',
                'color': '#6B7280',
                'points': 10,
                'badge_text': 'Newcomer',
                'requirements': {'profile_fields': ['first_name', 'last_name', 'bio']},
            },
            {
                'name': 'Profile Pro',
                'slug': 'profile-pro',
                'description': 'Complete all profile sections including avatar and background',
                'category': 'profile',
                'rarity': 'uncommon',
                'icon': '⭐',
                'color': '#10B981',
                'points': 25,
                'requirements': {'profile_completion': 100},
            },
            
            # Social Achievements
            {
                'name': 'Social Butterfly',
                'slug': 'social-butterfly',
                'description': 'Follow 50 users and build your network',
                'category': 'social',
                'rarity': 'uncommon',
                'icon': '🦋',
                'color': '#10B981',
                'points': 30,
                'requirements': {'following_count': 50},
            },
            {
                'name': 'Influencer',
                'slug': 'influencer',
                'description': 'Gain 100 followers',
                'category': 'social',
                'rarity': 'rare',
                'icon': '📢',
                'color': '#3B82F6',
                'points': 50,
                'requirements': {'followers_count': 100},
            },
            
            # Content Achievements
            {
                'name': 'First Post',
                'slug': 'first-post',
                'description': 'Create your first post',
                'category': 'content',
                'rarity': 'common',
                'icon': '📝',
                'color': '#6B7280',
                'points': 10,
                'requirements': {'posts_count': 1},
            },
            {
                'name': 'Content Creator',
                'slug': 'content-creator',
                'description': 'Create 50 posts and share your knowledge',
                'category': 'content',
                'rarity': 'rare',
                'icon': '✍️',
                'color': '#3B82F6',
                'points': 75,
                'requirements': {'posts_count': 50},
            },
            {
                'name': 'Curator',
                'slug': 'curator',
                'description': 'Create 5 collaborations with at least 10 startups each',
                'category': 'content',
                'rarity': 'rare',
                'icon': '🗂️',
                'color': '#3B82F6',
                'points': 60,
                'requirements': {'collaborations_count': 5, 'min_items_per_collaboration': 10},
            },
            
            # Networking Achievements
            {
                'name': 'Connector',
                'slug': 'connector',
                'description': 'Send 100 messages and build relationships',
                'category': 'networking',
                'rarity': 'uncommon',
                'icon': '🤝',
                'color': '#10B981',
                'points': 40,
                'requirements': {'messages_sent': 100},
            },
            {
                'name': 'Community Builder',
                'slug': 'community-builder',
                'description': 'Create a collaboration with 50+ followers',
                'category': 'networking',
                'rarity': 'epic',
                'icon': '🏛️',
                'color': '#8B5CF6',
                'points': 100,
                'requirements': {'collaboration_followers': 50},
            },
            
            # Startup Achievements
            {
                'name': 'Startup Founder',
                'slug': 'startup-founder',
                'description': 'List your first startup',
                'category': 'startup',
                'rarity': 'common',
                'icon': '🚀',
                'color': '#6B7280',
                'points': 20,
                'requirements': {'startups_created': 1},
            },
            {
                'name': 'Serial Entrepreneur',
                'slug': 'serial-entrepreneur',
                'description': 'List 5 startups',
                'category': 'startup',
                'rarity': 'epic',
                'icon': '💼',
                'color': '#8B5CF6',
                'points': 150,
                'requirements': {'startups_created': 5},
            },
            
            # Jobs Achievements
            {
                'name': 'Job Creator',
                'slug': 'job-creator',
                'description': 'Post your first job listing',
                'category': 'jobs',
                'rarity': 'common',
                'icon': '💼',
                'color': '#6B7280',
                'points': 15,
                'requirements': {'jobs_posted': 1},
            },
            {
                'name': 'Hiring Manager',
                'slug': 'hiring-manager',
                'description': 'Post 25 job listings',
                'category': 'jobs',
                'rarity': 'rare',
                'icon': '👔',
                'color': '#3B82F6',
                'points': 80,
                'requirements': {'jobs_posted': 25},
            },
            
            # Special Achievements
            {
                'name': 'Early Adopter',
                'slug': 'early-adopter',
                'description': 'Among the first 1000 users to join',
                'category': 'special',
                'rarity': 'legendary',
                'icon': '🌟',
                'color': '#F59E0B',
                'points': 500,
                'badge_text': 'Pioneer',
                'requirements': {'user_id_max': 1000},
                'is_secret': True,
            },
            {
                'name': 'Night Owl',
                'slug': 'night-owl',
                'description': 'Post 10 times between midnight and 5 AM',
                'category': 'special',
                'rarity': 'uncommon',
                'icon': '🦉',
                'color': '#10B981',
                'points': 35,
                'requirements': {'night_posts': 10},
                'is_secret': True,
            },
            {
                'name': 'Scheduler Master',
                'slug': 'scheduler-master',
                'description': 'Successfully schedule and publish 20 posts',
                'category': 'content',
                'rarity': 'uncommon',
                'icon': '📅',
                'color': '#10B981',
                'points': 45,
                'requirements': {'scheduled_posts_published': 20},
            },
        ]
        
        for achievement_data in achievements_data:
            achievement, created = Achievement.objects.get_or_create(
                slug=achievement_data['slug'],
                defaults=achievement_data
            )
            if created:
                self.stdout.write(f'Created achievement: {achievement.name}')

    def create_collaborations(self):
        """Create sample collaborations"""
        self.stdout.write('Creating collaborations...')
        
        collaborations_data = [
            {
                'owner': self.users[0],
                'name': 'AI & Machine Learning Innovators',
                'description': 'Cutting-edge startups using AI to solve real-world problems',
                'collaboration_type': 'public',
                'theme_color': '#8B5CF6',
                'is_featured': True,
            },
            {
                'owner': self.users[1],
                'name': 'Green Tech & Sustainability',
                'description': 'Startups fighting climate change and promoting sustainability',
                'collaboration_type': 'public',
                'theme_color': '#10B981',
                'is_featured': True,
            },
            {
                'owner': self.users[2],
                'name': 'EdTech Revolution',
                'description': 'Transforming education through technology',
                'collection_type': 'collaborative',
                'theme_color': '#3B82F6',
            },
            {
                'owner': self.users[0],
                'name': 'My Investment Watchlist',
                'description': 'Private collection of potential investment opportunities',
                'collection_type': 'private',
                'theme_color': '#F59E0B',
            },
            {
                'owner': self.users[3],
                'name': 'HealthTech Pioneers',
                'description': 'Digital health and biotech startups',
                'collaboration_type': 'public',
                'theme_color': '#EF4444',
            },
            {
                'owner': self.users[4],
                'name': 'FinTech Disruptors',
                'description': 'Financial technology startups changing how we handle money',
                'collaboration_type': 'public',
                'theme_color': '#6366F1',
            },
            {
                'owner': self.users[1],
                'name': 'Social Impact Startups',
                'description': 'Companies making a positive difference in society',
                'collection_type': 'collaborative',
                'theme_color': '#EC4899',
                'is_featured': True,
            },
            {
                'owner': self.users[2],
                'name': 'Future of Work',
                'description': 'Remote work tools, HR tech, and productivity startups',
                'collaboration_type': 'public',
                'theme_color': '#14B8A6',
            },
        ]
        
        for coll_data in collaborations_data:
            collaboration, created = StartupCollaboration.objects.get_or_create(
                owner=coll_data['owner'],
                name=coll_data['name'],
                defaults=coll_data
            )
            
            if created:
                self.stdout.write(f'Created collaboration: {collaboration.name}')
                
                # Add random startups to the collaboration
                num_startups = random.randint(5, 15)
                selected_startups = random.sample(self.startups, min(num_startups, len(self.startups)))
                
                for i, startup in enumerate(selected_startups):
                    CollaborationItem.objects.create(
                        collaboration=collaboration,
                        startup=startup,
                        added_by=collaboration.owner,
                        position=i,
                        custom_note=self.get_random_note(startup),
                        custom_tags=self.get_random_tags()
                    )
                
                # Add collaborators to collaborative collaborations
                if collaboration.collaboration_type == 'collaborative':
                    collaborators = random.sample([u for u in self.users if u != collaboration.owner], 2)
                    for collaborator in collaborators:
                        collaboration.collaborators.add(
                            collaborator,
                            through_defaults={
                                'permission_level': random.choice(['edit', 'admin']),
                                'added_by': collection.owner
                            }
                        )
                
                # Update metrics
                collection.view_count = random.randint(50, 500)
                collection.follower_count = random.randint(10, 100)
                collection.save()

    def create_scheduled_posts(self):
        """Create sample scheduled posts"""
        self.stdout.write('Creating scheduled posts...')
        
        scheduled_posts_data = [
            {
                'author': self.users[0],
                'title': 'Weekly Startup Spotlight: AI in Healthcare',
                'content': '''This week, I want to highlight some amazing startups using AI to revolutionize healthcare:

1. **MedAI Diagnostics** - Using computer vision for early disease detection
2. **HealthBot Pro** - AI-powered patient triage and support
3. **GenomeAI** - Machine learning for personalized medicine

What are your thoughts on AI in healthcare? Share your favorite health tech startups below!

#HealthTech #AIStartups #Innovation''',
                'post_type': 'discussion',
                'scheduled_for': timezone.now() + timedelta(days=1, hours=9),  # Tomorrow 9 AM
            },
            {
                'author': self.users[1],
                'title': 'Join us for Green Tech Summit 2025!',
                'content': '''Excited to announce that our startup will be presenting at the Green Tech Summit next month!

📅 Date: March 15-17, 2025
📍 Location: San Francisco Convention Center
🎟️ Use code STARTUP20 for 20% off tickets

We'll be showcasing our latest solar panel efficiency breakthrough. Hope to see you there!

#GreenTech #Sustainability #StartupEvents''',
                'post_type': 'announcement',
                'scheduled_for': timezone.now() + timedelta(days=7, hours=10),  # Next week
            },
            {
                'author': self.users[2],
                'title': 'What features do you want in an EdTech platform?',
                'content': '''We're building the next generation of online learning platforms and want YOUR input!

What features are missing from current EdTech solutions?
- Better collaboration tools?
- AI-powered tutoring?
- Gamification elements?
- VR/AR integration?

Drop your ideas in the comments! The best suggestions will be featured in our beta.

#EdTech #ProductDevelopment #CommunityFeedback''',
                'post_type': 'question',
                'scheduled_for': timezone.now() + timedelta(days=2, hours=14),  # Day after tomorrow, 2 PM
            },
            {
                'author': self.users[3],
                'title': 'Free Resources: Startup Financial Planning Templates',
                'content': '''Sharing my collection of financial planning templates that helped us reach profitability:

📊 Financial Model Template (Excel)
📈 Burn Rate Calculator
💰 Fundraising Timeline Planner
📋 Investor Pitch Deck Financial Section

Link: [startup-resources.com/financial-templates]

These are the exact templates we used to raise our Series A. Feel free to customize them for your needs!

#StartupResources #FinancialPlanning #Fundraising''',
                'post_type': 'resource',
                'scheduled_for': timezone.now() + timedelta(days=3, hours=11),
            },
            {
                'author': self.users[4],
                'title': 'FinTech Meetup - Network with Industry Leaders',
                'content': '''Join us for an exclusive FinTech networking event!

🗓️ When: Friday, March 5th, 6:00 PM - 9:00 PM
📍 Where: TechHub Downtown (123 Innovation Street)
🎯 Who: FinTech founders, investors, and enthusiasts

Agenda:
- 6:00 PM - Registration & Welcome Drinks
- 6:30 PM - Lightning Talks (5 startups, 5 minutes each)
- 7:30 PM - Open Networking
- 8:30 PM - Closing Remarks

RSVP: [fintech-meetup.eventbrite.com]

#FinTech #Networking #StartupEvents''',
                'post_type': 'event',
                'scheduled_for': timezone.now() + timedelta(days=5, hours=15),
            },
        ]
        
        for post_data in scheduled_posts_data:
            # Add some random related data
            if random.choice([True, False]) and self.startups:
                post_data['related_startup'] = random.choice(self.startups)
            
            post_data['topics_data'] = self.get_random_topics()
            
            scheduled_post = ScheduledPost.objects.create(**post_data)
            self.stdout.write(f'Created scheduled post: {scheduled_post.title}')
            
            # Simulate some as already published
            if random.random() > 0.7:
                scheduled_post.status = 'published'
                scheduled_post.published_at = scheduled_post.scheduled_for
                scheduled_post.save()

    def create_user_follows(self):
        """Create follow relationships between users"""
        self.stdout.write('Creating user follows...')
        
        for user in self.users:
            # Each user follows 2-4 other users
            num_following = random.randint(2, min(4, len(self.users) - 1))
            potential_follows = [u for u in self.users if u != user]
            to_follow = random.sample(potential_follows, num_following)
            
            for target_user in to_follow:
                UserFollow.objects.get_or_create(
                    follower=user,
                    following=target_user,
                    defaults={
                        'notify_on_posts': random.choice([True, True, False]),
                        'notify_on_stories': random.choice([True, False]),
                        'notify_on_achievements': random.choice([True, False]),
                    }
                )

    def create_stories(self):
        """Create sample stories"""
        self.stdout.write('Creating stories...')
        
        stories_data = [
            {
                'author': self.users[0],
                'story_type': 'text',
                'text_content': 'Just closed our Series A! 🎉 Grateful for everyone who believed in our vision. Big things coming!',
                'background_color': '#8B5CF6',
            },
            {
                'author': self.users[1],
                'story_type': 'achievement',
                'text_content': 'Finally hit 100 followers! Thanks for all the support 🙏',
                'background_color': '#10B981',
            },
            {
                'author': self.users[2],
                'story_type': 'link',
                'text_content': 'Check out our latest blog post on the future of EdTech!',
                'link_url': 'https://example.com/blog/future-of-edtech',
                'link_title': 'The Future of Education Technology',
                'link_description': 'How AI and VR are transforming the classroom',
                'background_color': '#3B82F6',
            },
            {
                'author': self.users[3],
                'story_type': 'text',
                'text_content': 'Looking for a senior developer to join our team! DM if interested 💼',
                'background_color': '#F59E0B',
            },
        ]
        
        for story_data in stories_data:
            # Some stories might be related to startups
            if random.choice([True, False]) and self.startups:
                story_data['related_startup'] = random.choice(self.startups)
            
            story = Story.objects.create(**story_data)
            story.view_count = random.randint(10, 200)
            story.save()
            self.stdout.write(f'Created story by {story.author.username}')

    def assign_achievements_to_users(self):
        """Assign some achievements to users"""
        self.stdout.write('Assigning achievements to users...')
        
        achievements = Achievement.objects.filter(is_active=True)
        
        for user in self.users:
            # Each user gets 2-5 random achievements
            num_achievements = random.randint(2, min(5, achievements.count()))
            user_achievements = random.sample(list(achievements), num_achievements)
            
            for achievement in user_achievements:
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={
                        'progress_data': self.get_random_progress_data(achievement),
                        'is_pinned': random.random() > 0.7,
                        'is_public': random.random() > 0.2,
                    }
                )
                
                # Update achievement earned count
                achievement.earned_count += 1
                achievement.save()

    def get_random_note(self, startup):
        """Generate random notes for collection items"""
        notes = [
            f"Great team and solid business model. {startup.name} is definitely one to watch!",
            f"Innovative approach to {startup.industry.name if hasattr(startup, 'industry') else 'the market'}.",
            f"Met the founders at a conference - very impressive vision.",
            f"Strong growth metrics. Potential unicorn in the making.",
            f"Interesting pivot from their original idea. Much stronger product-market fit now.",
            f"Love their commitment to sustainability and social impact.",
            f"Already using their product - game changer!",
            f"Backed by top-tier VCs. Definitely going places.",
        ]
        return random.choice(notes)

    def get_random_tags(self):
        """Generate random tags for collection items"""
        all_tags = [
            'promising', 'series-a', 'seed-stage', 'scaling', 'profitable',
            'innovative', 'disruptive', 'b2b', 'b2c', 'saas', 'marketplace',
            'platform', 'mobile-first', 'ai-powered', 'blockchain', 'iot',
            'remote-first', 'diverse-team', 'female-founded', 'impact-driven'
        ]
        num_tags = random.randint(1, 4)
        return random.sample(all_tags, num_tags)

    def get_random_topics(self):
        """Generate random topics for posts"""
        topics = [
            'startup-advice', 'fundraising', 'product-development', 'marketing',
            'sales', 'team-building', 'culture', 'remote-work', 'ai', 'blockchain',
            'sustainability', 'social-impact', 'growth-hacking', 'metrics', 'pivot'
        ]
        num_topics = random.randint(1, 3)
        return random.sample(topics, num_topics)

    def get_random_progress_data(self, achievement):
        """Generate random progress data for achievements"""
        if achievement.slug == 'first-steps':
            return {'profile_fields_completed': ['first_name', 'last_name', 'bio']}
        elif achievement.slug == 'social-butterfly':
            return {'following_count': random.randint(50, 100)}
        elif achievement.slug == 'content-creator':
            return {'posts_count': random.randint(50, 80)}
        else:
            return {'progress': 'completed'}