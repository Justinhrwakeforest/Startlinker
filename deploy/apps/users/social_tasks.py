# apps/users/social_tasks.py - Celery tasks for social features
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, F
import logging

from .social_models import (
    ScheduledPost, Story, Achievement, UserAchievement, 
    UserAchievementProgress, UserFollow
)
from apps.posts.models import Post, PostImage, PostLink
from apps.notifications.models import Notification
from apps.startups.models import Startup

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task
def publish_scheduled_post(scheduled_post_id):
    """Publish a scheduled post"""
    try:
        with transaction.atomic():
            scheduled_post = ScheduledPost.objects.select_for_update().get(
                id=scheduled_post_id,
                status='scheduled'
            )
            
            # Create the actual post
            post = Post.objects.create(
                author=scheduled_post.author,
                title=scheduled_post.title,
                content=scheduled_post.content,
                post_type=scheduled_post.post_type,
                is_anonymous=scheduled_post.is_anonymous,
                related_startup=scheduled_post.related_startup,
                related_job=scheduled_post.related_job
            )
            
            # Add topics
            if scheduled_post.topics_data:
                from apps.posts.models import Topic
                for topic_name in scheduled_post.topics_data:
                    topic, created = Topic.objects.get_or_create(
                        name=topic_name,
                        defaults={'slug': topic_name.lower().replace(' ', '-')}
                    )
                    post.topics.add(topic)
            
            # Add images
            if scheduled_post.images_data:
                for img_data in scheduled_post.images_data:
                    PostImage.objects.create(
                        post=post,
                        image=img_data.get('image'),
                        caption=img_data.get('caption', ''),
                        order=img_data.get('order', 0)
                    )
            
            # Add links
            if scheduled_post.links_data:
                for link_data in scheduled_post.links_data:
                    PostLink.objects.create(
                        post=post,
                        url=link_data.get('url'),
                        title=link_data.get('title', ''),
                        description=link_data.get('description', ''),
                        image_url=link_data.get('image_url', ''),
                        domain=link_data.get('domain', '')
                    )
            
            # Update scheduled post
            scheduled_post.status = 'published'
            scheduled_post.published_post = post
            scheduled_post.published_at = timezone.now()
            scheduled_post.save()
            
            # Notify followers
            create_post_notifications.delay(post.id)
            
            # Check achievements
            check_content_achievements.delay(scheduled_post.author.id)
            
            logger.info(f"Successfully published scheduled post {scheduled_post_id}")
            return {'success': True, 'post_id': str(post.id)}
            
    except ScheduledPost.DoesNotExist:
        logger.error(f"Scheduled post {scheduled_post_id} not found or already published")
        return {'success': False, 'error': 'Post not found or already published'}
    
    except Exception as e:
        logger.error(f"Error publishing scheduled post {scheduled_post_id}: {str(e)}")
        
        # Mark as failed
        try:
            scheduled_post = ScheduledPost.objects.get(id=scheduled_post_id)
            scheduled_post.status = 'failed'
            scheduled_post.error_message = str(e)
            scheduled_post.save()
        except:
            pass
        
        return {'success': False, 'error': str(e)}

@shared_task
def process_scheduled_posts():
    """Process all scheduled posts that are ready to publish"""
    ready_posts = ScheduledPost.objects.filter(
        status='scheduled',
        scheduled_for__lte=timezone.now()
    )
    
    processed_count = 0
    for post in ready_posts:
        publish_scheduled_post.delay(post.id)
        processed_count += 1
    
    logger.info(f"Queued {processed_count} scheduled posts for publishing")
    return {'processed_count': processed_count}

@shared_task
def cleanup_expired_stories():
    """Clean up expired stories"""
    expired_stories = Story.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now()
    )
    
    count = expired_stories.count()
    expired_stories.update(is_active=False)
    
    logger.info(f"Deactivated {count} expired stories")
    return {'deactivated_count': count}

