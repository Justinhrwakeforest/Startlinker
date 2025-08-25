# apps/users/points_service.py - Points and Achievement Management Service
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .social_models import UserPoints, PointsHistory, Achievement, UserAchievement, UserAchievementProgress
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class PointsService:
    """Service for managing user points and achievements"""
    
    # Point values for different activities - Comprehensive workflow tracking
    POINT_VALUES = {
        # 🎯 ONBOARDING & PROFILE (5-50 points)
        'signup_bonus': 50,           # Account creation
        'email_verify': 15,           # Email verification
        'phone_verify': 20,           # Phone verification
        'profile_picture_upload': 10, # First profile picture
        'profile_bio_complete': 15,   # Adding bio
        'profile_location_add': 10,   # Adding location
        'profile_website_add': 15,    # Adding website
        'profile_complete': 30,       # Complete profile setup (bonus)
        'first_interests_select': 10, # Selecting first interests
        
        # 📱 ENGAGEMENT & LOGIN (2-25 points)
        'daily_login': 5,             # Daily login
        'login_streak_3': 10,         # 3-day streak
        'login_streak_7': 25,         # 7-day streak
        'login_streak_30': 100,       # 30-day streak
        'first_session': 5,           # First platform visit
        
        # 📝 CONTENT CREATION (10-75 points)
        'first_post': 75,             # First post (milestone)
        'post_create': 15,            # Regular post creation
        'post_with_image': 20,        # Post with image
        'post_with_video': 25,        # Post with video
        'first_story': 50,            # First story (milestone)
        'story_create': 10,           # Regular story creation
        'story_with_media': 15,       # Story with media
        'comment_create': 3,          # Creating comments
        'first_comment': 15,          # First comment (milestone)
        
        # 🚀 STARTUP ACTIVITIES (25-100 points)
        'first_startup_submit': 100,  # First startup submission (major milestone)
        'startup_submit': 35,         # Regular startup submission
        'startup_claim': 75,          # Claiming a startup
        'startup_verify': 50,         # Verifying claimed startup
        'startup_update': 10,         # Updating startup info
        'startup_logo_upload': 15,    # Adding startup logo
        
        # 💼 JOB ACTIVITIES (5-40 points)
        'first_job_post': 60,         # First job posting (milestone)
        'job_post': 25,               # Regular job posting
        'job_apply': 8,               # Applying for jobs
        'job_bookmark': 3,            # Bookmarking jobs
        'resume_upload': 20,          # Uploading resume
        'resume_update': 10,          # Updating resume
        
        # 🤝 SOCIAL ACTIVITIES (2-30 points)
        'first_follow': 25,           # First user follow (milestone)
        'follow_user': 3,             # Following users
        'get_followed': 5,            # Being followed by others
        'like_post': 2,               # Liking posts
        'share_post': 5,              # Sharing posts
        'bookmark_post': 3,           # Bookmarking posts
        'join_community': 15,         # Joining communities
        'message_send': 2,            # Sending messages
        'first_message': 20,          # First message sent
        
        # 🏆 ACHIEVEMENTS & MILESTONES (25-200 points)
        'achievement': 0,             # Variable based on achievement
        'milestone_10_posts': 50,     # 10 posts milestone
        'milestone_50_posts': 100,    # 50 posts milestone
        'milestone_100_followers': 75, # 100 followers milestone
        'milestone_verified': 40,     # Account verification milestone
        
        # 🎁 BONUSES & SPECIAL (50-500 points)
        'weekly_bonus': 75,           # Weekly activity bonus
        'monthly_bonus': 250,         # Monthly activity bonus
        'referral': 150,              # Referring new users
        'early_adopter': 500,         # Early platform adopter
        'beta_tester': 200,           # Beta testing participation
        'feedback_submit': 25,        # Submitting feedback
        'bug_report': 35,             # Reporting bugs
        
        # 🔥 STREAK & CONSISTENCY (10-150 points)
        'posting_streak_7': 40,       # 7-day posting streak
        'posting_streak_30': 120,     # 30-day posting streak
        'engagement_streak_7': 30,    # 7-day engagement streak
        'platform_anniversary': 100,  # Annual platform usage
        
        # 📊 SPECIAL CONTRIBUTIONS (20-100 points)
        'quality_content': 25,        # High-quality content recognition
        'helpful_comment': 15,        # Helpful community comment
        'mentor_activity': 50,        # Mentoring other users
        'event_participation': 40,    # Participating in events
        'survey_complete': 20,        # Completing surveys
    }
    
    @classmethod
    def award_points(cls, user, reason, points=None, description=None, **references):
        """Award points to user and check for achievements"""
        try:
            with transaction.atomic():
                # Get or create user points
                user_points = UserPoints.get_or_create_for_user(user)
                
                # Calculate points if not provided
                if points is None:
                    points = cls.POINT_VALUES.get(reason, 10)
                
                # Create description if not provided
                if description is None:
                    description = dict(PointsHistory.POINT_REASONS).get(reason, 'Activity completed')
                
                # Add points to user account
                user_points.add_points(points, cls._get_point_category(reason))
                
                # Create history record
                history = PointsHistory.objects.create(
                    user=user,
                    points=points,
                    reason=reason,
                    description=description,
                    **references
                )
                
                # Check for achievements
                cls._check_achievements_for_activity(user, reason, **references)
                
                logger.info(f"Awarded {points} points to {user.username} for {reason}")
                return history
                
        except Exception as e:
            logger.error(f"Error awarding points to {user.username}: {str(e)}")
            raise
    
    @classmethod
    def _get_point_category(cls, reason):
        """Map reason to point category"""
        category_mapping = {
            # Achievement category
            'achievement': 'achievement',
            
            # Content category
            'first_post': 'content',
            'post_create': 'content',
            'post_with_image': 'content',
            'post_with_video': 'content',
            'first_story': 'content',
            'story_create': 'content',
            'story_with_media': 'content',
            'comment_create': 'content',
            'first_comment': 'content',
            'quality_content': 'content',
            'helpful_comment': 'content',
            
            # Startup category
            'first_startup_submit': 'startup',
            'startup_submit': 'startup',
            'startup_claim': 'startup',
            'startup_verify': 'startup',
            'startup_update': 'startup',
            'startup_logo_upload': 'startup',
            
            # Job category
            'first_job_post': 'job',
            'job_post': 'job',
            'job_apply': 'job',
            'job_bookmark': 'job',
            'resume_upload': 'job',
            'resume_update': 'job',
            
            # Social category
            'signup_bonus': 'social',
            'email_verify': 'social',
            'phone_verify': 'social',
            'profile_picture_upload': 'social',
            'profile_bio_complete': 'social',
            'profile_location_add': 'social',
            'profile_website_add': 'social',
            'profile_complete': 'social',
            'first_interests_select': 'social',
            'daily_login': 'social',
            'login_streak_3': 'social',
            'login_streak_7': 'social',
            'login_streak_30': 'social',
            'first_session': 'social',
            'first_follow': 'social',
            'follow_user': 'social',
            'get_followed': 'social',
            'like_post': 'social',
            'share_post': 'social',
            'bookmark_post': 'social',
            'join_community': 'social',
            'message_send': 'social',
            'first_message': 'social',
            'milestone_100_followers': 'social',
            'milestone_verified': 'social',
            'referral': 'social',
            'mentor_activity': 'social',
            'posting_streak_7': 'social',
            'posting_streak_30': 'social',
            'engagement_streak_7': 'social',
            'platform_anniversary': 'social',
        }
        return category_mapping.get(reason, 'general')
    
    @classmethod
    def _check_achievements_for_activity(cls, user, reason, **references):
        """Check if user qualifies for any achievements based on activity"""
        try:
            # Import here to avoid circular imports
            from .social_tasks import (
                check_profile_achievements, check_social_achievements,
                check_content_achievements, check_startup_achievements
            )
            
            # Map activities to achievement checks
            if reason in ['profile_complete']:
                check_profile_achievements.delay(user.id)
            elif reason in ['follow_user']:
                check_social_achievements.delay(user.id)
            elif reason in ['post_create', 'story_create']:
                check_content_achievements.delay(user.id)
            elif reason in ['startup_submit', 'startup_claim']:
                check_startup_achievements.delay(user.id)
                
            # Always check level-based achievements
            cls._check_level_achievements(user)
            
        except Exception as e:
            logger.error(f"Error checking achievements for {user.username}: {str(e)}")
    
    @classmethod
    def _check_level_achievements(cls, user):
        """Check for level-based achievements"""
        try:
            user_points = UserPoints.get_or_create_for_user(user)
            current_level = user_points.level
            
            # Level-based achievements
            level_achievements = [
                (5, 'level-5', 'Level 5 Achiever', 'Reached Level 5'),
                (10, 'level-10', 'Level 10 Master', 'Reached Level 10'),
                (25, 'level-25', 'Level 25 Expert', 'Reached Level 25'),
                (50, 'level-50', 'Level 50 Legendary', 'Reached Level 50'),
            ]
            
            for required_level, slug, name, description in level_achievements:
                if current_level >= required_level:
                    # Check if user already has this achievement
                    achievement = Achievement.objects.filter(slug=slug).first()
                    if achievement and not UserAchievement.objects.filter(
                        user=user, achievement=achievement
                    ).exists():
                        # Award the achievement
                        UserAchievement.objects.create(
                            user=user,
                            achievement=achievement,
                            progress_data={'level_reached': current_level}
                        )
                        
                        # Award achievement points
                        cls.award_points(
                            user, 
                            'achievement', 
                            points=achievement.points,
                            description=f"Achievement Unlocked: {achievement.name}",
                            achievement=achievement
                        )
                        
        except Exception as e:
            logger.error(f"Error checking level achievements for {user.username}: {str(e)}")
    
    @classmethod
    def check_and_unlock_achievements(cls, user):
        """Comprehensive achievement check for a user - uses Celery tasks for real-time processing"""
        try:
            # Import here to avoid circular imports
            from .social_tasks import (
                check_profile_achievements, check_social_achievements,
                check_content_achievements, check_startup_achievements
            )
            
            # Use asynchronous tasks for real-time processing
            check_profile_achievements.delay(user.id)
            check_social_achievements.delay(user.id)
            check_content_achievements.delay(user.id)
            check_startup_achievements.delay(user.id)
            
            # Also check level-based achievements immediately
            unlocked_count = cls._check_level_achievements(user)
            
            logger.info(f"Queued comprehensive achievement check for {user.username}")
            return unlocked_count
            
        except Exception as e:
            logger.error(f"Error checking achievements for {user.username}: {str(e)}")
            return 0
    
    @classmethod
    def _check_achievement_requirements(cls, user, achievement, stats):
        """Check if user meets achievement requirements"""
        requirements = achievement.requirements
        if not requirements:
            return False
        
        # Check each requirement
        for key, required_value in requirements.items():
            if key in stats:
                if stats[key] < required_value:
                    return False
            elif key == 'profile_completion':
                # Calculate profile completion percentage
                completion = cls._calculate_profile_completion(user)
                if completion < required_value:
                    return False
            elif key == 'verification':
                # Check if user is verified
                if not (user.email_verified and getattr(user, 'phone_verified', True)):
                    return False
            elif key == 'join_date':
                # Check join date requirements
                if required_value == 'early' and user.date_joined > timezone.now() - timezone.timedelta(days=90):
                    return False
            elif key == 'night_activity':
                # Check for night activity (simplified)
                return True  # Simplified for now
            elif key == 'consecutive_days':
                # Check consecutive login days (simplified)
                return True  # Simplified for now
        
        return True
    
    @classmethod
    def _calculate_profile_completion(cls, user):
        """Calculate profile completion percentage"""
        fields_to_check = [
            user.first_name,
            user.last_name,
            getattr(user, 'bio', None),
            getattr(user, 'location', None),
            getattr(user, 'profile_picture', None),
            getattr(user, 'website', None),
        ]
        
        completed_fields = sum(1 for field in fields_to_check if field)
        return (completed_fields / len(fields_to_check)) * 100
    
    @classmethod
    def get_user_leaderboard(cls, limit=50):
        """Get top users by points"""
        return UserPoints.objects.select_related('user').order_by('-total_points')[:limit]
    
    @classmethod
    def get_user_rank(cls, user):
        """Get user's rank in leaderboard"""
        user_points = UserPoints.get_or_create_for_user(user)
        rank = UserPoints.objects.filter(total_points__gt=user_points.total_points).count() + 1
        return rank