# apps/users/signals.py - Django signals for achievement and points system
import logging
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger(__name__)

def safe_celery_task(task_func, *args, **kwargs):
    """Safely execute Celery task, fallback to sync execution if broker unavailable"""
    try:
        # Try to execute as Celery task
        return task_func.delay(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Celery task {task_func.__name__} failed, skipping: {e}")
        try:
            # Fallback to direct execution if available
            return task_func(*args, **kwargs)
        except Exception as e2:
            logger.warning(f"Direct execution of {task_func.__name__} also failed: {e2}")
            pass

from .social_models import UserFollow, Story, StartupCollaboration
from .social_tasks import (
    check_profile_achievements, check_social_achievements, 
    check_content_achievements, update_achievement_progress,
    check_startup_achievements
)
from .points_service import PointsService
from apps.posts.models import Post
from apps.startups.models import Startup
from apps.jobs.models import Job, JobApplication

User = get_user_model()

@receiver(post_save, sender=User)
def handle_user_signup_and_profile(sender, instance, created, **kwargs):
    """Handle signup bonus and profile achievements"""
    if created:
        # Award signup bonus for new users
        try:
            PointsService.award_points(
                instance,
                'signup_bonus',
                description="Welcome to StartupHub! Thanks for joining our community."
            )
        except Exception as e:
            pass  # Log error but don't fail user creation
    else:
        # Check profile achievements on updates
        transaction.on_commit(
            lambda: safe_celery_task(check_profile_achievements, instance.id)
        )

@receiver(post_save, sender=UserFollow)
def check_follow_achievements(sender, instance, created, **kwargs):
    """Check social achievements and award points when user follows/unfollows"""
    if created:
        # Award points for following someone
        try:
            PointsService.award_points(
                instance.follower,
                'follow_user',
                description=f"Followed {instance.following.get_display_name() if hasattr(instance.following, 'get_display_name') else instance.following.username}"
            )
        except Exception as e:
            pass  # Log error but don't fail the operation
        
        # Check achievements for both follower and following
        transaction.on_commit(
            lambda: safe_celery_task(check_social_achievements, instance.follower.id)
        )
        transaction.on_commit(
            lambda: safe_celery_task(check_social_achievements, instance.following.id)
        )

@receiver(post_delete, sender=UserFollow)
def recheck_follow_achievements_on_unfollow(sender, instance, **kwargs):
    """Recheck achievements when unfollow happens (shouldn't remove achievements but updates progress)"""
    transaction.on_commit(
        lambda: safe_celery_task(check_social_achievements, instance.follower.id)
    )
    transaction.on_commit(
        lambda: safe_celery_task(check_social_achievements, instance.following.id)
    )

@receiver(post_save, sender=Post)
def check_content_achievements_on_post(sender, instance, created, **kwargs):
    """Check content achievements and award points when user creates a post"""
    if created and instance.is_approved:
        # Check if this is the user's first post
        is_first_post = Post.objects.filter(author=instance.author, is_approved=True).count() == 1
        
        # Award points for creating a post
        try:
            PointsService.award_points(
                instance.author,
                'post_create',
                description=f"Created post: {instance.title[:50] if instance.title else 'Untitled'}",
                post_id=instance.id
            )
            
            # Award extra points for first post
            if is_first_post:
                PointsService.award_points(
                    instance.author,
                    'first_post',
                    description="Congratulations on your first post! Welcome to the community.",
                    post_id=instance.id
                )
        except Exception as e:
            pass  # Log error but don't fail the operation
        
        transaction.on_commit(
            lambda: safe_celery_task(check_content_achievements, instance.author.id)
        )

@receiver(post_save, sender=Story)
def check_story_achievements(sender, instance, created, **kwargs):
    """Check achievements and award points when user creates a story"""
    if created:
        # Award points for creating a story
        try:
            PointsService.award_points(
                instance.author,
                'story_create',
                description="Created a story"
            )
        except Exception as e:
            pass  # Log error but don't fail the operation
        
        transaction.on_commit(
            lambda: safe_celery_task(check_content_achievements, instance.author.id)
        )

@receiver(post_save, sender=StartupCollaboration)
def check_collaboration_achievements(sender, instance, created, **kwargs):
    """Check collaboration-related achievements"""
    if created:
        # Check curator achievements
        transaction.on_commit(
            lambda: safe_celery_task(update_achievement_progress,
                instance.owner.id,
                'curator',
                {'collaborations_created': 1}
            )
        )

@receiver(post_save, sender=Startup)
def check_startup_achievements_signal(sender, instance, created, **kwargs):
    """Check startup achievements and award points when startup is created/updated"""
    if created and instance.submitted_by:
        # Award points for submitting a startup
        try:
            PointsService.award_points(
                instance.submitted_by,
                'startup_submit',
                description=f"Submitted startup: {instance.name}",
                startup_id=instance.id
            )
        except Exception as e:
            pass  # Log error but don't fail the operation
        
        transaction.on_commit(
            lambda: safe_celery_task(check_startup_achievements, instance.submitted_by.id)
        )
    
    # Check if startup was claimed
    if hasattr(instance, '_state') and not instance._state.adding:
        if instance.claimed_by and instance.claim_verified:
            # Award points for claiming a startup
            try:
                PointsService.award_points(
                    instance.claimed_by,
                    'startup_claim',
                    description=f"Claimed startup: {instance.name}",
                    startup_id=instance.id
                )
            except Exception as e:
                pass  # Log error but don't fail the operation
            
            transaction.on_commit(
                lambda: safe_celery_task(check_startup_achievements, instance.claimed_by.id)
            )

@receiver(post_save, sender=Job)
def check_job_achievements(sender, instance, created, **kwargs):
    """Check job-related achievements and award points"""
    if created and instance.posted_by:
        # Award points for posting a job
        try:
            PointsService.award_points(
                instance.posted_by,
                'job_post',
                description=f"Posted job: {instance.title}",
                job_id=instance.id
            )
        except Exception as e:
            pass  # Log error but don't fail the operation
        
        transaction.on_commit(
            lambda: safe_celery_task(update_achievement_progress,
                instance.posted_by.id,
                'job-creator',
                {'jobs_posted': 1}
            )
        )

# Job application signal (if JobApplication model exists)
@receiver(post_save, sender=JobApplication)
def check_job_application_points(sender, instance, created, **kwargs):
    """Award points when user applies for a job"""
    if created:
        try:
            PointsService.award_points(
                instance.applicant,
                'job_apply',
                description=f"Applied for job: {instance.job.title}",
                job_id=instance.job.id
            )
        except Exception as e:
            pass  # Log error but don't fail the operation

# Import this signals module in the app's ready() method