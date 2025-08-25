#!/usr/bin/env python
"""Initialize points system for existing users and test functionality"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.social_models import UserPoints, PointsHistory
from apps.users.points_service import PointsService

User = get_user_model()

def initialize_points_for_users():
    """Initialize points system for all existing users"""
    print('Initializing points system...')
    
    users = User.objects.all()
    
    for user in users:
        print(f"Setting up points for {user.username}...")
        
        # Create or get user points
        user_points = UserPoints.get_or_create_for_user(user)
        
        # Award some initial points based on existing activities
        initial_points = 0
        
        # Check for existing posts
        try:
            from apps.posts.models import Post
            posts_count = Post.objects.filter(author=user, is_approved=True).count()
            if posts_count > 0:
                points_for_posts = posts_count * 10
                initial_points += points_for_posts
                print(f"  - Found {posts_count} posts, awarding {points_for_posts} points")
        except:
            pass
        
        # Check for existing startups
        try:
            from apps.startups.models import Startup
            submitted_startups = Startup.objects.filter(submitted_by=user, is_approved=True).count()
            claimed_startups = Startup.objects.filter(claimed_by=user, claim_verified=True).count()
            
            startup_points = (submitted_startups * 25) + (claimed_startups * 50)
            if startup_points > 0:
                initial_points += startup_points
                print(f"  - Found {submitted_startups} submitted and {claimed_startups} claimed startups, awarding {startup_points} points")
        except:
            pass
        
        # Check for social activities
        try:
            from apps.users.social_models import UserFollow, Story
            following_count = UserFollow.objects.filter(follower=user).count()
            stories_count = Story.objects.filter(author=user).count()
            
            social_points = (following_count * 2) + (stories_count * 5)
            if social_points > 0:
                initial_points += social_points
                print(f"  - Found {following_count} follows and {stories_count} stories, awarding {social_points} points")
        except:
            pass
        
        # Check for jobs
        try:
            from apps.jobs.models import Job
            jobs_posted = Job.objects.filter(company_contact=user).count()
            if jobs_posted > 0:
                job_points = jobs_posted * 20
                initial_points += job_points
                print(f"  - Found {jobs_posted} jobs posted, awarding {job_points} points")
        except:
            pass
        
        # Award initial points if any activity found
        if initial_points > 0:
            user_points.add_points(initial_points, 'general')
            
            # Create history entry
            PointsHistory.objects.create(
                user=user,
                points=initial_points,
                reason='other',
                description=f"Initial points for existing activity"
            )
            
            print(f"  - Total initial points awarded: {initial_points}")
        
        # Award welcome bonus
        welcome_points = 50
        user_points.add_points(welcome_points, 'general')
        
        PointsHistory.objects.create(
            user=user,
            points=welcome_points,
            reason='other',
            description="Welcome bonus for joining StartupHub"
        )
        
        print(f"  - Welcome bonus: {welcome_points} points")
        print(f"  - Final total: {user_points.total_points} points, Level {user_points.level}")
        print()

def test_points_system():
    """Test the points system functionality"""
    print('Testing points system...')
    
    user = User.objects.first()
    if not user:
        print("No users found to test with")
        return
    
    print(f"Testing with user: {user.username}")
    
    # Test award points
    try:
        PointsService.award_points(
            user,
            'post_create',
            description="Test post creation"
        )
        print("✓ Successfully awarded points for post creation")
    except Exception as e:
        print(f"✗ Error awarding points: {e}")
    
    # Test achievement checking
    try:
        unlocked_count = PointsService.check_and_unlock_achievements(user)
        print(f"✓ Checked achievements, unlocked {unlocked_count} new achievements")
    except Exception as e:
        print(f"✗ Error checking achievements: {e}")
    
    # Get updated user points
    user_points = UserPoints.get_or_create_for_user(user)
    print(f"Final user stats:")
    print(f"  - Total Points: {user_points.total_points}")
    print(f"  - Level: {user_points.level}")
    print(f"  - Level Progress: {user_points.level_progress:.1f}%")
    print(f"  - Points This Month: {user_points.points_this_month}")

if __name__ == '__main__':
    initialize_points_for_users()
    print("=" * 50)
    test_points_system()
    print("Points system initialization complete!")