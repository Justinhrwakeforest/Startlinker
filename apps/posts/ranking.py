# startup_hub/apps/posts/ranking.py
from django.db.models import F, Q, Count, Avg, Case, When, Value, FloatField
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from typing import List, Dict, Optional
import math
import logging

from .models import Post, PostRankingScore, UserInteraction
from apps.connect.models import Follow

User = get_user_model()
logger = logging.getLogger(__name__)


class PostRankingService:
    """
    Sophisticated post ranking service that considers multiple factors:
    1. Posts from followed users (highest priority)
    2. Recent posts (time decay)
    3. Engagement metrics (likes, comments, shares)
    4. User interaction history
    5. Post popularity score
    6. Author reputation
    """
    
    # Scoring weights
    FOLLOW_BOOST = 10.0
    ENGAGEMENT_WEIGHT = 1.0
    RECENCY_WEIGHT = 0.5
    QUALITY_WEIGHT = 0.3
    REPUTATION_WEIGHT = 0.2
    TRENDING_WEIGHT = 0.8
    
    # Time decay parameters
    RECENCY_HALF_LIFE_HOURS = 24  # Score halves every 24 hours
    TRENDING_WINDOW_HOURS = 48    # Consider posts from last 48 hours for trending
    
    # Engagement score weights
    LIKE_WEIGHT = 1.0
    COMMENT_WEIGHT = 3.0
    SHARE_WEIGHT = 5.0
    BOOKMARK_WEIGHT = 2.0
    VIEW_WEIGHT = 0.01
    
    def __init__(self, user: Optional[User] = None):
        self.user = user
        
    def get_ranked_posts(self, limit: int = 50, offset: int = 0) -> List[Post]:
        """
        Get ranked posts for a user with sophisticated ranking algorithm
        """
        try:
            if self.user and self.user.is_authenticated:
                return self._get_personalized_ranked_posts(limit, offset)
            else:
                return self._get_general_ranked_posts(limit, offset)
        except Exception as e:
            logger.error(f"Error in get_ranked_posts: {e}")
            # Fallback to simple ordering
            return list(Post.objects.filter(
                is_approved=True, 
                is_draft=False
            ).order_by('-created_at')[offset:offset + limit])
    
    def _get_personalized_ranked_posts(self, limit: int, offset: int) -> List[Post]:
        """Get personalized ranked posts for authenticated user"""
        cache_key = f"ranked_posts_{self.user.id}_{limit}_{offset}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get followed users
        followed_user_ids = self._get_followed_user_ids()
        
        # Base queryset with optimizations
        queryset = Post.objects.filter(
            is_approved=True,
            is_draft=False
        ).select_related(
            'author',
            'related_startup',
            'related_job'
        ).prefetch_related(
            'topics',
            'images',
            'ranking_score'
        )
        
        # Calculate personalized scores
        queryset = self._annotate_personalized_scores(queryset, followed_user_ids)
        
        # Order by final score and get results
        posts = list(queryset.order_by('-final_ranking_score')[offset:offset + limit])
        
        # Cache for 5 minutes
        cache.set(cache_key, posts, 300)
        
        return posts
    
    def _get_general_ranked_posts(self, limit: int, offset: int) -> List[Post]:
        """Get ranked posts for anonymous users"""
        cache_key = f"ranked_posts_general_{limit}_{offset}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Use pre-calculated ranking scores or calculate on-the-fly
        queryset = Post.objects.filter(
            is_approved=True,
            is_draft=False
        ).select_related(
            'author',
            'related_startup',
            'related_job',
            'ranking_score'
        ).prefetch_related(
            'topics',
            'images'
        )
        
        # Try to use pre-calculated scores first
        posts_with_scores = queryset.filter(
            ranking_score__isnull=False
        ).order_by('-ranking_score__total_score')
        
        if posts_with_scores.exists():
            posts = list(posts_with_scores[offset:offset + limit])
        else:
            # Fallback to calculating scores on-the-fly
            queryset = self._annotate_general_scores(queryset)
            posts = list(queryset.order_by('-final_ranking_score')[offset:offset + limit])
        
        # Cache for 10 minutes
        cache.set(cache_key, posts, 600)
        
        return posts
    
    def _get_followed_user_ids(self) -> List[int]:
        """Get IDs of users followed by current user"""
        if not self.user or not self.user.is_authenticated:
            return []
        
        cache_key = f"followed_users_{self.user.id}"
        followed_ids = cache.get(cache_key)
        
        if followed_ids is None:
            followed_ids = list(Follow.objects.filter(
                follower=self.user
            ).values_list('following_id', flat=True))
            # Cache for 30 minutes
            cache.set(cache_key, followed_ids, 1800)
        
        return followed_ids
    
    def _annotate_personalized_scores(self, queryset, followed_user_ids):
        """Annotate queryset with personalized ranking scores"""
        now = timezone.now()
        
        return queryset.annotate(
            # Follow boost
            follow_boost=Case(
                When(author_id__in=followed_user_ids, then=Value(self.FOLLOW_BOOST)),
                default=Value(0.0),
                output_field=FloatField()
            ),
            
            # Engagement score
            engagement_score=(
                F('like_count') * self.LIKE_WEIGHT +
                F('comment_count') * self.COMMENT_WEIGHT +
                F('share_count') * self.SHARE_WEIGHT +
                F('bookmark_count') * self.BOOKMARK_WEIGHT +
                F('view_count') * self.VIEW_WEIGHT
            ),
            
            # Calculate hours since creation
            hours_since_creation=Case(
                When(created_at__gte=now - timezone.timedelta(hours=120),  # Within last 5 days
                     then=Value(1.0)),
                When(created_at__gte=now - timezone.timedelta(hours=240),  # Within last 10 days  
                     then=Value(5.0)),
                default=Value(24.0),
                output_field=FloatField()
            ),
            
            # Time decay factor
            recency_score=Case(
                When(hours_since_creation__lte=self.RECENCY_HALF_LIFE_HOURS * 5,
                     then=Value(2.0) ** (-F('hours_since_creation') / self.RECENCY_HALF_LIFE_HOURS)),
                default=Value(0.01),
                output_field=FloatField()
            ),
            
            # Quality score based on engagement rate
            quality_score=Case(
                When(view_count__gt=0,
                     then=(F('like_count') + F('comment_count') * 2) / F('view_count')),
                default=Value(0.0),
                output_field=FloatField()
            ),
            
            # Author reputation (from connect profile)
            author_reputation=Case(
                When(author__connect_profile__isnull=False,
                     then=F('author__connect_profile__reputation_score') / 100.0),
                default=Value(0.5),
                output_field=FloatField()
            ),
            
            # Trending score (recent engagement)
            trending_score=Case(
                When(created_at__gte=now - timezone.timedelta(hours=self.TRENDING_WINDOW_HOURS),
                     then=F('engagement_score') * F('recency_score')),
                default=Value(0.0),
                output_field=FloatField()
            ),
            
            # Final composite score
            final_ranking_score=(
                F('follow_boost') +
                F('engagement_score') * self.ENGAGEMENT_WEIGHT +
                F('recency_score') * self.RECENCY_WEIGHT +
                F('quality_score') * self.QUALITY_WEIGHT +
                F('author_reputation') * self.REPUTATION_WEIGHT +
                F('trending_score') * self.TRENDING_WEIGHT
            )
        )
    
    def _annotate_general_scores(self, queryset):
        """Annotate queryset with general ranking scores (no personalization)"""
        now = timezone.now()
        
        return queryset.annotate(
            # Engagement score
            engagement_score=(
                F('like_count') * self.LIKE_WEIGHT +
                F('comment_count') * self.COMMENT_WEIGHT +
                F('share_count') * self.SHARE_WEIGHT +
                F('bookmark_count') * self.BOOKMARK_WEIGHT +
                F('view_count') * self.VIEW_WEIGHT
            ),
            
            # Recency score
            hours_since_creation=Case(
                When(created_at__gte=now - timezone.timedelta(hours=120),  # Within last 5 days
                     then=Value(1.0)),
                When(created_at__gte=now - timezone.timedelta(hours=240),  # Within last 10 days  
                     then=Value(5.0)),
                default=Value(24.0),
                output_field=FloatField()
            ),
            
            recency_score=Case(
                When(hours_since_creation__lte=self.RECENCY_HALF_LIFE_HOURS * 5,
                     then=Value(2.0) ** (-F('hours_since_creation') / self.RECENCY_HALF_LIFE_HOURS)),
                default=Value(0.01),
                output_field=FloatField()
            ),
            
            # Quality score
            quality_score=Case(
                When(view_count__gt=0,
                     then=(F('like_count') + F('comment_count') * 2) / F('view_count')),
                default=Value(0.0),
                output_field=FloatField()
            ),
            
            # Author reputation
            author_reputation=Case(
                When(author__connect_profile__isnull=False,
                     then=F('author__connect_profile__reputation_score') / 100.0),
                default=Value(0.5),
                output_field=FloatField()
            ),
            
            # Trending score
            trending_score=Case(
                When(created_at__gte=now - timezone.timedelta(hours=self.TRENDING_WINDOW_HOURS),
                     then=F('engagement_score') * F('recency_score')),
                default=Value(0.0),
                output_field=FloatField()
            ),
            
            # Final score (no follow boost)
            final_ranking_score=(
                F('engagement_score') * self.ENGAGEMENT_WEIGHT +
                F('recency_score') * self.RECENCY_WEIGHT +
                F('quality_score') * self.QUALITY_WEIGHT +
                F('author_reputation') * self.REPUTATION_WEIGHT +
                F('trending_score') * self.TRENDING_WEIGHT
            )
        )
    
    def calculate_and_store_ranking_scores(self, batch_size: int = 1000):
        """
        Calculate and store ranking scores for all posts
        This should be run periodically (e.g., every hour) as a background task
        """
        try:
            posts = Post.objects.filter(
                is_approved=True,
                is_draft=False
            ).select_related('author__connect_profile')
            
            total_posts = posts.count()
            logger.info(f"Calculating ranking scores for {total_posts} posts")
            
            for i in range(0, total_posts, batch_size):
                batch = posts[i:i + batch_size]
                self._calculate_batch_scores(batch)
                logger.info(f"Processed {min(i + batch_size, total_posts)}/{total_posts} posts")
            
            logger.info("Finished calculating ranking scores")
            
        except Exception as e:
            logger.error(f"Error calculating ranking scores: {e}")
    
    def _calculate_batch_scores(self, posts):
        """Calculate scores for a batch of posts"""
        ranking_scores = []
        now = timezone.now()
        
        for post in posts:
            try:
                # Calculate individual score components
                engagement_score = (
                    post.like_count * self.LIKE_WEIGHT +
                    post.comment_count * self.COMMENT_WEIGHT +
                    post.share_count * self.SHARE_WEIGHT +
                    post.bookmark_count * self.BOOKMARK_WEIGHT +
                    post.view_count * self.VIEW_WEIGHT
                )
                
                # Recency score with exponential decay
                hours_since = (now - post.created_at).total_seconds() / 3600
                recency_score = 2 ** (-hours_since / self.RECENCY_HALF_LIFE_HOURS) if hours_since <= self.RECENCY_HALF_LIFE_HOURS * 5 else 0.01
                
                # Quality score
                quality_score = 0.0
                if post.view_count > 0:
                    quality_score = (post.like_count + post.comment_count * 2) / post.view_count
                
                # Author reputation
                author_reputation = 0.5
                if hasattr(post.author, 'connect_profile') and post.author.connect_profile:
                    author_reputation = post.author.connect_profile.reputation_score / 100.0
                
                # Trending score
                trending_score = 0.0
                if hours_since <= self.TRENDING_WINDOW_HOURS:
                    trending_score = engagement_score * recency_score
                
                # Total score
                total_score = (
                    engagement_score * self.ENGAGEMENT_WEIGHT +
                    recency_score * self.RECENCY_WEIGHT +
                    quality_score * self.QUALITY_WEIGHT +
                    author_reputation * self.REPUTATION_WEIGHT +
                    trending_score * self.TRENDING_WEIGHT
                )
                
                # Create or update ranking score
                score, created = PostRankingScore.objects.update_or_create(
                    post=post,
                    defaults={
                        'engagement_score': engagement_score,
                        'recency_score': recency_score,
                        'quality_score': quality_score,
                        'author_reputation_score': author_reputation,
                        'trending_score': trending_score,
                        'total_score': total_score,
                    }
                )
                
                ranking_scores.append(score)
                
            except Exception as e:
                logger.error(f"Error calculating score for post {post.id}: {e}")
        
        return ranking_scores
    
    def track_user_interaction(self, user: User, post: Post, interaction_type: str, value: float = 1.0, metadata: Dict = None):
        """Track user interaction for future ranking improvements"""
        if not user.is_authenticated:
            return
        
        try:
            UserInteraction.objects.create(
                user=user,
                post=post,
                interaction_type=interaction_type,
                value=value,
                metadata=metadata or {}
            )
            
            # Clear user's ranking cache
            cache_pattern = f"ranked_posts_{user.id}_*"
            # Note: In production, you might want to use a more sophisticated cache invalidation
            
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
    
    def get_user_interest_profile(self, user: User) -> Dict:
        """
        Analyze user's interaction history to build interest profile
        This can be used for better personalization
        """
        if not user.is_authenticated:
            return {}
        
        cache_key = f"user_interests_{user.id}"
        interests = cache.get(cache_key)
        
        if interests is not None:
            return interests
        
        try:
            # Analyze user's interactions in the last 30 days
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            
            interactions = UserInteraction.objects.filter(
                user=user,
                created_at__gte=cutoff_date
            ).select_related('post').prefetch_related('post__topics')
            
            # Calculate interest scores by topic
            topic_scores = {}
            author_scores = {}
            
            for interaction in interactions:
                weight = self._get_interaction_weight(interaction.interaction_type)
                
                # Topic interests
                for topic in interaction.post.topics.all():
                    topic_scores[topic.slug] = topic_scores.get(topic.slug, 0) + weight
                
                # Author interests
                author_id = interaction.post.author_id
                author_scores[author_id] = author_scores.get(author_id, 0) + weight
            
            interests = {
                'topics': dict(sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:10]),
                'authors': dict(sorted(author_scores.items(), key=lambda x: x[1], reverse=True)[:10]),
                'calculated_at': timezone.now().isoformat()
            }
            
            # Cache for 6 hours
            cache.set(cache_key, interests, 21600)
            
            return interests
            
        except Exception as e:
            logger.error(f"Error calculating user interests: {e}")
            return {}
    
    def _get_interaction_weight(self, interaction_type: str) -> float:
        """Get weight for different interaction types"""
        weights = {
            'view': 0.1,
            'like': 1.0,
            'comment': 3.0,
            'share': 5.0,
            'bookmark': 2.0,
            'click_profile': 0.5,
            'click_link': 0.3,
            'time_spent': 0.01,  # Per second
        }
        return weights.get(interaction_type, 1.0)