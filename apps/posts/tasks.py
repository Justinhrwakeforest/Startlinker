# startup_hub/apps/posts/tasks.py
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from .ranking import PostRankingService
from .models import Post, PostRankingScore
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def calculate_ranking_scores_task(self, batch_size=1000, recent_only=False):
    """
    Celery task to calculate ranking scores for posts
    This should be run periodically (e.g., every hour)
    """
    try:
        logger.info("Starting ranking score calculation task")
        
        # Initialize ranking service
        ranking_service = PostRankingService()
        
        # Get posts to process
        posts_queryset = Post.objects.filter(
            is_approved=True,
            is_draft=False
        ).select_related('author__connect_profile')
        
        if recent_only:
            # Only process posts from the last 7 days for efficiency
            cutoff_date = timezone.now() - timezone.timedelta(days=7)
            posts_queryset = posts_queryset.filter(created_at__gte=cutoff_date)
        
        # Only process posts that haven't been calculated in the last hour
        cutoff_time = timezone.now() - timezone.timedelta(hours=1)
        posts_queryset = posts_queryset.filter(
            models.Q(ranking_score__isnull=True) |
            models.Q(ranking_score__calculated_at__lt=cutoff_time)
        )
        
        total_posts = posts_queryset.count()
        
        if total_posts == 0:
            logger.info("No posts to process for ranking scores")
            return {"status": "success", "processed": 0, "message": "No posts to process"}
        
        logger.info(f"Processing {total_posts} posts for ranking scores")
        
        processed = 0
        errors = 0
        
        # Process in batches
        for i in range(0, total_posts, batch_size):
            try:
                batch = posts_queryset[i:i + batch_size]
                batch_scores = ranking_service._calculate_batch_scores(batch)
                processed += len(batch_scores)
                
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch_scores)} posts")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                
                # Retry the task if too many errors
                if errors > 3:
                    logger.error("Too many errors, retrying task")
                    raise self.retry(countdown=60 * (self.request.retries + 1))
        
        logger.info(f"Ranking score calculation completed. Processed: {processed}, Errors: {errors}")
        
        # Clear ranking caches
        cache.delete_many([
            key for key in cache._cache.keys() 
            if key.startswith('ranked_posts_')
        ])
        
        return {
            "status": "success",
            "processed": processed,
            "errors": errors,
            "total_scores": PostRankingScore.objects.count()
        }
        
    except Exception as e:
        logger.error(f"Fatal error in ranking score calculation task: {e}")
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task
def cleanup_old_ranking_scores():
    """
    Clean up old or orphaned ranking scores
    """
    try:
        logger.info("Starting cleanup of old ranking scores")
        
        # Remove ranking scores for posts older than 30 days that have low engagement
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        old_low_engagement = PostRankingScore.objects.filter(
            post__created_at__lt=cutoff_date,
            total_score__lt=1.0  # Very low engagement
        )
        
        count = old_low_engagement.count()
        if count > 0:
            old_low_engagement.delete()
            logger.info(f"Cleaned up {count} old low-engagement ranking scores")
        
        # Remove orphaned scores (posts that no longer exist)
        orphaned_scores = PostRankingScore.objects.filter(post__isnull=True)
        orphaned_count = orphaned_scores.count()
        
        if orphaned_count > 0:
            orphaned_scores.delete()
            logger.info(f"Cleaned up {orphaned_count} orphaned ranking scores")
        
        return {
            "status": "success",
            "old_scores_removed": count,
            "orphaned_scores_removed": orphaned_count
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise


@shared_task
def update_trending_posts():
    """
    Update trending posts cache
    """
    try:
        logger.info("Updating trending posts cache")
        
        ranking_service = PostRankingService()
        
        # Get trending posts for anonymous users
        trending_posts = ranking_service._get_general_ranked_posts(limit=50, offset=0)
        
        # Cache for 30 minutes
        cache.set('trending_posts_cache', trending_posts, 1800)
        
        logger.info(f"Cached {len(trending_posts)} trending posts")
        
        return {
            "status": "success",
            "cached_posts": len(trending_posts)
        }
        
    except Exception as e:
        logger.error(f"Error updating trending posts: {e}")
        raise


@shared_task
def analyze_user_interactions(days_back=7):
    """
    Analyze user interactions to improve ranking algorithm
    """
    try:
        from .models import UserInteraction
        from django.db.models import Count, Avg
        
        logger.info(f"Analyzing user interactions from the last {days_back} days")
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days_back)
        
        # Analyze interaction patterns
        interaction_stats = UserInteraction.objects.filter(
            created_at__gte=cutoff_date
        ).values('interaction_type').annotate(
            count=Count('id'),
            avg_value=Avg('value')
        ).order_by('-count')
        
        # Store analysis results in cache for use by ranking algorithm
        analysis_data = {
            'interaction_stats': list(interaction_stats),
            'analyzed_period': days_back,
            'total_interactions': sum(stat['count'] for stat in interaction_stats),
            'calculated_at': timezone.now().isoformat()
        }
        
        cache.set('interaction_analysis', analysis_data, 86400)  # Cache for 24 hours
        
        logger.info(f"Analyzed {analysis_data['total_interactions']} interactions")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Error analyzing user interactions: {e}")
        raise