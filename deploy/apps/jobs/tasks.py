# startup_hub/apps/jobs/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.core.management import call_command
from .models import Job, JobBookmark
import logging

logger = logging.getLogger(__name__)


@shared_task
def delete_expired_jobs():
    """
    Celery task to delete expired jobs automatically.
    This task should be scheduled to run daily.
    """
    try:
        # Use the management command for consistency
        call_command('delete_expired_jobs', verbosity=1)
        logger.info('Expired jobs cleanup task completed successfully')
        return 'Expired jobs cleanup completed'
    except Exception as e:
        logger.error(f'Error in expired jobs cleanup task: {e}')
        raise


@shared_task
def cleanup_expired_jobs_manual(soft_delete=True):
    """
    Manual cleanup task that can be triggered from admin interface.
    
    Args:
        soft_delete (bool): If True, mark jobs as expired instead of deleting them
    """
    now = timezone.now()
    
    try:
        with transaction.atomic():
            # Find expired jobs
            expired_jobs = Job.objects.filter(
                expires_at__lt=now,
                status__in=['active', 'pending']
            )
            
            total_expired = expired_jobs.count()
            
            if total_expired == 0:
                logger.info('No expired jobs found during manual cleanup')
                return 'No expired jobs found'
            
            job_ids = list(expired_jobs.values_list('id', flat=True))
            affected_bookmarks = JobBookmark.objects.filter(job_id__in=job_ids).count()
            
            if soft_delete:
                # Soft delete: change status to 'expired'
                expired_jobs.update(
                    status='expired',
                    is_active=False
                )
                
                # Remove bookmarks
                JobBookmark.objects.filter(job_id__in=job_ids).delete()
                
                message = f'Marked {total_expired} jobs as expired and removed {affected_bookmarks} bookmarks'
                logger.info(f'Manual cleanup: {message}')
                return message
            else:
                # Hard delete
                deleted_count, _ = expired_jobs.delete()
                
                message = f'Deleted {deleted_count} expired jobs and their bookmarks'
                logger.info(f'Manual cleanup: {message}')
                return message
                
    except Exception as e:
        logger.error(f'Error in manual expired jobs cleanup: {e}')
        raise


@shared_task
def notify_expiring_jobs(days_before=3):
    """
    Task to notify job posters about jobs expiring soon.
    
    Args:
        days_before (int): Number of days before expiration to send notification
    """
    from datetime import timedelta
    from django.core.mail import send_mail
    from django.conf import settings
    
    now = timezone.now()
    expiry_threshold = now + timedelta(days=days_before)
    
    try:
        # Find jobs expiring soon
        expiring_jobs = Job.objects.filter(
            expires_at__lte=expiry_threshold,
            expires_at__gt=now,
            status='active',
            is_active=True
        ).select_related('posted_by', 'startup')
        
        notifications_sent = 0
        
        for job in expiring_jobs:
            try:
                # Send email notification to job poster
                days_left = (job.expires_at - now).days
                
                subject = f'Job posting "{job.title}" expires in {days_left} days'
                message = f"""
Hello {job.posted_by.get_full_name() or job.posted_by.username},

Your job posting "{job.title}" at {job.startup.name if job.startup else 'your company'} 
will expire on {job.expires_at.strftime('%B %d, %Y')}.

If you'd like to extend the posting or create a new one, please log in to your account.

Best regards,
StartupHub Team
"""
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[job.posted_by.email],
                    fail_silently=False
                )
                
                notifications_sent += 1
                
            except Exception as e:
                logger.error(f'Failed to send expiry notification for job {job.id}: {e}')
        
        message = f'Sent {notifications_sent} job expiry notifications'
        logger.info(message)
        return message
        
    except Exception as e:
        logger.error(f'Error in job expiry notification task: {e}')
        raise