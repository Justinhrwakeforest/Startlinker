#!/usr/bin/env python
"""Unlock achievements for existing users based on their current activity"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.social_models import UserPoints, PointsHistory, UserFollow, Story, UserAchievement, Achievement
from apps.users.points_service import PointsService
from apps.posts.models import Post
from apps.startups.models import Startup
from apps.jobs.models import Job

User = get_user_model()

def calculate_user_stats(user):
    """Calculate comprehensive stats for a user"""
    try:
        # Get posts count
        posts_count = Post.objects.filter(author=user, is_approved=True).count()
        
        # Get stories count
        stories_count = Story.objects.filter(author=user).count()
        
        # Get social stats
        followers_count = UserFollow.objects.filter(following=user).count()
        following_count = UserFollow.objects.filter(follower=user).count()
        
        # Get startup stats
        startups_claimed = Startup.objects.filter(claimed_by=user, claim_verified=True).count()
        startups_submitted = Startup.objects.filter(submitted_by=user, is_approved=True).count()
        
        # Get job stats
        try:
            jobs_posted = Job.objects.filter(company_contact=user).count()
        except:
            jobs_posted = 0
        
        # Get points stats
        user_points = UserPoints.get_or_create_for_user(user)
        
        return {
            'posts_count': posts_count,
            'stories_count': stories_count,
            'followers_count': followers_count,
            'following_count': following_count,
            'startups_claimed': startups_claimed,
            'startups_submitted': startups_submitted,
            'jobs_posted': jobs_posted,
            'total_points': user_points.total_points,
            'level': user_points.level,
        }
    except Exception as e:
        print(f"Error calculating stats for {user.username}: {e}")
        return {}

def unlock_achievements_for_user(user, stats):
    """Unlock all achievements a user qualifies for"""
    unlocked_count = 0
    
    # Get all active achievements
    achievements = Achievement.objects.filter(is_active=True)
    
    for achievement in achievements:
        # Check if user already has this achievement
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        # Check if user meets requirements
        if meets_achievement_requirements(stats, achievement):
            try:
                # Create the achievement
                UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    progress_data=stats
                )
                
                # Award achievement points
                PointsService.award_points(
                    user,
                    'achievement',
                    points=achievement.points,
                    description=f"Achievement Unlocked: {achievement.name}",
                    achievement=achievement
                )
                
                unlocked_count += 1
                print(f"   + Unlocked: {achievement.name} ({achievement.points} pts)")
                
            except Exception as e:
                print(f"   - Failed to unlock {achievement.name}: {e}")
    
    return unlocked_count

def meets_achievement_requirements(stats, achievement):
    """Check if user stats meet achievement requirements"""
    requirements = achievement.requirements
    if not requirements:
        return False
    
    for key, required_value in requirements.items():
        if key in stats:
            if stats[key] < required_value:
                return False
        elif key == 'profile_completion':
            # For now, assume all users have completed profiles
            continue
        elif key == 'verification':
            # For now, assume all users are verified
            continue
        elif key == 'join_date':
            # Skip date-based requirements for existing users
            continue
        elif key == 'consecutive_days':
            # Skip consecutive days for retroactive unlock
            continue
        elif key == 'night_activity':
            # Skip time-based requirements
            continue
    
    return True

def unlock_all_existing_achievements():
    """Process all users and unlock their achievements"""
    print("Unlocking achievements for existing users based on current activity...")
    print("=" * 70)
    
    users = User.objects.all()
    total_unlocked = 0
    
    for user in users:
        print(f"\nProcessing {user.username}...")
        
        # Calculate user stats
        stats = calculate_user_stats(user)
        if not stats:
            continue
        
        print(f"   Stats: {stats['posts_count']} posts, {stats['followers_count']} followers, "
              f"{stats['following_count']} following, {stats['total_points']} points")
        
        # Unlock achievements
        unlocked = unlock_achievements_for_user(user, stats)
        total_unlocked += unlocked
        
        if unlocked == 0:
            print("   -> No new achievements to unlock")
        else:
            print(f"   >> Unlocked {unlocked} achievements!")
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Unlocked {total_unlocked} total achievements across all users!")
    print("All existing achievements have been processed!")

if __name__ == '__main__':
    unlock_all_existing_achievements()