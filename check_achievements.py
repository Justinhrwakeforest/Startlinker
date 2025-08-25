#!/usr/bin/env python
"""Check if achievements exist in the database"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
sys.path.append('.')

django.setup()

from django.contrib.auth import get_user_model
from apps.users.social_models import Achievement, UserAchievement

User = get_user_model()

def check_achievements():
    """Check if achievements exist"""
    try:
        # Count total achievements
        total_achievements = Achievement.objects.filter(is_active=True).count()
        print(f"Total active achievements in database: {total_achievements}")
        
        # Get sample achievements
        print("\nSample achievements:")
        for achievement in Achievement.objects.filter(is_active=True)[:5]:
            print(f"  - {achievement.name} ({achievement.rarity}) - {achievement.points} pts")
        
        # Check user achievements for the first user
        user = User.objects.first()
        if user:
            user_achievements = UserAchievement.objects.filter(user=user).count()
            print(f"\nUser '{user.username}' has earned {user_achievements} achievements")
            
            # List their achievements
            if user_achievements > 0:
                print("\nEarned achievements:")
                for ua in UserAchievement.objects.filter(user=user)[:5]:
                    print(f"  - {ua.achievement.name} - earned on {ua.earned_at}")
        
        # Check if achievements need to be created
        if total_achievements == 0:
            print("\nNo achievements found! You need to create achievements first.")
            print("Run: python manage.py create_achievements")
        
    except Exception as e:
        import traceback
        print(f"Error checking achievements: {str(e)}")
        print(traceback.format_exc())

if __name__ == '__main__':
    check_achievements()