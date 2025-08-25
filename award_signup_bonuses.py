#!/usr/bin/env python
"""Award signup bonuses to existing users who don't have them yet"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.social_models import PointsHistory
from apps.users.points_service import PointsService

User = get_user_model()

def award_signup_bonuses():
    """Award signup bonuses to existing users"""
    print('Awarding signup bonuses to existing users...')
    
    # Get all users who don't have a signup bonus yet
    users_with_signup_bonus = PointsHistory.objects.filter(
        reason='signup_bonus'
    ).values_list('user_id', flat=True)
    
    users_without_bonus = User.objects.exclude(id__in=users_with_signup_bonus)
    
    print(f'Found {users_without_bonus.count()} users without signup bonus')
    
    awarded_count = 0
    for user in users_without_bonus:
        try:
            # Award signup bonus
            PointsService.award_points(
                user,
                'signup_bonus',
                description="Welcome to StartupHub! Thanks for joining our community."
            )
            awarded_count += 1
            print(f'Awarded signup bonus to {user.username}')
        except Exception as e:
            print(f'Failed to award bonus to {user.username}: {str(e)}')
    
    print(f'\nCompleted! Awarded signup bonuses to {awarded_count} users.')

if __name__ == '__main__':
    award_signup_bonuses()