@shared_task
def create_post_notifications(post_id):
    """Create notifications for followers when user creates a post"""
    try:
        post = Post.objects.get(id=post_id)
        
        # Get followers who want post notifications
        followers = UserFollow.objects.filter(
            following=post.author,
            notify_on_posts=True
        ).select_related('follower')
        
        notifications = []
        for follow in followers:
            notifications.append(
                Notification(
                    recipient=follow.follower,
                    sender=post.author,
                    notification_type='post_created',
                    title=f"New post from {post.author.get_display_name()}",
                    message=f"{post.author.get_display_name()} shared a new post: {post.title or post.content[:50]}...",
                    post_id=post.id
                )
            )
        
        # Bulk create notifications
        if notifications:
            Notification.objects.bulk_create(notifications, batch_size=100)
            logger.info(f"Created {len(notifications)} post notifications for post {post_id}")
        
        return {'notifications_created': len(notifications)}
        
    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found for notifications")
        return {'error': 'Post not found'}

@shared_task
def create_story_notifications(story_id):
    """Create notifications for followers when user creates a story"""
    try:
        story = Story.objects.get(id=story_id)
        
        # Get followers who want story notifications
        followers = UserFollow.objects.filter(
            following=story.author,
            notify_on_stories=True
        ).select_related('follower')
        
        notifications = []
        for follow in followers:
            notifications.append(
                Notification(
                    recipient=follow.follower,
                    sender=story.author,
                    notification_type='story_created',
                    title=f"New story from {story.author.get_display_name()}",
                    message=f"{story.author.get_display_name()} shared a new story",
                    extra_data={'story_id': str(story.id)}
                )
            )
        
        if notifications:
            Notification.objects.bulk_create(notifications, batch_size=100)
            logger.info(f"Created {len(notifications)} story notifications for story {story_id}")
        
        return {'notifications_created': len(notifications)}
        
    except Story.DoesNotExist:
        logger.error(f"Story {story_id} not found for notifications")
        return {'error': 'Story not found'}

@shared_task
def check_profile_achievements(user_id):
    """Check and award profile completion achievements"""
    try:
        user = User.objects.get(id=user_id)
        
        # Profile completion percentage
        completion_fields = [
            user.first_name, user.last_name, user.bio, 
            user.location, user.profile_picture
        ]
        completion_percentage = sum(1 for field in completion_fields if field) / len(completion_fields) * 100
        
        # Award achievements based on completion
        achievements_to_check = [
            ('profile_starter', 25),  # 25% completion
            ('profile_builder', 50),  # 50% completion
            ('profile_complete', 100), # 100% completion
        ]
        
        awarded_count = 0
        for achievement_slug, required_percentage in achievements_to_check:
            if completion_percentage >= required_percentage:
                achievement = Achievement.objects.filter(slug=achievement_slug).first()
                if achievement:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        awarded_count += 1
                        create_achievement_notification.delay(user.id, achievement.id)
        
        return {'awarded_count': awarded_count, 'completion_percentage': completion_percentage}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for profile achievements")
        return {'error': 'User not found'}

@shared_task
def check_social_achievements(user_id):
    """Check and award social engagement achievements"""
    try:
        user = User.objects.get(id=user_id)
        
        # Count social metrics
        followers_count = UserFollow.objects.filter(following=user).count()
        following_count = UserFollow.objects.filter(follower=user).count()
        
        # Achievement thresholds
        follower_achievements = [
            ('first_follower', 1),
            ('popular_user', 10),
            ('social_star', 50),
            ('influencer', 100),
            ('celebrity', 500),
        ]
        
        following_achievements = [
            ('networker', 10),
            ('super_networker', 50),
            ('connection_master', 100),
        ]
        
        awarded_count = 0
        
        # Check follower achievements
        for achievement_slug, required_count in follower_achievements:
            if followers_count >= required_count:
                achievement = Achievement.objects.filter(slug=achievement_slug).first()
                if achievement:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        awarded_count += 1
                        create_achievement_notification.delay(user.id, achievement.id)
        
        # Check following achievements
        for achievement_slug, required_count in following_achievements:
            if following_count >= required_count:
                achievement = Achievement.objects.filter(slug=achievement_slug).first()
                if achievement:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        awarded_count += 1
                        create_achievement_notification.delay(user.id, achievement.id)
        
        return {'awarded_count': awarded_count}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for social achievements")
        return {'error': 'User not found'}

