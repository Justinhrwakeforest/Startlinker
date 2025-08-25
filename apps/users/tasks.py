# apps/users/tasks.py - Celery tasks for user/social functionality
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task
def publish_scheduled_post(scheduled_post_id):
    """
    Publish a scheduled post immediately
    """
    try:
        from .social_models import ScheduledPost
        from apps.posts.models import Post
        
        # Get the scheduled post
        try:
            scheduled_post = ScheduledPost.objects.get(id=scheduled_post_id)
        except ScheduledPost.DoesNotExist:
            logger.error(f"Scheduled post {scheduled_post_id} not found")
            return False
        
        if scheduled_post.status != 'scheduled':
            logger.error(f"Cannot publish scheduled post {scheduled_post_id}: status is {scheduled_post.status}")
            return False
        
        # Create the actual post
        post_data = {
            'author': scheduled_post.author,
            'title': scheduled_post.title,
            'content': scheduled_post.content,
            'post_type': scheduled_post.post_type,
            'is_anonymous': scheduled_post.is_anonymous,
            'related_startup': scheduled_post.related_startup,
            'related_job': scheduled_post.related_job,
        }
        
        # Create the post
        post = Post.objects.create(**post_data)
        
        # Handle attachments if any
        if scheduled_post.images_data:
            # TODO: Handle image attachments when implemented
            pass
            
        if scheduled_post.links_data:
            # TODO: Handle link attachments when implemented
            pass
            
        if scheduled_post.topics_data:
            # TODO: Handle topic/hashtag attachments when implemented
            pass
        
        # Update scheduled post status
        scheduled_post.status = 'published'
        scheduled_post.published_post = post
        scheduled_post.published_at = timezone.now()
        scheduled_post.save(update_fields=['status', 'published_post', 'published_at'])
        
        logger.info(f"Successfully published scheduled post {scheduled_post_id} as post {post.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error publishing scheduled post {scheduled_post_id}: {str(e)}")
        
        # Mark as failed
        try:
            scheduled_post = ScheduledPost.objects.get(id=scheduled_post_id)
            scheduled_post.status = 'failed'
            scheduled_post.error_message = str(e)
            scheduled_post.save(update_fields=['status', 'error_message'])
        except:
            pass
            
        return False