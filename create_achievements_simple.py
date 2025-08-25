#!/usr/bin/env python
"""Simple script to create achievements without Celery dependencies"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.social_models import Achievement, UserAchievement

User = get_user_model()

def create_achievements():
    """Create diverse achievements with unique icons"""
    print('Creating achievements...')
    
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
            'description': 'Complete all profile sections including avatar',
            'category': 'profile',
            'rarity': 'uncommon',
            'icon': '⭐',
            'color': '#10B981',
            'points': 25,
            'requirements': {'profile_completion': 100},
        },
        {
            'name': 'Verified User',
            'slug': 'verified-user',
            'description': 'Verify your email and phone number',
            'category': 'profile',
            'rarity': 'uncommon',
            'icon': '✅',
            'color': '#10B981',
            'points': 20,
            'requirements': {'verification': True},
        },
        
        # Social Achievements
        {
            'name': 'Social Butterfly',
            'slug': 'social-butterfly',
            'description': 'Follow 10 users and build your network',
            'category': 'social',
            'rarity': 'uncommon',
            'icon': '🦋',
            'color': '#10B981',
            'points': 30,
            'requirements': {'following_count': 10},
        },
        {
            'name': 'Popular User',
            'slug': 'popular-user',
            'description': 'Gain 50 followers',
            'category': 'social',
            'rarity': 'rare',
            'icon': '🌟',
            'color': '#3B82F6',
            'points': 50,
            'requirements': {'followers_count': 50},
        },
        {
            'name': 'Influencer',
            'slug': 'influencer',
            'description': 'Gain 100 followers',
            'category': 'social',
            'rarity': 'epic',
            'icon': '📢',
            'color': '#8B5CF6',
            'points': 100,
            'requirements': {'followers_count': 100},
        },
        {
            'name': 'Celebrity',
            'slug': 'celebrity',
            'description': 'Gain 500 followers and become famous',
            'category': 'social',
            'rarity': 'legendary',
            'icon': '👑',
            'color': '#F59E0B',
            'points': 200,
            'requirements': {'followers_count': 500},
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
            'description': 'Create 25 posts and share your knowledge',
            'category': 'content',
            'rarity': 'rare',
            'icon': '✍️',
            'color': '#3B82F6',
            'points': 75,
            'requirements': {'posts_count': 25},
        },
        {
            'name': 'Thought Leader',
            'slug': 'thought-leader',
            'description': 'Create 50 high-quality posts',
            'category': 'content',
            'rarity': 'epic',
            'icon': '🧠',
            'color': '#8B5CF6',
            'points': 150,
            'requirements': {'posts_count': 50},
        },
        {
            'name': 'Master Storyteller',
            'slug': 'master-storyteller',
            'description': 'Create 20 engaging stories',
            'category': 'content',
            'rarity': 'rare',
            'icon': '📚',
            'color': '#3B82F6',
            'points': 80,
            'requirements': {'stories_count': 20},
        },
        
        # Startup Achievements
        {
            'name': 'Startup Founder',
            'slug': 'startup-founder',
            'description': 'Successfully register and claim your startup',
            'category': 'startup',
            'rarity': 'epic',
            'icon': '🚀',
            'color': '#8B5CF6',
            'points': 100,
            'requirements': {'startup_claimed': 1},
        },
        {
            'name': 'Serial Entrepreneur',
            'slug': 'serial-entrepreneur',
            'description': 'Register 3 different startups',
            'category': 'startup',
            'rarity': 'legendary',
            'icon': '💼',
            'color': '#F59E0B',
            'points': 250,
            'requirements': {'startups_claimed': 3},
        },
        {
            'name': 'Startup Scout',
            'slug': 'startup-scout',
            'description': 'Submit 5 startups to the platform',
            'category': 'startup',
            'rarity': 'uncommon',
            'icon': '🔍',
            'color': '#10B981',
            'points': 40,
            'requirements': {'startups_submitted': 5},
        },
        
        # Community Achievements
        {
            'name': 'Helpful Member',
            'slug': 'helpful-member',
            'description': 'Help others by answering questions',
            'category': 'community',
            'rarity': 'uncommon',
            'icon': '🤝',
            'color': '#10B981',
            'points': 35,
            'requirements': {'helpful_actions': 10},
        },
        {
            'name': 'Community Leader',
            'slug': 'community-leader',
            'description': 'Become a respected community member',
            'category': 'community',
            'rarity': 'epic',
            'icon': '🏆',
            'color': '#8B5CF6',
            'points': 120,
            'requirements': {'leadership_score': 100},
        },
        
        # Special Achievements
        {
            'name': 'Early Adopter',
            'slug': 'early-adopter',
            'description': 'Join the platform in its early days',
            'category': 'special',
            'rarity': 'rare',
            'icon': '🌱',
            'color': '#3B82F6',
            'points': 60,
            'requirements': {'join_date': 'early'},
        },
        {
            'name': 'Night Owl',
            'slug': 'night-owl',
            'description': 'Active during late night hours',
            'category': 'special',
            'rarity': 'uncommon',
            'icon': '🦉',
            'color': '#10B981',
            'points': 30,
            'requirements': {'night_activity': True},
        },
        {
            'name': 'Marathon User',
            'slug': 'marathon-user',
            'description': 'Use the platform for 30 consecutive days',
            'category': 'special',
            'rarity': 'epic',
            'icon': '🏃',
            'color': '#8B5CF6',
            'points': 150,
            'requirements': {'consecutive_days': 30},
        },
    ]
    
    created_count = 0
    for achievement_data in achievements_data:
        achievement, created = Achievement.objects.get_or_create(
            slug=achievement_data['slug'],
            defaults=achievement_data
        )
        if created:
            created_count += 1
            print(f"Created achievement: {achievement.name}")
        else:
            print(f"Achievement already exists: {achievement.name}")
    
    print(f"Created {created_count} new achievements")
    return Achievement.objects.all()

def assign_sample_achievements():
    """Assign some achievements to the current user for testing"""
    print('Assigning sample achievements...')
    
    # Get the first user (or create if none exists)
    try:
        user = User.objects.first()
        if not user:
            print("No users found. Please create a user first.")
            return
        
        # Get some achievements to assign
        achievements_to_assign = [
            'first-steps',
            'profile-pro', 
            'first-post',
            'social-butterfly',
            'helpful-member',
            'early-adopter',
            'night-owl',
            'startup-scout',
            'content-creator',
            'popular-user',
            'verified-user',
            'thought-leader',
            'startup-founder',
            'community-leader',
            'marathon-user',
            'serial-entrepreneur'
        ]
        
        assigned_count = 0
        for slug in achievements_to_assign:
            try:
                achievement = Achievement.objects.get(slug=slug)
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'progress_data': {}}
                )
                if created:
                    assigned_count += 1
                    print(f"Assigned {achievement.name} to {user.username}")
            except Achievement.DoesNotExist:
                print(f"Achievement {slug} not found")
        
        print(f"Assigned {assigned_count} achievements to {user.username}")
        
    except Exception as e:
        print(f"Error assigning achievements: {e}")

if __name__ == '__main__':
    create_achievements()
    assign_sample_achievements()
    print("Done!")