@shared_task
def check_content_achievements(user_id):
    """Check and award content creation achievements"""
    try:
        user = User.objects.get(id=user_id)
        
        # Count content metrics
        posts_count = Post.objects.filter(author=user, is_approved=True).count()
        stories_count = Story.objects.filter(author=user).count()
        
        # Content achievements
        post_achievements = [
            ('first_post', 1),
            ('prolific_writer', 10),
            ('content_creator', 25),
            ('thought_leader', 50),
            ('content_master', 100),
        ]
        
        story_achievements = [
            ('storyteller', 5),
            ('story_master', 25),
            ('daily_storyteller', 50),
        ]
        
        awarded_count = 0
        
        # Check post achievements
        for achievement_slug, required_count in post_achievements:
            if posts_count >= required_count:
                achievement = Achievement.objects.filter(slug=achievement_slug).first()
                if achievement:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        awarded_count += 1
                        create_achievement_notification.delay(user.id, achievement.id)
        
        # Check story achievements
        for achievement_slug, required_count in story_achievements:
            if stories_count >= required_count:
                achievement = Achievement.objects.filter(slug=achievement_slug).first()
                if achievement:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        awarded_count += 1
                        create_achievement_notification.delay(user.id, achievement.id)
        
        return {'awarded_count': awarded_count}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for content achievements")
        return {'error': 'User not found'}

@shared_task
def check_startup_achievements(user_id):
    """Check and award startup-related achievements"""
    try:
        user = User.objects.get(id=user_id)
        
        # Count startup metrics
        claimed_startups = Startup.objects.filter(
            claimed_by=user, 
            claim_verified=True
        ).count()
        
        submitted_startups = Startup.objects.filter(
            submitted_by=user,
            is_approved=True
        ).count()
        
        # Startup achievements
        achievements_to_check = [
            ('startup_founder', claimed_startups, 1),
            ('serial_entrepreneur', claimed_startups, 3),
            ('startup_contributor', submitted_startups, 1),
            ('startup_scout', submitted_startups, 5),
        ]
        
        awarded_count = 0
        for achievement_slug, user_count, required_count in achievements_to_check:
            if user_count >= required_count:
                achievement = Achievement.objects.filter(slug=achievement_slug).first()
                if achievement:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        awarded_count += 1
                        create_achievement_notification.delay(user.id, achievement.id)
        
        return {'awarded_count': awarded_count}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for startup achievements")
        return {'error': 'User not found'}

@shared_task
def create_achievement_notification(user_id, achievement_id):
    """Create notification for earned achievement"""
    try:
        user = User.objects.get(id=user_id)
        achievement = Achievement.objects.get(id=achievement_id)
        
        # Award points for achievement (if not already awarded)
        from .points_service import PointsService
        try:
            PointsService.award_points(
                user, 
                'achievement', 
                points=achievement.points,
                description=f"Achievement Unlocked: {achievement.name}",
                achievement=achievement
            )
        except Exception as points_error:
            logger.error(f"Error awarding points for achievement {achievement_id}: {str(points_error)}")
        
        # Create notification
        notification = Notification.objects.create(
            recipient=user,
            notification_type='achievement_earned',
            title=f"Achievement Unlocked: {achievement.name}!",
            message=f"Congratulations! You've earned the '{achievement.name}' achievement (+{achievement.points} points). {achievement.description}",
            extra_data={
                'achievement_id': achievement.id,
                'achievement_slug': achievement.slug,
                'points': achievement.points,
                'rarity': achievement.rarity,
                'icon': achievement.icon
            }
        )
        
        # Send real-time WebSocket update
        try:
            from .consumers import send_achievement_update
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'rarity': achievement.rarity,
                'icon': achievement.icon,
                'points': achievement.points,
                'slug': achievement.slug
            }
            send_achievement_update(user.id, achievement_data, notification.id)
        except ImportError:
            pass  # WebSocket not configured
        
        # Notify followers about achievement (if public)
        user_achievement = UserAchievement.objects.get(
            user=user, 
            achievement=achievement
        )
        
        if user_achievement.is_public and achievement.rarity in ['rare', 'epic', 'legendary']:
            followers = UserFollow.objects.filter(
                following=user,
                notify_on_achievements=True
            ).select_related('follower')
            
            notifications = []
            for follow in followers:
                notifications.append(
                    Notification(
                        recipient=follow.follower,
                        sender=user,
                        notification_type='user_achievement',
                        title=f"{user.get_display_name()} earned an achievement!",
                        message=f"{user.get_display_name()} unlocked the '{achievement.name}' achievement",
                        extra_data={
                            'achievement_id': achievement.id,
                            'achievement_slug': achievement.slug
                        }
                    )
                )
            
            if notifications:
                Notification.objects.bulk_create(notifications, batch_size=100)
        
        logger.info(f"Created achievement notification for user {user_id}, achievement {achievement_id}")
        return {'success': True}
        
    except (User.DoesNotExist, Achievement.DoesNotExist) as e:
        logger.error(f"Error creating achievement notification: {str(e)}")
        return {'error': str(e)}

