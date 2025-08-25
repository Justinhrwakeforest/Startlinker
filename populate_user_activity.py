# populate_user_activity.py - Retroactively populate user activities
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.simple_prod')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.activity_tracker import ActivityTracker
from apps.users.points_service import PointsService
from apps.users.achievement_tracker import AchievementTracker

User = get_user_model()

def populate_user_activity(username='hruthik'):
    """Populate activity data for existing user based on their usage"""
    try:
        user = User.objects.get(username=username)
        print(f"Populating activities for user: {user.username}")
        
        # Award signup bonus (backdated)
        ActivityTracker.track_signup(user)
        print("Tracked signup activity")
        
        # Profile activities (simulate profile completion)
        profile_activities = [
            'email_verify',
            'profile_picture_upload', 
            'profile_bio_complete',
            'profile_location_add',
        ]
        
        for activity in profile_activities:
            ActivityTracker.track_profile_activity(user, activity)
            print(f"Tracked {activity}")
        
        # Login activities (simulate login history)
        for i in range(5):  # Last 5 days
            ActivityTracker.track_login(user)
        print("Tracked login activities")
        
        # Existing startup interactions (based on current activity page)
        # Simulate startup bookmarking
        ActivityTracker.track_social_activity(user, 'bookmark_post')
        print("Tracked startup bookmark")
        
        # Content creation activities
        ActivityTracker.track_content_creation(user, 'post', is_first=True)
        print("Tracked first post creation")
        
        # Social activities
        ActivityTracker.track_social_activity(user, 'follow_user')
        print("Tracked first user follow")
        
        # Startup activities
        ActivityTracker.track_startup_activity(user, 'startup_submit', 'UserStartup')
        print("Tracked startup submission")
        
        # Milestone activities
        ActivityTracker.track_milestone(user, 'milestone_verified', 'Account fully verified as admin user')
        print("Tracked verification milestone")
        
        # Get final statistics
        from apps.users.social_models import UserPoints, PointsHistory
        user_points = UserPoints.get_or_create_for_user(user)
        total_activities = PointsHistory.objects.filter(user=user).count()
        
        print(f"\nActivity population completed!")
        print(f"Final Stats:")
        print(f"   Total Points: {user_points.total_points}")
        print(f"   Level: {user_points.level}")
        print(f"   Total Activities: {total_activities}")
        print(f"   Content Points: {user_points.content_points}")
        print(f"   Social Points: {user_points.social_points}")
        print(f"   Startup Points: {user_points.startup_points}")
        
        # Check and unlock achievements
        print(f"\nChecking achievements...")
        unlocked_achievements = AchievementTracker.check_and_unlock_achievements(user)
        
        if unlocked_achievements:
            print(f"🎉 Unlocked {len(unlocked_achievements)} achievements:")
            for user_achievement in unlocked_achievements:
                print(f"   🏆 {user_achievement.achievement.name} (+{user_achievement.achievement.points} points)")
        else:
            print("   No new achievements unlocked")
        
        return True
        
    except User.DoesNotExist:
        print(f"User '{username}' not found")
        return False
    except Exception as e:
        print(f"Error populating activities: {str(e)}")
        return False

if __name__ == "__main__":
    populate_user_activity()