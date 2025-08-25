# apps/notifications/utils.py
from .models import Notification, NotificationPreference
import logging

logger = logging.getLogger(__name__)


def create_notification(recipient, notification_type, title, message, sender=None, **kwargs):
    """
    Helper function to create notifications
    """
    try:
        # Check if user wants this type of notification
        preferences, _ = NotificationPreference.objects.get_or_create(user=recipient)
        
        # Check in-app notification preference
        preference_field = f"inapp_on_{notification_type.split('_')[0]}"
        if hasattr(preferences, preference_field):
            if not getattr(preferences, preference_field):
                return None  # User doesn't want this type of notification
        
        notification = Notification.create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            sender=sender,
            **kwargs
        )
        
        logger.info(f"Created notification: {notification_type} for {recipient.username}")
        return notification
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None


def notify_startup_liked(startup, liker):
    """Create notification when someone likes a startup"""
    if startup.claimed_by and startup.claimed_by != liker:
        return create_notification(
            recipient=startup.claimed_by,
            notification_type='like_startup',
            title='Someone liked your startup!',
            message=f'{liker.get_full_name() or liker.username} liked {startup.name}',
            sender=liker,
            startup_id=startup.id
        )


def notify_startup_commented(startup, commenter, comment_text):
    """Create notification when someone comments on a startup"""
    if startup.claimed_by and startup.claimed_by != commenter:
        preview = comment_text[:50] + '...' if len(comment_text) > 50 else comment_text
        return create_notification(
            recipient=startup.claimed_by,
            notification_type='comment_startup',
            title='New comment on your startup',
            message=f'{commenter.get_full_name() or commenter.username} commented: "{preview}"',
            sender=commenter,
            startup_id=startup.id
        )


def notify_startup_rated(startup, rater, rating):
    """Create notification when someone rates a startup"""
    if startup.claimed_by and startup.claimed_by != rater:
        return create_notification(
            recipient=startup.claimed_by,
            notification_type='rating_startup',
            title='Someone rated your startup!',
            message=f'{rater.get_full_name() or rater.username} gave {startup.name} {rating} stars',
            sender=rater,
            startup_id=startup.id,
            extra_data={'rating': rating}
        )


def notify_post_liked(post, liker):
    """Create notification when someone likes a post"""
    if post.author and post.author != liker:
        return create_notification(
            recipient=post.author,
            notification_type='like_post',
            title='Someone liked your post!',
            message=f'{liker.get_full_name() or liker.username} liked your post',
            sender=liker,
            post_id=post.id
        )


def notify_post_commented(post, commenter, comment_text):
    """Create notification when someone comments on a post"""
    if post.author and post.author != commenter:
        preview = comment_text[:50] + '...' if len(comment_text) > 50 else comment_text
        return create_notification(
            recipient=post.author,
            notification_type='comment_post',
            title='New comment on your post',
            message=f'{commenter.get_full_name() or commenter.username} commented: "{preview}"',
            sender=commenter,
            post_id=post.id
        )


def notify_job_application(job, applicant):
    """Create notification when someone applies to a job"""
    if job.posted_by and job.posted_by != applicant:
        startup_name = job.startup.name if job.startup else 'your job posting'
        return create_notification(
            recipient=job.posted_by,
            notification_type='job_application',
            title='New job application',
            message=f'{applicant.get_full_name() or applicant.username} applied to {job.title} at {startup_name}',
            sender=applicant,
            job_id=job.id
        )


def notify_startup_approved(startup):
    """Create notification when a startup is approved"""
    if startup.claimed_by:
        return create_notification(
            recipient=startup.claimed_by,
            notification_type='startup_approved',
            title='Startup approved!',
            message=f'Your startup "{startup.name}" has been approved and is now live!',
            startup_id=startup.id
        )


def notify_startup_rejected(startup, reason=''):
    """Create notification when a startup is rejected"""
    if startup.claimed_by:
        message = f'Your startup "{startup.name}" was not approved'
        if reason:
            message += f': {reason}'
        
        return create_notification(
            recipient=startup.claimed_by,
            notification_type='startup_rejected',
            title='Startup not approved',
            message=message,
            startup_id=startup.id,
            extra_data={'reason': reason}
        )


def notify_job_approved(job):
    """Create notification when a job is approved"""
    if job.posted_by:
        return create_notification(
            recipient=job.posted_by,
            notification_type='job_approved',
            title='Job posting approved!',
            message=f'Your job posting "{job.title}" has been approved and is now live!',
            job_id=job.id
        )


def notify_job_rejected(job, reason=''):
    """Create notification when a job is rejected"""
    if job.posted_by:
        message = f'Your job posting "{job.title}" was not approved'
        if reason:
            message += f': {reason}'
        
        return create_notification(
            recipient=job.posted_by,
            notification_type='job_rejected',
            title='Job posting not approved',
            message=message,
            job_id=job.id,
            extra_data={'reason': reason}
        )


def notify_user_followed(followed_user, follower):
    """Create notification when someone follows a user"""
    if followed_user != follower:  # Don't notify if user follows themselves
        return create_notification(
            recipient=followed_user,
            notification_type='follow_user',
            title='New follower!',
            message=f'{follower.get_full_name() or follower.username} started following you',
            sender=follower
        )


def notify_user_mentioned(mentioned_user, mentioner, content_type, content_id, content_title=''):
    """Create notification when someone mentions a user"""
    if mentioned_user != mentioner:  # Don't notify if user mentions themselves
        return create_notification(
            recipient=mentioned_user,
            notification_type='mention',
            title='You were mentioned!',
            message=f'{mentioner.get_full_name() or mentioner.username} mentioned you in a {content_type}',
            sender=mentioner,
            startup_id=content_id if content_type == 'startup' else None,
            post_id=content_id if content_type == 'post' else None,
            comment_id=content_id if content_type == 'comment' else None,
            extra_data={'content_type': content_type, 'content_title': content_title}
        )


def notify_claim_approved(claim, approver=None):
    """Create notification when a startup claim is approved"""
    if claim.user:
        return create_notification(
            recipient=claim.user,
            notification_type='claim_approved',
            title='Claim approved!',
            message=f'Your claim for "{claim.startup.name}" has been approved. You now have ownership access.',
            sender=approver,
            startup_id=claim.startup.id
        )


def notify_claim_rejected(claim, reason='', rejector=None):
    """Create notification when a startup claim is rejected"""
    if claim.user:
        message = f'Your claim for "{claim.startup.name}" was not approved'
        if reason:
            message += f': {reason}'
        
        return create_notification(
            recipient=claim.user,
            notification_type='claim_rejected',
            title='Claim not approved',
            message=message,
            sender=rejector,
            startup_id=claim.startup.id,
            extra_data={'reason': reason}
        )