@shared_task
def update_achievement_progress(user_id, achievement_slug, progress_data):
    """Update user's progress towards an achievement"""
    try:
        user = User.objects.get(id=user_id)
        achievement = Achievement.objects.get(slug=achievement_slug, is_active=True)
        
        # Get or create progress record
        progress, created = UserAchievementProgress.objects.get_or_create(
            user=user,
            achievement=achievement,
            defaults={'current_progress': progress_data}
        )
        
        if not created and not progress.is_completed:
            # Update progress
            progress.current_progress.update(progress_data)
            
            # Calculate completion percentage based on requirements
            requirements = achievement.requirements
            total_required = sum(requirements.values()) if requirements else 1
            total_current = sum(progress.current_progress.values())
            
            progress.progress_percentage = min(100.0, (total_current / total_required) * 100)
            progress.save()
            
            # Send real-time progress update
            try:
                from .consumers import send_progress_update
                send_progress_update(
                    user.id, 
                    achievement.slug, 
                    progress.progress_percentage,
                    progress.current_progress
                )
            except ImportError:
                pass  # WebSocket not configured
            
            # Check if achievement is now complete
            if progress.progress_percentage >= 100.0 and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = timezone.now()
                progress.save()
                
                # Award the achievement
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'progress_data': progress.current_progress}
                )
                
                if created:
                    create_achievement_notification.delay(user.id, achievement.id)
                    return {'achievement_earned': True}
        
        return {'progress_updated': True, 'percentage': progress.progress_percentage}
        
    except (User.DoesNotExist, Achievement.DoesNotExist) as e:
        logger.error(f"Error updating achievement progress: {str(e)}")
        return {'error': str(e)}

@shared_task
def daily_achievement_check():
    """Daily task to check achievements for all users"""
    users = User.objects.filter(is_active=True)
    processed_count = 0
    
    for user in users:
        # Check different types of achievements
        check_profile_achievements.delay(user.id)
        check_social_achievements.delay(user.id)
        check_content_achievements.delay(user.id)
        check_startup_achievements.delay(user.id)
        processed_count += 1
    
    logger.info(f"Queued achievement checks for {processed_count} users")
    return {'users_processed': processed_count}

@shared_task
def generate_achievement_leaderboard():
    """Generate achievement leaderboard data"""
    # Top users by total points
    top_achievers = User.objects.annotate(
        total_points=models.Sum('achievements__achievement__points'),
        achievement_count=Count('achievements')
    ).filter(
        total_points__gt=0
    ).order_by('-total_points')[:50]
    
    # Recent achievements (last 7 days)
    recent_achievements = UserAchievement.objects.filter(
        earned_at__gte=timezone.now() - timezone.timedelta(days=7),
        is_public=True
    ).select_related('user', 'achievement').order_by('-earned_at')[:100]
    
    # Cache results (implementation depends on your caching strategy)
    leaderboard_data = {
        'top_achievers': [
            {
                'user_id': user.id,
                'username': user.username,
                'display_name': user.get_display_name(),
                'avatar': user.get_avatar_url(),
                'total_points': user.total_points or 0,
                'achievement_count': user.achievement_count
            }
            for user in top_achievers
        ],
        'recent_achievements': [
            {
                'user_id': ua.user.id,
                'username': ua.user.username,
                'display_name': ua.user.get_display_name(),
                'avatar': ua.user.get_avatar_url(),
                'achievement_name': ua.achievement.name,
                'achievement_icon': ua.achievement.icon,
                'achievement_rarity': ua.achievement.rarity,
                'earned_at': ua.earned_at.isoformat()
            }
            for ua in recent_achievements
        ]
    }
    
    logger.info("Generated achievement leaderboard data")
    return leaderboard_data