# startup_hub/apps/connect/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import math
import logging

logger = logging.getLogger(__name__)

def calculate_match_score(profile1, profile2):
    """Calculate compatibility score between two co-founder profiles"""
    scores = {
        'skills': 0,
        'interests': 0,
        'experience': 0,
        'overall': 0
    }
    
    # Skills complementarity (higher score for different but complementary skills)
    skills1 = set(profile1.skills)
    skills2 = set(profile2.skills)
    looking_for1 = set(profile1.looking_for_skills)
    looking_for2 = set(profile2.looking_for_skills)
    
    # How well do their skills match what the other is looking for?
    match1 = len(skills1.intersection(looking_for2))
    match2 = len(skills2.intersection(looking_for1))
    
    if looking_for1 and looking_for2:
        scores['skills'] = ((match1 / len(looking_for2)) + (match2 / len(looking_for1))) * 50
    
    # Industry interest alignment
    industries1 = set(profile1.industry_preferences.values_list('id', flat=True))
    industries2 = set(profile2.industry_preferences.values_list('id', flat=True))
    
    if industries1 and industries2:
        overlap = len(industries1.intersection(industries2))
        total = len(industries1.union(industries2))
        scores['interests'] = (overlap / total) * 100
    
    # Experience balance (complementary experience levels can be good)
    exp_diff = abs(profile1.experience_years - profile2.experience_years)
    if exp_diff <= 2:  # Similar experience
        scores['experience'] = 90
    elif exp_diff <= 5:  # Somewhat complementary
        scores['experience'] = 70
    elif exp_diff <= 10:  # Very complementary
        scores['experience'] = 50
    else:
        scores['experience'] = 30
    
    # Calculate overall score
    scores['overall'] = (
        scores['skills'] * 0.4 +
        scores['interests'] * 0.3 +
        scores['experience'] * 0.3
    )
    
    return scores

def send_notification_email(user, notification):
    """Send email notification to user"""
    if not user.email:
        return
    
    # Check user's email preferences
    profile = getattr(user, 'connect_profile', None)
    if not profile:
        return
    
    # Check notification type preferences
    if notification.notification_type == 'mention' and not profile.email_on_mention:
        return
    elif notification.notification_type == 'reply' and not profile.email_on_reply:
        return
    elif notification.notification_type == 'follow' and not profile.email_on_follow:
        return
    
    # Prepare email
    subject = f"[StartupHub] {notification.title}"
    
    html_message = render_to_string('emails/notification.html', {
        'user': user,
        'notification': notification,
        'action_url': f"{settings.FRONTEND_URL}{notification.action_url}" if notification.action_url else None
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Log error but don't raise
        logger.error(f"Failed to send notification email: {e}")

def get_user_activity_score(user, days=30):
    """Calculate user's activity score for the past N days"""
    from django.utils import timezone
    from datetime import timedelta
    from apps.posts.models import Post, Comment, PostReaction
    
    since = timezone.now() - timedelta(days=days)
    
    # Count activities
    posts_count = Post.objects.filter(
        author=user,
        created_at__gte=since
    ).count()
    
    comments_count = Comment.objects.filter(
        author=user,
        created_at__gte=since
    ).count()
    
    reactions_count = PostReaction.objects.filter(
        user=user,
        created_at__gte=since
    ).count()
    
    # Weight different activities
    score = (
        posts_count * 10 +  # Posts are most valuable
        comments_count * 5 +  # Comments are valuable
        reactions_count * 1  # Reactions show engagement
    )
    
    return score

def update_user_reputation(user, action, points=0):
    """Update user's reputation score based on actions"""
    profile = getattr(user, 'connect_profile', None)
    if not profile:
        return
    
    # Define point values for different actions
    action_points = {
        'post_created': 5,
        'post_liked': 1,
        'post_commented': 2,
        'helpful_vote': 3,
        'best_answer': 10,
        'event_hosted': 15,
        'resource_shared': 8,
        'cofounder_match': 20,
    }
    
    # Use provided points or default for action
    points_to_add = points or action_points.get(action, 0)
    
    # Update reputation
    profile.reputation_score += points_to_add
    profile.save(update_fields=['reputation_score'])
    
    # Check for badge achievements
    check_and_award_badges(user, profile)

def check_and_award_badges(user, profile):
    """Check and award badges based on achievements"""
    current_badges = set(profile.badges)
    new_badges = set()
    
    # Define badge criteria
    if profile.reputation_score >= 100 and 'rising_star' not in current_badges:
        new_badges.add('rising_star')
    
    if profile.reputation_score >= 500 and 'contributor' not in current_badges:
        new_badges.add('contributor')
    
    if profile.reputation_score >= 1000 and 'expert' not in current_badges:
        new_badges.add('expert')
    
    if profile.follower_count >= 50 and 'influencer' not in current_badges:
        new_badges.add('influencer')
    
    if profile.helpful_votes >= 25 and 'helpful_member' not in current_badges:
        new_badges.add('helpful_member')
    
    # Early adopter badge (if user joined in first month)
    from django.utils import timezone
    from datetime import timedelta
    
    if user.date_joined < timezone.now() - timedelta(days=30) and 'early_adopter' not in current_badges:
        new_badges.add('early_adopter')
    
    # Update badges if new ones earned
    if new_badges:
        profile.badges = list(current_badges.union(new_badges))
        profile.save(update_fields=['badges'])
        
        # Send notifications for new badges
        from .models import Notification
        for badge in new_badges:
            Notification.objects.create(
                user=user,
                notification_type='badge_earned',
                title=f'New Badge: {badge.replace("_", " ").title()}',
                message=f'Congratulations! You\'ve earned the {badge.replace("_", " ").title()} badge!'
            )

def get_trending_topics(days=7, limit=10):
    """Get trending topics based on recent usage"""
    from django.utils import timezone
    from datetime import timedelta
    from apps.posts.models import Topic
    
    since = timezone.now() - timedelta(days=days)
    
    # Get topics with most posts in recent days
    trending = Topic.objects.annotate(
        recent_posts=Count(
            'posts',
            filter=Q(posts__created_at__gte=since)
        )
    ).filter(recent_posts__gt=0).order_by('-recent_posts')[:limit]
    
    return trending

def generate_feed_recommendations(user, limit=20):
    """Generate personalized feed recommendations for user"""
    from apps.posts.models import Post
    from django.db.models import Q, F, Count
    
    # Get user's interests and followed users
    profile = getattr(user, 'connect_profile', None)
    if not profile:
        return Post.objects.none()
    
    followed_users = user.following_relationships.values_list('following', flat=True)
    user_expertise = profile.expertise or []
    
    # Build recommendation query
    posts = Post.objects.filter(
        is_approved=True,
        is_draft=False
    ).exclude(
        author=user  # Don't show own posts
    )
    
    # Prioritize posts from followed users
    if followed_users:
        posts = posts.annotate(
            is_following=Exists(
                Post.objects.filter(
                    id=OuterRef('id'),
                    author__in=followed_users
                )
            )
        )
    
    # Prioritize posts matching user expertise
    if user_expertise:
        # This would need to match against post topics
        pass
    
    # Order by relevance
    posts = posts.annotate(
        engagement_score=F('like_count') + F('comment_count') * 2
    ).order_by(
        '-is_following',  # Followed users first
        '-created_at',  # Then by recency
        '-engagement_score'  # Then by engagement
    )[:limit]
    
    return posts