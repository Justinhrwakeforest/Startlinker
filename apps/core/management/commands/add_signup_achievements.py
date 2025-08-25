#!/usr/bin/env python
"""Add signup and milestone achievements"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.core.management.base import BaseCommand
from apps.users.social_models import Achievement
import json

class Command(BaseCommand):
    help = 'Add signup and milestone achievements'

    def handle(self, *args, **options):
        self.stdout.write('Adding signup and milestone achievements...')
        
        # Define new achievements
        achievements_data = [
            {
                'name': 'Welcome to StartupHub!',
                'slug': 'welcome-signup',
                'description': 'Welcome to the StartupHub community! Thanks for joining us.',
                'category': 'milestone',
                'rarity': 'common',
                'icon': '🎉',
                'points': 100,
                'requirements': {},  # Automatically awarded on signup
                'is_active': True,
            },
            {
                'name': 'First Post Creator',
                'slug': 'first-post-created',
                'description': 'Created your very first post! Welcome to the conversation.',
                'category': 'content',
                'rarity': 'common',
                'icon': '✍️',
                'points': 50,
                'requirements': {'posts_count': 1},
                'is_active': True,
            },
            {
                'name': 'Daily Visitor',
                'slug': 'daily-login',
                'description': 'Logged in for 7 consecutive days. Building great habits!',
                'category': 'engagement',
                'rarity': 'uncommon',
                'icon': '📅',
                'points': 25,
                'requirements': {'consecutive_days': 7},
                'is_active': True,
            },
            {
                'name': 'Dedicated Member',
                'slug': 'monthly-login',
                'description': 'Logged in for 30 consecutive days. You are truly dedicated!',
                'category': 'engagement',
                'rarity': 'rare',
                'icon': '🏆',
                'points': 100,
                'requirements': {'consecutive_days': 30},
                'is_active': True,
            },
            {
                'name': 'Network Builder',
                'slug': 'follow-ten-users',
                'description': 'Followed 10 interesting people. Networking pro!',
                'category': 'social',
                'rarity': 'uncommon',
                'icon': '🦋',
                'points': 30,
                'requirements': {'following_count': 10},
                'is_active': True,
            },
            {
                'name': 'Active Creator',
                'slug': 'ten-posts-created',
                'description': 'Created 10 posts. You are becoming a content creator!',
                'category': 'content',
                'rarity': 'uncommon',
                'icon': '📝',
                'points': 75,
                'requirements': {'posts_count': 10},
                'is_active': True,
            },
            {
                'name': 'Prolific Writer',
                'slug': 'fifty-posts',
                'description': 'Created 50 posts. Your voice is heard loud and clear!',
                'category': 'content',
                'rarity': 'rare',
                'icon': '🖊️',
                'points': 200,
                'requirements': {'posts_count': 50},
                'is_active': True,
            },
            {
                'name': 'Popular Leader',
                'slug': 'hundred-followers-earned',
                'description': 'Gained 100 followers. You are a true community leader!',
                'category': 'social',
                'rarity': 'epic',
                'icon': '👑',
                'points': 300,
                'requirements': {'followers_count': 100},
                'is_active': True,
            },
            {
                'name': 'Points Collector',
                'slug': 'thousand-points',
                'description': 'Accumulated 1000 total points. You are on fire!',
                'category': 'milestone',
                'rarity': 'rare',
                'icon': '💎',
                'points': 100,
                'requirements': {'total_points': 1000},
                'is_active': True,
            },
            {
                'name': 'Points Master',
                'slug': 'five-thousand-points',
                'description': 'Accumulated 5000 total points. You are a true master!',
                'category': 'milestone',
                'rarity': 'epic',
                'icon': '💯',
                'points': 250,
                'requirements': {'total_points': 5000},
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for achievement_data in achievements_data:
            try:
                # Check if achievement already exists
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
                    # Update existing achievement (but don't change name if it exists)
                    for key, value in achievement_data.items():
                        if key not in ['slug', 'name']:  # Don't update slug or name
                            setattr(achievement, key, value)
                    achievement.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated achievement: {achievement.name}')
                    )
            except Exception as e:
                # Skip if there's a naming conflict
                self.stdout.write(
                    self.style.ERROR(f'Skipped achievement {achievement_data["name"]}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nAchievement setup complete!\n'
                f'Created: {created_count} new achievements\n'
                f'Updated: {updated_count} existing achievements'
            )
        )