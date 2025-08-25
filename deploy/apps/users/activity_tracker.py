# apps/users/activity_tracker.py - Comprehensive Activity Tracking System
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .points_service import PointsService
from .social_models import UserPoints, PointsHistory
# Import will be done inside methods to avoid circular imports
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ActivityTracker:
    """
    Comprehensive activity tracking system that automatically awards points
    for user activities throughout the platform workflow.
    """
    
    @classmethod
    def track_signup(cls, user):
        """Track user signup and award welcome bonus"""
        try:
            # Award signup bonus
            PointsService.award_points(
                user=user,
                reason='signup_bonus',
                description=f'Welcome to the platform! Here are your first {PointsService.POINT_VALUES["signup_bonus"]} points.'
            )
            
            # Award first session points
            cls.track_first_session(user)
            
            # Check for achievements related to signup
            try:
                from .achievement_tracker import AchievementTracker
                AchievementTracker.track_activity_achievement(user, 'signup_bonus')
            except ImportError:
                pass  # Achievement tracker not available
            
            logger.info(f"Tracked signup for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking signup for {user.username}: {str(e)}")
            return False
    
    @classmethod
    def track_first_session(cls, user):
        """Track user's first platform visit"""
        try:
            # Check if this is truly the first session
            if not PointsHistory.objects.filter(user=user, reason='first_session').exists():
                PointsService.award_points(
                    user=user,
                    reason='first_session',
                    description='First platform visit - great to have you here!'
                )
                
                # Check for achievements
                try:
                    from .achievement_tracker import AchievementTracker
                    AchievementTracker.track_activity_achievement(user, 'first_session')
                except ImportError:
                    pass
                logger.info(f"Tracked first session for user: {user.username}")
            
        except Exception as e:
            logger.error(f"Error tracking first session for {user.username}: {str(e)}")
    
    @classmethod
    def track_profile_activity(cls, user, activity_type, field_name=None):
        """Track profile-related activities"""
        activity_mapping = {
            'email_verify': 'Email verification completed',
            'phone_verify': 'Phone number verified',
            'profile_picture_upload': 'Profile picture uploaded',
            'profile_bio_complete': 'Bio added to profile',
            'profile_location_add': 'Location added to profile',
            'profile_website_add': 'Website added to profile',
            'first_interests_select': 'Interests selected',
        }
        
        try:
            # Check if this activity has already been rewarded
            if not PointsHistory.objects.filter(user=user, reason=activity_type).exists():
                description = activity_mapping.get(activity_type, f'Profile activity: {activity_type}')
                
                PointsService.award_points(
                    user=user,
                    reason=activity_type,
                    description=description
                )
                
                logger.info(f"Tracked profile activity '{activity_type}' for user: {user.username}")
                
                # Check for achievements
                try:
                    from .achievement_tracker import AchievementTracker
                    AchievementTracker.track_activity_achievement(user, activity_type)
                except ImportError:
                    pass
                
                # Check if profile is now complete
                cls._check_complete_profile(user)
            
        except Exception as e:
            logger.error(f"Error tracking profile activity for {user.username}: {str(e)}")
    
    @classmethod
    def track_content_creation(cls, user, content_type, has_media=False, is_first=False):
        """Track content creation activities"""
        try:
            if content_type == 'post':
                if is_first or not PointsHistory.objects.filter(user=user, reason='first_post').exists():
                    # Award first post bonus
                    PointsService.award_points(
                        user=user,
                        reason='first_post',
                        description='Congratulations on your first post! Keep sharing your thoughts.'
                    )
                    
                    # Check for achievements
                    try:
                        from .achievement_tracker import AchievementTracker
                        AchievementTracker.track_activity_achievement(user, 'first_post')
                    except ImportError:
                        pass
                else:
                    # Regular post creation
                    reason = 'post_create'
                    if has_media:
                        reason = 'post_with_image' if 'image' in str(has_media).lower() else 'post_with_video'
                    
                    PointsService.award_points(
                        user=user,
                        reason=reason,
                        description=f'Post created{" with media" if has_media else ""}'
                    )
                    
                    # Check for achievements
                    try:
                        from .achievement_tracker import AchievementTracker
                        AchievementTracker.track_activity_achievement(user, reason)
                    except ImportError:
                        pass
                
            elif content_type == 'story':
                if is_first or not PointsHistory.objects.filter(user=user, reason='first_story').exists():
                    # Award first story bonus
                    PointsService.award_points(
                        user=user,
                        reason='first_story',
                        description='Your first story! Stories are a great way to share quick updates.'
                    )
                else:
                    # Regular story creation
                    reason = 'story_create'
                    if has_media:
                        reason = 'story_with_media'
                    
                    PointsService.award_points(
                        user=user,
                        reason=reason,
                        description=f'Story created{" with media" if has_media else ""}'
                    )
            
            elif content_type == 'comment':
                if is_first or not PointsHistory.objects.filter(user=user, reason='first_comment').exists():
                    # Award first comment bonus
                    PointsService.award_points(
                        user=user,
                        reason='first_comment',
                        description='Your first comment! Engaging with the community is awesome.'
                    )
                else:
                    # Regular comment
                    PointsService.award_points(
                        user=user,
                        reason='comment_create',
                        description='Comment added to discussion'
                    )
            
            # Check content milestones
            cls._check_content_milestones(user)
            
            logger.info(f"Tracked {content_type} creation for user: {user.username}")
            
        except Exception as e:
            logger.error(f"Error tracking content creation for {user.username}: {str(e)}")
    
    @classmethod
    def track_startup_activity(cls, user, activity_type, startup_name=None):
        """Track startup-related activities"""
        activity_descriptions = {
            'first_startup_submit': f'First startup submitted: {startup_name}! Welcome to the startup community.',
            'startup_submit': f'Startup submitted: {startup_name}',
            'startup_claim': f'Startup claimed: {startup_name}',
            'startup_verify': f'Startup verified: {startup_name}',
            'startup_update': f'Startup updated: {startup_name}',
            'startup_logo_upload': f'Logo uploaded for: {startup_name}',
        }
        
        try:
            # Check for first startup submission
            if activity_type == 'startup_submit':
                if not PointsHistory.objects.filter(user=user, reason__in=['first_startup_submit', 'startup_submit']).exists():
                    activity_type = 'first_startup_submit'
            
            description = activity_descriptions.get(activity_type, f'Startup activity: {activity_type}')
            
            PointsService.award_points(
                user=user,
                reason=activity_type,
                description=description
            )
            
            logger.info(f"Tracked startup activity '{activity_type}' for user: {user.username}")
            
        except Exception as e:
            logger.error(f"Error tracking startup activity for {user.username}: {str(e)}")
    
    @classmethod
    def track_job_activity(cls, user, activity_type, job_title=None):
        """Track job-related activities"""
        activity_descriptions = {
            'first_job_post': f'First job posted: {job_title}! Thanks for adding opportunities.',
            'job_post': f'Job posted: {job_title}',
            'job_apply': f'Applied for job: {job_title}',
            'job_bookmark': f'Job bookmarked: {job_title}',
            'resume_upload': 'Resume uploaded to profile',
            'resume_update': 'Resume updated',
        }
        
        try:
            # Check for first job posting
            if activity_type == 'job_post':
                if not PointsHistory.objects.filter(user=user, reason__in=['first_job_post', 'job_post']).exists():
                    activity_type = 'first_job_post'
            
            description = activity_descriptions.get(activity_type, f'Job activity: {activity_type}')
            
            PointsService.award_points(
                user=user,
                reason=activity_type,
                description=description
            )
            
            logger.info(f"Tracked job activity '{activity_type}' for user: {user.username}")
            
        except Exception as e:
            logger.error(f"Error tracking job activity for {user.username}: {str(e)}")
    
    @classmethod
    def track_social_activity(cls, user, activity_type, target_user=None, post_id=None):
        """Track social interaction activities"""
        try:
            descriptions = {
                'first_follow': f'First user followed: @{target_user.username if target_user else "someone"}! Building your network.',
                'follow_user': f'Followed @{target_user.username if target_user else "someone"}',
                'get_followed': f'Gained a new follower! Your profile is attracting attention.',
                'like_post': 'Post liked',
                'share_post': 'Post shared with network',
                'bookmark_post': 'Post bookmarked for later',
                'message_send': f'Message sent to @{target_user.username if target_user else "someone"}',
                'first_message': f'First message sent to @{target_user.username if target_user else "someone"}! Great for networking.',
            }
            
            # Check for first-time activities
            if activity_type == 'follow_user':
                if not PointsHistory.objects.filter(user=user, reason__in=['first_follow', 'follow_user']).exists():
                    activity_type = 'first_follow'
            elif activity_type == 'message_send':
                if not PointsHistory.objects.filter(user=user, reason__in=['first_message', 'message_send']).exists():
                    activity_type = 'first_message'
            
            description = descriptions.get(activity_type, f'Social activity: {activity_type}')
            
            PointsService.award_points(
                user=user,
                reason=activity_type,
                description=description,
                post_id=post_id
            )
            
            # Check social milestones
            if activity_type in ['follow_user', 'first_follow']:
                cls._check_social_milestones(user)
            
            logger.info(f"Tracked social activity '{activity_type}' for user: {user.username}")
            
        except Exception as e:
            logger.error(f"Error tracking social activity for {user.username}: {str(e)}")
    
    @classmethod
    def track_login(cls, user):
        """Track daily login and streaks"""
        try:
            today = timezone.now().date()
            
            # Check if already logged in today
            if not PointsHistory.objects.filter(
                user=user, 
                reason='daily_login',
                created_at__date=today
            ).exists():
                PointsService.award_points(
                    user=user,
                    reason='daily_login',
                    description=f'Daily login bonus for {today.strftime("%B %d, %Y")}'
                )
                
                # Check login streaks
                cls._check_login_streaks(user)
                
                logger.info(f"Tracked daily login for user: {user.username}")
            
        except Exception as e:
            logger.error(f"Error tracking login for {user.username}: {str(e)}")
    
    @classmethod
    def _check_complete_profile(cls, user):
        """Check if profile is complete and award bonus"""
        try:
            # Calculate profile completion
            completion_percentage = PointsService._calculate_profile_completion(user)
            
            if completion_percentage >= 80 and not PointsHistory.objects.filter(
                user=user, reason='profile_complete'
            ).exists():
                PointsService.award_points(
                    user=user,
                    reason='profile_complete',
                    description='Profile completed! You look professional and ready to network.'
                )
                
        except Exception as e:
            logger.error(f"Error checking profile completion for {user.username}: {str(e)}")
    
    @classmethod
    def _check_content_milestones(cls, user):
        """Check content creation milestones"""
        try:
            # Count user's posts
            from apps.posts.models import Post
            post_count = Post.objects.filter(author=user, is_approved=True).count()
            
            milestones = [
                (10, 'milestone_10_posts', '10 posts milestone reached!'),
                (50, 'milestone_50_posts', '50 posts milestone - you are a content creator!'),
            ]
            
            for count, reason, description in milestones:
                if post_count >= count and not PointsHistory.objects.filter(
                    user=user, reason=reason
                ).exists():
                    PointsService.award_points(
                        user=user,
                        reason=reason,
                        description=description
                    )
                    
        except Exception as e:
            logger.error(f"Error checking content milestones for {user.username}: {str(e)}")
    
    @classmethod
    def _check_social_milestones(cls, user):
        """Check social interaction milestones"""
        try:
            from .social_models import UserFollow
            follower_count = UserFollow.objects.filter(following=user).count()
            
            if follower_count >= 100 and not PointsHistory.objects.filter(
                user=user, reason='milestone_100_followers'
            ).exists():
                PointsService.award_points(
                    user=user,
                    reason='milestone_100_followers',
                    description='100 followers milestone! You are building a strong network.'
                )
                
        except Exception as e:
            logger.error(f"Error checking social milestones for {user.username}: {str(e)}")
    
    @classmethod
    def _check_login_streaks(cls, user):
        """Check and award login streak bonuses"""
        try:
            # Get recent login history
            recent_logins = PointsHistory.objects.filter(
                user=user,
                reason='daily_login'
            ).order_by('-created_at')[:30]
            
            if len(recent_logins) < 3:
                return
            
            # Check for consecutive days
            login_dates = [login.created_at.date() for login in recent_logins]
            consecutive_days = cls._count_consecutive_dates(login_dates)
            
            # Award streak bonuses (only once per streak)
            if consecutive_days >= 30:
                if not PointsHistory.objects.filter(
                    user=user, 
                    reason='login_streak_30',
                    created_at__gte=timezone.now() - timezone.timedelta(days=35)
                ).exists():
                    PointsService.award_points(
                        user=user,
                        reason='login_streak_30',
                        description='30-day login streak! Your dedication is impressive.'
                    )
            elif consecutive_days >= 7:
                if not PointsHistory.objects.filter(
                    user=user, 
                    reason='login_streak_7',
                    created_at__gte=timezone.now() - timezone.timedelta(days=10)
                ).exists():
                    PointsService.award_points(
                        user=user,
                        reason='login_streak_7',
                        description='7-day login streak! Keep up the consistency.'
                    )
            elif consecutive_days >= 3:
                if not PointsHistory.objects.filter(
                    user=user, 
                    reason='login_streak_3',
                    created_at__gte=timezone.now() - timezone.timedelta(days=5)
                ).exists():
                    PointsService.award_points(
                        user=user,
                        reason='login_streak_3',
                        description='3-day login streak! Building great habits.'
                    )
                    
        except Exception as e:
            logger.error(f"Error checking login streaks for {user.username}: {str(e)}")
    
    @classmethod
    def _count_consecutive_dates(cls, dates):
        """Count consecutive dates in a list"""
        if not dates:
            return 0
        
        dates = sorted(dates, reverse=True)  # Most recent first
        consecutive = 1
        
        for i in range(1, len(dates)):
            expected_date = dates[i-1] - timezone.timedelta(days=1)
            if dates[i] == expected_date:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    @classmethod
    def track_milestone(cls, user, milestone_type, description=None):
        """Track special milestones and achievements"""
        try:
            milestone_descriptions = {
                'milestone_verified': 'Account fully verified! You are now a trusted member.',
                'early_adopter': 'Early adopter bonus! Thanks for joining us early.',
                'beta_tester': 'Beta tester bonus! Thanks for helping us improve.',
                'platform_anniversary': 'Happy platform anniversary! Thanks for being with us.',
            }
            
            if not description:
                description = milestone_descriptions.get(milestone_type, f'Milestone achieved: {milestone_type}')
            
            # Check if milestone already awarded
            if not PointsHistory.objects.filter(user=user, reason=milestone_type).exists():
                PointsService.award_points(
                    user=user,
                    reason=milestone_type,
                    description=description
                )
                
                logger.info(f"Tracked milestone '{milestone_type}' for user: {user.username}")
                
        except Exception as e:
            logger.error(f"Error tracking milestone for {user.username}: {str(e)}")
    
    @classmethod
    def get_user_activity_summary(cls, user, days=30):
        """Get user's recent activity summary"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            since_date = timezone.now() - timedelta(days=days)
            
            recent_activities = PointsHistory.objects.filter(
                user=user,
                created_at__gte=since_date
            ).order_by('-created_at')
            
            summary = {
                'total_points_earned': sum(activity.points for activity in recent_activities if activity.points > 0),
                'total_activities': recent_activities.count(),
                'activity_breakdown': {},
                'recent_activities': recent_activities[:10]
            }
            
            # Group by activity type
            for activity in recent_activities:
                reason = activity.reason
                if reason not in summary['activity_breakdown']:
                    summary['activity_breakdown'][reason] = {
                        'count': 0,
                        'points': 0,
                        'description': activity.get_reason_display()
                    }
                summary['activity_breakdown'][reason]['count'] += 1
                summary['activity_breakdown'][reason]['points'] += activity.points
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting activity summary for {user.username}: {str(e)}")
            return {}