# apps/users/achievement_tracker.py - Activity-based Achievement Tracking System
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from .social_models import Achievement, UserAchievement, UserAchievementProgress, PointsHistory, UserPoints
from .points_service import PointsService
from apps.posts.models import Post
from apps.startups.models import Startup
from apps.jobs.models import Job
import logging
from datetime import datetime, timedelta

User = get_user_model()
logger = logging.getLogger(__name__)

class AchievementTracker:
    """
    Activity-based achievement tracking system that monitors user activities
    and automatically unlocks achievements when goals are met.
    """
    
    @classmethod
    def check_and_unlock_achievements(cls, user, activity_type=None):
        """
        Check all achievements for a user and unlock any that are now earned.
        Can be called after specific activities or as a general check.
        """
        try:
            with transaction.atomic():
                # Get all active achievements that the user hasn't earned yet
                earned_achievement_ids = UserAchievement.objects.filter(
                    user=user
                ).values_list('achievement_id', flat=True)
                
                achievements_to_check = Achievement.objects.filter(
                    is_active=True
                ).exclude(id__in=earned_achievement_ids)
                
                # If specific activity type provided, filter relevant achievements
                if activity_type:
                    achievements_to_check = cls._filter_achievements_by_activity(
                        achievements_to_check, activity_type
                    )
                
                unlocked_achievements = []
                
                for achievement in achievements_to_check:
                    if cls._check_achievement_requirements(user, achievement):
                        # Unlock the achievement
                        user_achievement = cls._unlock_achievement(user, achievement)
                        if user_achievement:
                            unlocked_achievements.append(user_achievement)
                
                # Log results
                if unlocked_achievements:
                    logger.info(f"Unlocked {len(unlocked_achievements)} achievements for {user.username}")
                    
                return unlocked_achievements
                
        except Exception as e:
            logger.error(f"Error checking achievements for {user.username}: {str(e)}")
            return []
    
    @classmethod
    def _filter_achievements_by_activity(cls, achievements, activity_type):
        """Filter achievements that might be relevant to a specific activity"""
        activity_category_map = {
            'signup_bonus': ['profile'],
            'email_verify': ['profile'],
            'profile_picture_upload': ['profile'],
            'profile_complete': ['profile'],
            'first_post': ['content', 'social'],
            'post_create': ['content', 'social'],
            'first_follow': ['social', 'networking'],
            'follow_user': ['social', 'networking'],
            'first_startup_submit': ['startup'],
            'startup_submit': ['startup'],
            'first_job_post': ['jobs'],
            'job_post': ['jobs'],
            'daily_login': ['social'],
            'login_streak_3': ['social'],
            'login_streak_7': ['social'],
            'login_streak_30': ['social'],
        }
        
        relevant_categories = activity_category_map.get(activity_type, [])
        if relevant_categories:
            return achievements.filter(category__in=relevant_categories)
        
        return achievements
    
    @classmethod
    def _check_achievement_requirements(cls, user, achievement):
        """Check if user meets all requirements for an achievement"""
        try:
            requirements = achievement.requirements
            
            # Handle different requirement types
            if 'activity_count' in requirements:
                return cls._check_activity_count_requirement(user, requirements)
            elif 'points_total' in requirements:
                return cls._check_points_requirement(user, requirements)
            elif 'consecutive_days' in requirements:
                return cls._check_consecutive_days_requirement(user, requirements)
            elif 'multiple_conditions' in requirements:
                return cls._check_multiple_conditions(user, requirements)
            else:
                # Legacy or simple requirements
                return cls._check_legacy_requirements(user, requirements)
                
        except Exception as e:
            logger.error(f"Error checking requirements for achievement {achievement.name}: {str(e)}")
            return False
    
    @classmethod
    def _check_activity_count_requirement(cls, user, requirements):
        """Check if user has performed enough of a specific activity"""
        activity_type = requirements['activity_count']['type']
        required_count = requirements['activity_count']['count']
        
        # Get actual count from PointsHistory
        actual_count = PointsHistory.objects.filter(
            user=user,
            reason=activity_type
        ).count()
        
        return actual_count >= required_count
    
    @classmethod
    def _check_points_requirement(cls, user, requirements):
        """Check if user has enough points"""
        required_points = requirements['points_total']
        user_points = UserPoints.get_or_create_for_user(user)
        
        return user_points.total_points >= required_points
    
    @classmethod
    def _check_consecutive_days_requirement(cls, user, requirements):
        """Check consecutive days requirement (like login streaks)"""
        activity_type = requirements['consecutive_days']['type']
        required_days = requirements['consecutive_days']['days']
        
        # Get recent activities of this type
        recent_activities = PointsHistory.objects.filter(
            user=user,
            reason=activity_type
        ).order_by('-created_at')[:required_days]
        
        if len(recent_activities) < required_days:
            return False
        
        # Check if they're consecutive days
        dates = [activity.created_at.date() for activity in recent_activities]
        dates.reverse()  # Oldest first
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days != 1:
                return False
        
        return True
    
    @classmethod
    def _check_multiple_conditions(cls, user, requirements):
        """Check multiple conditions that must all be true"""
        conditions = requirements['multiple_conditions']
        
        for condition in conditions:
            logger.debug(f"Checking condition: {condition}")
            if condition['type'] == 'activity_count':
                activity_type = condition['activity_type']
                required_count = condition['required']
                
                actual_count = PointsHistory.objects.filter(
                    user=user,
                    reason=activity_type
                ).count()
                
                if actual_count < required_count:
                    return False
                    
            elif condition['type'] == 'points_category':
                user_points = UserPoints.get_or_create_for_user(user)
                category_points = getattr(user_points, f"{condition['category']}_points", 0)
                if category_points < condition['required']:
                    return False
                    
            elif condition['type'] == 'profile_complete':
                if not cls._check_profile_completion(user):
                    return False
        
        return True
    
    @classmethod
    def _check_legacy_requirements(cls, user, requirements):
        """Handle legacy or simple requirement formats"""
        # Simple post count check
        if 'posts' in requirements:
            post_count = Post.objects.filter(author=user).count()
            return post_count >= requirements['posts']
        
        # Simple follower count check
        if 'followers' in requirements:
            from .social_models import UserFollow
            follower_count = UserFollow.objects.filter(following=user).count()
            return follower_count >= requirements['followers']
        
        # Points requirement
        if 'points' in requirements:
            user_points = UserPoints.get_or_create_for_user(user)
            return user_points.total_points >= requirements['points']
        
        return False
    
    @classmethod
    def _check_profile_completion(cls, user):
        """Check if user profile is complete"""
        required_fields = ['first_name', 'last_name', 'email']
        
        for field in required_fields:
            if not getattr(user, field, None):
                return False
        
        # Check if profile picture exists
        if not getattr(user, 'profile_picture', None):
            return False
            
        return True
    
    @classmethod
    def _unlock_achievement(cls, user, achievement):
        """Unlock an achievement for a user"""
        try:
            # Create the user achievement record
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement,
                defaults={
                    'earned_at': timezone.now(),
                    'progress_data': cls._get_current_progress_data(user, achievement),
                }
            )
            
            if created:
                # Award points for the achievement
                PointsService.award_points(
                    user=user,
                    reason='achievement',
                    points=achievement.points,
                    description=f'Achievement unlocked: {achievement.name}'
                )
                
                # Update achievement earned count
                achievement.earned_count += 1
                achievement.save(update_fields=['earned_count'])
                
                # Mark any progress tracking as completed
                UserAchievementProgress.objects.filter(
                    user=user,
                    achievement=achievement
                ).update(
                    is_completed=True,
                    completed_at=timezone.now(),
                    progress_percentage=100.0
                )
                
                logger.info(f"Achievement '{achievement.name}' unlocked for {user.username}")
                return user_achievement
            
        except Exception as e:
            logger.error(f"Error unlocking achievement {achievement.name} for {user.username}: {str(e)}")
            
        return None
    
    @classmethod
    def _get_current_progress_data(cls, user, achievement):
        """Get current progress data when achievement is unlocked"""
        user_points = UserPoints.get_or_create_for_user(user)
        
        return {
            'total_points': user_points.total_points,
            'level': user_points.level,
            'unlock_timestamp': timezone.now().isoformat(),
            'activity_counts': cls._get_activity_counts(user)
        }
    
    @classmethod
    def _get_activity_counts(cls, user):
        """Get summary of user's activity counts"""
        return {
            'posts': Post.objects.filter(author=user).count(),
            'total_activities': PointsHistory.objects.filter(user=user).count(),
            'points_by_category': {
                'content': user.points.content_points if hasattr(user, 'points') else 0,
                'social': user.points.social_points if hasattr(user, 'points') else 0,
                'startup': user.points.startup_points if hasattr(user, 'points') else 0,
                'job': user.points.job_points if hasattr(user, 'points') else 0,
            }
        }
    
    @classmethod
    def update_progress(cls, user, achievement, current_value, max_value):
        """Update progress towards an achievement"""
        try:
            progress, created = UserAchievementProgress.objects.get_or_create(
                user=user,
                achievement=achievement,
                defaults={
                    'current_progress': {'value': current_value, 'max': max_value},
                    'progress_percentage': min(100.0, (current_value / max_value) * 100)
                }
            )
            
            if not created:
                progress.current_progress = {'value': current_value, 'max': max_value}
                progress.progress_percentage = min(100.0, (current_value / max_value) * 100)
                progress.save()
            
            return progress
            
        except Exception as e:
            logger.error(f"Error updating progress for {achievement.name}: {str(e)}")
            return None
    
    @classmethod
    def track_activity_achievement(cls, user, activity_type, **kwargs):
        """
        Track an activity and check for related achievements.
        This should be called from activity_tracker.py after awarding points.
        """
        try:
            # Check achievements related to this activity
            unlocked = cls.check_and_unlock_achievements(user, activity_type)
            
            # Update progress for relevant achievements
            cls._update_relevant_progress(user, activity_type, **kwargs)
            
            return unlocked
            
        except Exception as e:
            logger.error(f"Error tracking activity achievement: {str(e)}")
            return []
    
    @classmethod
    def _update_relevant_progress(cls, user, activity_type, **kwargs):
        """Update progress for achievements related to this activity"""
        try:
            # Get user's current activity counts for progress tracking
            activity_counts = {
                'posts': Post.objects.filter(author=user).count(),
                'login_streak': cls._get_current_login_streak(user),
                'total_points': UserPoints.get_or_create_for_user(user).total_points,
            }
            
            # Update progress for all active achievements
            achievements = Achievement.objects.filter(is_active=True)
            for achievement in achievements:
                if achievement.requirements:
                    cls._update_achievement_progress(user, achievement, activity_counts)
                    
        except Exception as e:
            logger.error(f"Error updating relevant progress: {str(e)}")
    
    @classmethod
    def _update_achievement_progress(cls, user, achievement, activity_counts):
        """Update progress for a specific achievement"""
        try:
            requirements = achievement.requirements
            
            if 'activity_count' in requirements:
                activity_type = requirements['activity_count']['type']
                required_count = requirements['activity_count']['count']
                
                current_count = PointsHistory.objects.filter(
                    user=user,
                    reason=activity_type
                ).count()
                
                cls.update_progress(user, achievement, current_count, required_count)
                
            elif 'points_total' in requirements:
                required_points = requirements['points_total']
                current_points = activity_counts['total_points']
                
                cls.update_progress(user, achievement, current_points, required_points)
                
        except Exception as e:
            logger.error(f"Error updating achievement progress: {str(e)}")
    
    @classmethod
    def _get_current_login_streak(cls, user):
        """Calculate current login streak"""
        try:
            login_activities = PointsHistory.objects.filter(
                user=user,
                reason='daily_login'
            ).order_by('-created_at')
            
            if not login_activities:
                return 0
            
            streak = 1
            current_date = login_activities[0].created_at.date()
            
            for activity in login_activities[1:]:
                activity_date = activity.created_at.date()
                if (current_date - activity_date).days == 1:
                    streak += 1
                    current_date = activity_date
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating login streak: {str(e)}")
            return 0