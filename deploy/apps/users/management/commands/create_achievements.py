# apps/users/management/commands/create_achievements.py
from django.core.management.base import BaseCommand
from apps.users.social_models import Achievement

class Command(BaseCommand):
    help = 'Create default achievements for the platform'

    def handle(self, *args, **options):
        achievements_data = [
            # Profile Completion Achievements
            {
                'name': 'Welcome Aboard!',
                'slug': 'welcome-aboard',
                'description': 'Successfully signed up for StartLinker. Welcome to the community!',
                'category': 'profile',
                'rarity': 'common',
                'icon': '🎉',
                'color': '#10B981',
                'points': 50,
                'requirements': {'activity_count': {'type': 'signup_bonus', 'count': 1}},
                'is_secret': False,
            },
            {
                'name': 'Profile Pioneer',
                'slug': 'profile-pioneer',
                'description': 'Complete your profile by adding a picture, bio, and location.',
                'category': 'profile',
                'rarity': 'common',
                'icon': '👤',
                'color': '#3B82F6',
                'points': 75,
                'requirements': {
                    'multiple_conditions': [
                        {'type': 'activity_count', 'activity_type': 'profile_picture_upload', 'required': 1},
                        {'type': 'activity_count', 'activity_type': 'profile_bio_complete', 'required': 1},
                        {'type': 'activity_count', 'activity_type': 'profile_location_add', 'required': 1},
                    ]
                },
                'is_secret': False,
            },
            {
                'name': 'Verified Member',
                'slug': 'verified-member',
                'description': 'Verify your email address to unlock full platform features.',
                'category': 'profile',
                'rarity': 'common',
                'icon': '✅',
                'color': '#10B981',
                'points': 25,
                'requirements': {'activity_count': {'type': 'email_verify', 'count': 1}},
                'is_secret': False,
            },
            
            # Content Creation Achievements
            {
                'name': 'First Steps',
                'slug': 'first-steps',
                'description': 'Share your first post with the community!',
                'category': 'content',
                'rarity': 'common',
                'icon': '✍️',
                'color': '#6366F1',
                'points': 100,
                'requirements': {'activity_count': {'type': 'first_post', 'count': 1}},
                'is_secret': False,
            },
            {
                'name': 'Active Creator',
                'slug': 'active-creator',
                'description': 'Create 10 posts and establish your voice in the community.',
                'category': 'content',
                'rarity': 'uncommon',
                'icon': '📝',
                'color': '#8B5CF6',
                'points': 200,
                'requirements': {'posts': 10},
                'is_secret': False,
            },
            {
                'name': 'Prolific Writer',
                'slug': 'prolific-writer',
                'description': 'Share 50 posts and become a recognized contributor.',
                'category': 'content',
                'rarity': 'rare',
                'icon': '📚',
                'color': '#F59E0B',
                'points': 500,
                'requirements': {'posts': 50},
                'is_secret': False,
            },
            
            # Social Achievements
            {
                'name': 'Social Butterfly',
                'slug': 'social-butterfly',
                'description': 'Follow your first user and start building your network!',
                'category': 'social',
                'rarity': 'common',
                'icon': '🦋',
                'color': '#EC4899',
                'points': 50,
                'requirements': {'activity_count': {'type': 'first_follow', 'count': 1}},
                'is_secret': False,
            },
            {
                'name': 'Network Builder',
                'slug': 'network-builder',
                'description': 'Follow 10 users and expand your professional network.',
                'category': 'networking',
                'rarity': 'uncommon',
                'icon': '🌐',
                'color': '#10B981',
                'points': 150,
                'requirements': {'activity_count': {'type': 'follow_user', 'count': 10}},
                'is_secret': False,
            },
            {
                'name': 'Popular Member',
                'slug': 'popular-member',
                'description': 'Gain 25 followers and become a recognized community member.',
                'category': 'social',
                'rarity': 'rare',
                'icon': '⭐',
                'color': '#F59E0B',
                'points': 300,
                'requirements': {'followers': 25},
                'is_secret': False,
            },
            
            # Startup Achievements
            {
                'name': 'Startup Founder',
                'slug': 'startup-founder',
                'description': 'Submit your first startup to the platform!',
                'category': 'startup',
                'rarity': 'uncommon',
                'icon': '🚀',
                'color': '#8B5CF6',
                'points': 200,
                'requirements': {'activity_count': {'type': 'first_startup_submit', 'count': 1}},
                'is_secret': False,
            },
            {
                'name': 'Startup Enthusiast',
                'slug': 'startup-enthusiast',
                'description': 'Submit 5 startups and show your entrepreneurial spirit.',
                'category': 'startup',
                'rarity': 'rare',
                'icon': '💼',
                'color': '#F59E0B',
                'points': 400,
                'requirements': {'activity_count': {'type': 'startup_submit', 'count': 5}},
                'is_secret': False,
            },
            
            # Job Achievements
            {
                'name': 'Job Creator',
                'slug': 'job-creator',
                'description': 'Post your first job opportunity and help others find work!',
                'category': 'jobs',
                'rarity': 'uncommon',
                'icon': '💼',
                'color': '#3B82F6',
                'points': 150,
                'requirements': {'activity_count': {'type': 'first_job_post', 'count': 1}},
                'is_secret': False,
            },
            
            # Points-based Achievements
            {
                'name': 'Rising Star',
                'slug': 'rising-star',
                'description': 'Earn your first 500 points through platform engagement.',
                'category': 'special',
                'rarity': 'uncommon',
                'icon': '🌟',
                'color': '#F59E0B',
                'points': 100,
                'requirements': {'points_total': 500},
                'is_secret': False,
            },
            {
                'name': 'Community Champion',
                'slug': 'community-champion',
                'description': 'Earn 2000 points and become a community champion!',
                'category': 'special',
                'rarity': 'rare',
                'icon': '🏆',
                'color': '#F59E0B',
                'points': 300,
                'requirements': {'points_total': 2000},
                'is_secret': False,
            },
            {
                'name': 'Platform Legend',
                'slug': 'platform-legend',
                'description': 'Achieve legendary status with 10,000 points!',
                'category': 'special',
                'rarity': 'legendary',
                'icon': '👑',
                'color': '#F59E0B',
                'points': 1000,
                'requirements': {'points_total': 10000},
                'is_secret': False,
            },
            
            # Login Streak Achievements
            {
                'name': 'Dedicated User',
                'slug': 'dedicated-user',
                'description': 'Login for 7 consecutive days and show your commitment!',
                'category': 'social',
                'rarity': 'uncommon',
                'icon': '🔥',
                'color': '#EF4444',
                'points': 150,
                'requirements': {'consecutive_days': {'type': 'daily_login', 'days': 7}},
                'is_secret': False,
            },
            {
                'name': 'Super User',
                'slug': 'super-user',
                'description': 'Maintain a 30-day login streak and prove your dedication!',
                'category': 'social',
                'rarity': 'epic',
                'icon': '⚡',
                'color': '#8B5CF6',
                'points': 500,
                'requirements': {'consecutive_days': {'type': 'daily_login', 'days': 30}},
                'is_secret': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for achievement_data in achievements_data:
            achievement, created = Achievement.objects.get_or_create(
                slug=achievement_data['slug'],
                defaults=achievement_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created achievement: {achievement.name}')
                )
            else:
                # Update existing achievement
                for key, value in achievement_data.items():
                    if key != 'slug':
                        setattr(achievement, key, value)
                achievement.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated achievement: {achievement.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new achievements, updated {updated_count} existing achievements.'
            )
        )