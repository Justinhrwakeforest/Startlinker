#!/usr/bin/env python
"""
Award initial achievements to users
"""
import os
import sys
import django

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set required static URL for development
os.environ['STATIC_URL'] = '/static/'

# Setup Django with base settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.base')
django.setup()

from apps.users.models import User
from apps.users.social_models import Achievement, UserAchievement, UserPoints, PointsHistory
from django.utils import timezone
from django.db import transaction

def award_signup_achievements():
    """Award signup bonus and other initial achievements to users"""
    
    # Get the most recent user (the one who just signed up)
    users = User.objects.filter(is_active=True).order_by('-date_joined')[:5]
    
    if not users:
        print("No users found")
        return
    
    # Get signup-related achievements
    signup_achievements = Achievement.objects.filter(
        slug__in=['signup_bonus', 'first_steps', 'welcome_aboard', 'early_adopter']
    )
    
    print(f"Found {signup_achievements.count()} signup achievements")
    
    for user in users:
        print(f"\nProcessing user: {user.username}")
        
        # Initialize user points if not exists
        user_points, created = UserPoints.objects.get_or_create(
            user=user,
            defaults={
                'total_points': 0,
                'current_level': 1,
                'points_this_month': 0
            }
        )
        
        if created:
            print(f"Created points for {user.username}")
        
        with transaction.atomic():
            for achievement in signup_achievements:
                # Check if user already has this achievement
                if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                    # Award the achievement
                    user_achievement = UserAchievement.objects.create(
                        user=user,
                        achievement=achievement,
                        earned_at=timezone.now()
                    )
                    print(f"✅ Awarded '{achievement.name}' to {user.username} (+{achievement.points} points)")
                    
                    # Award points
                    if achievement.points > 0:
                        user_points.total_points += achievement.points
                        user_points.points_this_month += achievement.points
                        user_points.save()
                        
                        # Record points history
                        PointsHistory.objects.create(
                            user=user,
                            points=achievement.points,
                            activity_type='achievement',
                            description=f'Achievement unlocked: {achievement.name}',
                            balance_after=user_points.total_points
                        )
                else:
                    print(f"⏭️  {user.username} already has '{achievement.name}'")
        
        # Award some activity-based achievements if applicable
        activity_achievements = Achievement.objects.filter(
            slug__in=['first_login', 'profile_complete']
        )
        
        for achievement in activity_achievements:
            if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                # Check conditions
                should_award = False
                
                if achievement.slug == 'first_login':
                    # Award if user has logged in (they have if they're active)
                    should_award = user.is_active
                elif achievement.slug == 'profile_complete':
                    # Award if profile has basic info
                    should_award = bool(user.first_name or user.last_name)
                
                if should_award:
                    with transaction.atomic():
                        user_achievement = UserAchievement.objects.create(
                            user=user,
                            achievement=achievement,
                            earned_at=timezone.now()
                        )
                        print(f"✅ Awarded '{achievement.name}' to {user.username} (+{achievement.points} points)")
                        
                        # Award points
                        if achievement.points > 0:
                            user_points.total_points += achievement.points
                            user_points.points_this_month += achievement.points
                            user_points.save()
                            
                            # Record points history
                            PointsHistory.objects.create(
                                user=user,
                                points=achievement.points,
                                activity_type='achievement',
                                description=f'Achievement unlocked: {achievement.name}',
                                balance_after=user_points.total_points
                            )
        
        # Print user's total achievements
        total_achievements = UserAchievement.objects.filter(user=user).count()
        print(f"\n{user.username} now has {total_achievements} achievements and {user_points.total_points} points")

if __name__ == '__main__':
    award_signup_achievements()
    print("\n✅ Achievement awarding complete!")