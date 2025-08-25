# startup_hub/apps/posts/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F, Count, Exists, OuterRef, Prefetch
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.cache import cache
from apps.notifications.utils import notify_post_liked, notify_post_commented
import logging

from .models import (
    Topic, Post, Comment, PostReaction, CommentReaction,
    PostBookmark, PostView, PostShare, PostReport, Mention, UserInteraction, SeenPost,
    Poll, PollOption, PollVote
)
from .ranking import PostRankingService
from .serializers import (
    TopicSerializer, PostListSerializer, PostDetailSerializer,
    PostCreateSerializer, CommentSerializer, CommentCreateSerializer,
    PollSerializer, PollVoteSerializer,
    PostBookmarkSerializer, PostReportSerializer, PostReactionSerializer
)
from .permissions import IsAuthorOrReadOnly, CanModeratePost, IsNotLocked

logger = logging.getLogger(__name__)

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for topics/hashtags"""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending topics with caching"""
        cache_key = 'trending_topics'
        trending = cache.get(cache_key)
        
        if not trending:
            trending = self.queryset.order_by('-post_count')[:20]
            cache.set(cache_key, trending, 300)  # Cache for 5 minutes
            
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search topics with autocomplete"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({'error': 'Query must be at least 2 characters'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        topics = self.queryset.filter(
            Q(name__istartswith=query) | Q(name__icontains=query)
        ).distinct()[:10]
        
        serializer = self.get_serializer(topics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, slug=None):
        """Follow/unfollow a topic"""
        topic = self.get_object()
        user = request.user
        
        # This would need a TopicFollow model
        # For now, just return success
        return Response({'message': 'Topic followed successfully'})

class PostViewSet(viewsets.ModelViewSet):
    """Enhanced ViewSet for posts with real-time features"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    
    def get_queryset(self):
        queryset = Post.objects.filter(is_approved=True, is_draft=False)
        
        # Optimize query with select_related and prefetch_related
        queryset = queryset.select_related(
            'author', 'related_startup', 'related_job'
        ).prefetch_related(
            'topics',
            'images',
            'links',
            Prefetch(
                'reactions',
                queryset=PostReaction.objects.select_related('user')
            ),
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(
                    parent=None
                ).select_related('author').prefetch_related(
                    'replies',
                    'reactions'
                ).order_by('-created_at')
            )
        )
        
        # Annotate with user-specific data if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                user_has_liked=Exists(
                    PostReaction.objects.filter(
                        post=OuterRef('pk'),
                        user=self.request.user
                    )
                ),
                user_has_bookmarked=Exists(
                    PostBookmark.objects.filter(
                        post=OuterRef('pk'),
                        user=self.request.user
                    )
                )
            )
        
        # Apply filters
        params = self.request.query_params
        
        # Filter by post type
        post_type = params.get('type')
        if post_type:
            queryset = queryset.filter(post_type=post_type)
        
        # Filter by topic
        topic = params.get('topic')
        if topic:
            queryset = queryset.filter(topics__slug=topic)
        
        # Filter by author
        author = params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)
        
        # Filter by followed users (for following feed)
        if params.get('feed') == 'following' and self.request.user.is_authenticated:
            # Get followed users
            from apps.connect.models import Follow
            following_ids = Follow.objects.filter(
                follower=self.request.user
            ).values_list('following_id', flat=True)
            
            queryset = queryset.filter(
                Q(author_id__in=following_ids) |
                Q(author=self.request.user)
            )
        
        # Exclude seen posts if requested
        if params.get('exclude_seen') == 'true' and self.request.user.is_authenticated:
            seen_post_ids = SeenPost.objects.filter(
                user=self.request.user
            ).values_list('post_id', flat=True)
            
            queryset = queryset.exclude(id__in=seen_post_ids)
        
        # Search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(topics__name__icontains=search) |
                Q(author__username__icontains=search) |
                Q(author__first_name__icontains=search) |
                Q(author__last_name__icontains=search)
            ).distinct()
        
        # Time filter
        time_filter = params.get('time')
        if time_filter:
            now = timezone.now()
            if time_filter == 'today':
                queryset = queryset.filter(created_at__gte=now - timezone.timedelta(days=1))
            elif time_filter == 'week':
                queryset = queryset.filter(created_at__gte=now - timezone.timedelta(days=7))
            elif time_filter == 'month':
                queryset = queryset.filter(created_at__gte=now - timezone.timedelta(days=30))
            elif time_filter == 'year':
                queryset = queryset.filter(created_at__gte=now - timezone.timedelta(days=365))
        
        # Sorting
        sort = params.get('sort', 'new')
        if sort == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort == 'top':
            queryset = queryset.order_by('-like_count', '-created_at')
        elif sort == 'hot':
            # Hot algorithm: recent posts with high engagement
            queryset = queryset.annotate(
                engagement_score=F('like_count') + F('comment_count') * 2 + F('view_count') * 0.1
            ).order_by('-engagement_score', '-created_at')
        elif sort == 'discussed':
            queryset = queryset.order_by('-comment_count', '-created_at')
        elif sort == 'viewed':
            queryset = queryset.order_by('-view_count', '-created_at')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return PostCreateSerializer
        elif self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer
    
    def perform_create(self, serializer):
        print(f"🔍 Performing create for user: {self.request.user}")
        print(f"🔍 Request data: {self.request.data}")
        print(f"🔍 Request FILES: {self.request.FILES}")
        
        post = serializer.save(author=self.request.user)
        
        # Send notifications for mentions
        self._send_mention_notifications(post)
        
        # Update user's post count (if tracking)
        self._update_user_metrics(self.request.user, 'post_created')
    
    def retrieve(self, request, *args, **kwargs):
        """Get post details and track view"""
        instance = self.get_object()
        
        # Track unique view
        view_key = f"post_view_{instance.id}_{self.get_client_ip(request)}"
        if not cache.get(view_key):
            PostView.objects.create(
                post=instance,
                user=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request)
            )
            
            # Track as seen post for authenticated users
            if request.user.is_authenticated:
                SeenPost.objects.get_or_create(
                    user=request.user,
                    post=instance,
                    defaults={
                        'viewed_from': 'direct',
                    }
                )
            
            # Increment view count
            Post.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
            instance.refresh_from_db(fields=['view_count'])
            
            # Track interaction for ranking
            if request.user.is_authenticated:
                ranking_service = PostRankingService(user=request.user)
                ranking_service.track_user_interaction(
                    user=request.user,
                    post=instance,
                    interaction_type='view',
                    metadata={'ip_address': self.get_client_ip(request)}
                )
            
            # Cache to prevent duplicate views
            cache.set(view_key, True, 3600)  # 1 hour
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update post with edit tracking"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if can edit
        if not instance.can_edit(request.user):
            return Response(
                {'error': 'Cannot edit post after 30 minutes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Track edit
        instance.edited_at = timezone.now()
        instance.edit_count = F('edit_count') + 1
        
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        """Like/unlike a post (simplified to only support thumbs up)"""
        post = self.get_object()
        
        if request.method == 'DELETE':
            # Remove like
            try:
                reaction = PostReaction.objects.get(post=post, user=request.user)
                reaction.delete()
                
                # Update like count
                post.like_count = post.reactions.count()
                post.save(update_fields=['like_count'])
                
                return Response({
                    'success': True,
                    'message': 'Like removed',
                    'liked': False,
                    'like_count': post.like_count
                })
            except PostReaction.DoesNotExist:
                return Response(
                    {'error': 'You have not liked this post'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Add like
        with transaction.atomic():
            reaction, created = PostReaction.objects.get_or_create(
                post=post,
                user=request.user
            )
            
            # Update like count
            post.like_count = post.reactions.count()
            post.save(update_fields=['like_count'])
            
            # Track interaction for ranking
            if created:
                ranking_service = PostRankingService(user=request.user)
                ranking_service.track_user_interaction(
                    user=request.user,
                    post=post,
                    interaction_type='like',
                    metadata={}
                )
            
            # Send notification if new like
            if created and post.author != request.user:
                notify_post_liked(post, request.user)
        
        return Response({
            'success': True,
            'liked': True,
            'created': created,
            'like_count': post.like_count
        })
    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Toggle bookmark on post"""
        post = self.get_object()
        
        if request.method == 'DELETE':
            # Remove bookmark
            deleted, _ = PostBookmark.objects.filter(post=post, user=request.user).delete()
            if deleted:
                post.bookmark_count = F('bookmark_count') - 1
                post.save(update_fields=['bookmark_count'])
                return Response({
                    'success': True,
                    'bookmarked': False,
                    'message': 'Bookmark removed'
                })
            return Response({'error': 'Bookmark not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Add bookmark
        bookmark, created = PostBookmark.objects.get_or_create(
            post=post,
            user=request.user,
            defaults={'notes': request.data.get('notes', '')}
        )
        
        if created:
            post.bookmark_count = F('bookmark_count') + 1
            post.save(update_fields=['bookmark_count'])
            
            # Track interaction for ranking
            ranking_service = PostRankingService(user=request.user)
            ranking_service.track_user_interaction(
                user=request.user,
                post=post,
                interaction_type='bookmark',
                metadata={'notes': request.data.get('notes', '')}
            )
        
        return Response({
            'success': True,
            'bookmarked': True,
            'message': 'Post bookmarked' if created else 'Already bookmarked'
        })
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Track and handle post share"""
        post = self.get_object()
        platform = request.data.get('platform', 'copy_link')
        
        # Validate platform
        valid_platforms = [p[0] for p in PostShare.PLATFORMS]
        if platform not in valid_platforms:
            return Response(
                {'error': f'Invalid platform. Must be one of: {valid_platforms}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create share record
        PostShare.objects.create(
            post=post,
            user=request.user if request.user.is_authenticated else None,
            platform=platform
        )
        
        # Update share count
        post.share_count = F('share_count') + 1
        post.save(update_fields=['share_count'])
        
        # Track interaction for ranking
        if request.user.is_authenticated:
            ranking_service = PostRankingService(user=request.user)
            ranking_service.track_user_interaction(
                user=request.user,
                post=post,
                interaction_type='share',
                metadata={'platform': platform}
            )
        
        # Generate share URL based on platform
        share_urls = {
            'twitter': f"https://twitter.com/intent/tweet?text={post.title}&url=",
            'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url=",
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u=",
            'whatsapp': f"https://wa.me/?text=",
        }
        
        share_url = share_urls.get(platform, '')
        
        return Response({
            'success': True,
            'share_url': share_url,
            'share_count': post.shares.count()
        })
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """Report post with reason"""
        post = self.get_object()
        
        serializer = PostReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            report = serializer.save(
                post=post,
                reported_by=request.user
            )
            
            # Notify moderators
            self._notify_moderators(f"Post reported: {post.title}", report)
            
            return Response({
                'success': True,
                'message': 'Post reported successfully. Our team will review it.'
            })
        except Exception as e:
            if 'unique constraint' in str(e).lower():
                return Response(
                    {'error': 'You have already reported this post'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def comments_list(self, request, pk=None):
        """Simple endpoint to get comments"""
        try:
            post = self.get_object()
            comments = post.comments.filter(parent=None).select_related('author').order_by('created_at')
            
            return Response({
                'results': [
                    {
                        'id': str(c.id),
                        'content': c.content,
                        'author': {
                            'username': c.author.username,
                            'display_name': c.author.get_full_name() or c.author.username,
                            'avatar_url': c.author.get_avatar_url()
                        },
                        'time_since': 'recently',
                        'like_count': c.like_count
                    }
                    for c in comments
                ],
                'count': comments.count()
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.AllowAny])
    def comments(self, request, pk=None):
        """Get or create comments on the post"""
        post = self.get_object()
        
        if request.method == 'GET':
            try:
                # Get comments for the post - use simple data to avoid serializer issues
                comments = post.comments.filter(parent=None).order_by('created_at')
                
                comments_data = []
                for comment in comments:
                    try:
                        # Get replies for this comment (limit initial load to 3)
                        replies_data = []
                        all_replies = comment.replies.all().order_by('created_at')
                        total_replies = all_replies.count()
                        initial_replies = all_replies[:3]  # Load first 3 replies
                        
                        for reply in initial_replies:
                            try:
                                replies_data.append({
                                    'id': str(reply.id),
                                    'author': {
                                        'id': reply.author.id,
                                        'username': reply.author.username,
                                        'display_name': reply.author.get_full_name() or reply.author.username,
                                        'avatar_url': reply.author.get_avatar_url(),
                                    },
                                    'content': reply.content,
                                    'created_at': reply.created_at.isoformat(),
                                    'like_count': reply.like_count,
                                    'time_since': "recently",
                                    'is_liked': False,
                                })
                            except Exception as e:
                                logger.error(f"Error serializing reply {reply.id}: {e}")
                                continue
                        
                        comments_data.append({
                            'id': str(comment.id),
                            'author': {
                                'id': comment.author.id,
                                'username': comment.author.username,
                                'display_name': comment.author.get_full_name() or comment.author.username,
                                'avatar_url': comment.author.get_avatar_url(),
                            },
                            'content': comment.content,
                            'is_anonymous': comment.is_anonymous,
                            'created_at': comment.created_at.isoformat(),
                            'like_count': comment.like_count,
                            'reply_count': comment.reply_count,
                            'time_since': "recently",
                            'is_liked': False,
                            'can_edit': False,
                            'can_delete': False,
                            'replies': replies_data,
                            'has_more_replies': total_replies > 3,
                            'remaining_replies_count': max(0, total_replies - 3)
                        })
                    except Exception as e:
                        logger.error(f"Error serializing comment {comment.id}: {e}")
                        continue
                
                return Response({
                    'results': comments_data,
                    'count': len(comments_data)
                })
            except Exception as e:
                logger.error(f"Error in comments GET: {e}")
                import traceback
                traceback.print_exc()
                return Response(
                    {'error': f'Failed to fetch comments: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # POST request - create comment
        # Require authentication for POST
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to post comments'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Check if post is locked
        if post.is_locked:
            return Response(
                {'error': 'Comments are locked for this post'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create comment manually to avoid serializer issues
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=serializer.validated_data['content'],
            is_anonymous=serializer.validated_data.get('is_anonymous', False),
            parent=serializer.validated_data.get('parent', None)
        )
        
        # Update post comment count
        post.comment_count = F('comment_count') + 1
        post.save(update_fields=['comment_count'])
        
        # Track interaction for ranking
        ranking_service = PostRankingService(user=request.user)
        ranking_service.track_user_interaction(
            user=request.user,
            post=post,
            interaction_type='comment',
            metadata={
                'comment_id': str(comment.id),
                'is_anonymous': comment.is_anonymous,
                'parent_id': str(comment.parent.id) if comment.parent else None
            }
        )
        
        # Send notification to post author
        if post.author != request.user and not comment.is_anonymous:
            notify_post_commented(post, request.user, comment)
        
        # Return the created comment with simplified data
        return Response({
            'id': str(comment.id),
            'author': {
                'id': comment.author.id,
                'username': comment.author.username,
                'display_name': comment.author.get_full_name() or comment.author.username,
            },
            'content': comment.content,
            'time_since': 'just now',
            'like_count': 0,
            'is_liked': False,
            'created_at': comment.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def reactions_summary(self, request, pk=None):
        """Get detailed likes summary (simplified to only show likes)"""
        post = self.get_object()
        
        # Get all likes for the post
        likes = post.reactions.select_related('user')
        
        reactions = {}
        if likes.exists():
            reactions['like'] = {
                'emoji': '👍',
                'count': likes.count(),
                'users': [
                    {
                        'id': r.user.id,
                        'username': r.user.username,
                        'full_name': r.user.get_full_name() or r.user.username
                    } for r in likes[:5]  # Show first 5 users
                ],
                'has_more': likes.count() > 5
            }
        
        return Response(reactions)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending posts with enhanced algorithm"""
        # Time-based trending (last 24-48 hours)
        time_threshold = timezone.now() - timezone.timedelta(hours=48)
        
        trending = self.get_queryset().filter(
            created_at__gte=time_threshold
        ).annotate(
            # Enhanced engagement score
            engagement_score=(
                F('like_count') * 1 +
                F('comment_count') * 2 +
                F('share_count') * 3 +
                F('view_count') * 0.01
            )
        ).order_by('-engagement_score', '-created_at')[:20]
        
        serializer = self.get_serializer(trending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def following(self, request):
        """Get posts from followed users and topics"""
        # Get followed users
        from apps.connect.models import Follow
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)
        
        # Get posts from followed users and self
        posts = self.get_queryset().filter(
            Q(author_id__in=following_ids) |
            Q(author=request.user)
        ).distinct()
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def feed(self, request):
        """Get personalized feed for user"""
        feed_type = request.query_params.get('type', 'mixed')
        
        if feed_type == 'following':
            # Use existing following logic
            from apps.connect.models import Follow
            following_ids = Follow.objects.filter(
                follower=request.user
            ).values_list('following_id', flat=True)
            
            posts = self.get_queryset().filter(
                Q(author_id__in=following_ids) |
                Q(author=request.user)
            ).distinct()
        elif feed_type == 'trending':
            # Get trending posts
            posts = self.get_queryset().order_by('-view_count', '-like_count', '-created_at')
        else:
            # Mixed feed - combine different signals
            posts = self.get_queryset().order_by('-created_at')
        
        # Limit to recent posts (last 30 days)
        from datetime import timedelta
        recent_cutoff = timezone.now() - timedelta(days=30)
        posts = posts.filter(created_at__gte=recent_cutoff)
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def bookmarks(self, request):
        """Get user's bookmarked posts"""
        from .serializers import PostBookmarkSerializer
        
        bookmarks = PostBookmark.objects.filter(
            user=request.user
        ).select_related('post__author').order_by('-created_at')
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Posts bookmarks request from user: {request.user}")
        logger.info(f"Found {bookmarks.count()} bookmarks")
        
        try:
            page = self.paginate_queryset(bookmarks)
            if page is not None:
                serializer = PostBookmarkSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = PostBookmarkSerializer(bookmarks, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in posts bookmarks: {e}")
            # Return simple data structure without pagination for debugging
            simple_data = []
            for bookmark in bookmarks:
                simple_data.append({
                    'id': bookmark.id,
                    'created_at': bookmark.created_at,
                    'notes': bookmark.notes,
                    'post': {
                        'id': bookmark.post.id,
                        'title': bookmark.post.title,
                        'content_preview': bookmark.post.content[:200] if bookmark.post.content else '',
                        'author': {
                            'id': bookmark.post.author.id,
                            'username': bookmark.post.author.username,
                            'display_name': bookmark.post.author.get_full_name() or bookmark.post.author.username,
                            'avatar_url': bookmark.post.author.get_avatar_url(),
                        }
                    }
                })
            return Response(simple_data)
    
    @action(detail=False, methods=['get'])
    def ranked_feed(self, request):
        """
        Get intelligently ranked posts using sophisticated algorithm
        Considers followed users, engagement, recency, and user preferences
        """
        try:
            # Get pagination parameters
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            
            # Calculate offset
            offset = (page - 1) * page_size
            limit = page_size
            
            # Initialize ranking service
            ranking_service = PostRankingService(user=request.user if request.user.is_authenticated else None)
            
            # Get ranked posts
            ranked_posts = ranking_service.get_ranked_posts(limit=limit + 1, offset=offset)  # +1 to check if there are more
            
            # Check if there are more posts
            has_next = len(ranked_posts) > limit
            if has_next:
                ranked_posts = ranked_posts[:limit]  # Remove the extra post
            
            # Serialize the posts
            serializer = self.get_serializer(ranked_posts, many=True)
            
            # Return paginated response
            return Response({
                'results': serializer.data,
                'count': len(serializer.data),
                'page': page,
                'page_size': page_size,
                'has_next': has_next,
                'has_previous': page > 1,
                'algorithm_info': {
                    'personalized': request.user.is_authenticated,
                    'factors': [
                        'followed_users_boost',
                        'engagement_metrics',
                        'time_decay',
                        'quality_score',
                        'author_reputation',
                        'trending_score'
                    ]
                }
            })
            
        except Exception as e:
            logger.error(f"Error in ranked_feed: {e}")
            # Fallback to regular feed
            return self.list(request)
    
    @action(detail=False, methods=['get'])
    def smart_feed(self, request):
        """
        Alternative smart feed endpoint with additional personalization options
        """
        try:
            # Get user preferences
            boost_followed = request.query_params.get('boost_followed', 'true').lower() == 'true'
            include_topics = request.query_params.get('topics', '').split(',') if request.query_params.get('topics') else []
            exclude_seen = request.query_params.get('exclude_seen', 'false').lower() == 'true'
            
            # Initialize ranking service
            ranking_service = PostRankingService(user=request.user if request.user.is_authenticated else None)
            
            # Get user's interest profile if authenticated
            user_interests = {}
            if request.user.is_authenticated:
                user_interests = ranking_service.get_user_interest_profile(request.user)
            
            # Get base ranked posts
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            offset = (page - 1) * page_size
            
            ranked_posts = ranking_service.get_ranked_posts(limit=page_size + 10, offset=offset)
            
            # Apply additional filters
            if include_topics:
                ranked_posts = [p for p in ranked_posts if any(t.slug in include_topics for t in p.topics.all())]
            
            # Implement exclude_seen logic by tracking viewed posts
            if exclude_seen and request.user.is_authenticated:
                # Get IDs of posts that the user has already seen
                seen_post_ids = SeenPost.objects.filter(
                    user=request.user
                ).values_list('post_id', flat=True)
                
                # Filter out seen posts from the ranked posts
                ranked_posts = [p for p in ranked_posts if p.id not in seen_post_ids]
            
            # Limit to requested page size
            ranked_posts = ranked_posts[:page_size]
            
            # Serialize
            serializer = self.get_serializer(ranked_posts, many=True)
            
            return Response({
                'results': serializer.data,
                'count': len(serializer.data),
                'user_interests': user_interests if request.user.is_authenticated else None,
                'applied_filters': {
                    'boost_followed': boost_followed,
                    'include_topics': include_topics,
                    'exclude_seen': exclude_seen
                }
            })
            
        except Exception as e:
            logger.error(f"Error in smart_feed: {e}")
            return Response({'error': 'Failed to generate smart feed'}, status=500)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def view(self, request, pk=None):
        """Track post view"""
        post = self.get_object()
        
        # Create view record (avoid duplicates within 1 hour for same user/IP)
        ip_address = self.get_client_ip(request)
        user = request.user if request.user.is_authenticated else None
        
        # Check for recent view from same user/IP
        from datetime import timedelta
        recent_threshold = timezone.now() - timedelta(hours=1)
        
        existing_view = PostView.objects.filter(
            post=post,
            viewed_at__gte=recent_threshold
        )
        
        if user:
            existing_view = existing_view.filter(user=user)
        else:
            existing_view = existing_view.filter(ip_address=ip_address)
        
        if not existing_view.exists():
            PostView.objects.create(
                post=post,
                user=user,
                ip_address=ip_address
            )
            
            # Track as seen post for authenticated users
            if user:
                SeenPost.objects.get_or_create(
                    user=user,
                    post=post,
                    defaults={
                        'viewed_from': 'feed',
                    }
                )
            
            # Update view count
            Post.objects.filter(pk=post.pk).update(view_count=F('view_count') + 1)
            post.refresh_from_db(fields=['view_count'])
        
        return Response({'success': True, 'view_count': post.view_count})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_seen(self, request, pk=None):
        """Mark a post as seen by the user"""
        post = self.get_object()
        viewed_from = request.data.get('viewed_from', 'feed')
        view_duration = request.data.get('view_duration', None)
        
        seen_post, created = SeenPost.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={
                'viewed_from': viewed_from,
                'view_duration': view_duration,
            }
        )
        
        if not created and view_duration:
            # Update view duration if post was already seen
            seen_post.view_duration = view_duration
            seen_post.save(update_fields=['view_duration'])
        
        return Response({
            'success': True,
            'message': 'Post marked as seen',
            'already_seen': not created
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_multiple_as_seen(self, request):
        """Mark multiple posts as seen by the user"""
        post_ids = request.data.get('post_ids', [])
        viewed_from = request.data.get('viewed_from', 'feed')
        
        if not post_ids:
            return Response(
                {'error': 'post_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that all posts exist
        posts = Post.objects.filter(id__in=post_ids, is_approved=True)
        if posts.count() != len(post_ids):
            return Response(
                {'error': 'Some posts not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark all posts as seen
        seen_posts = []
        for post in posts:
            seen_post, created = SeenPost.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={
                    'viewed_from': viewed_from,
                }
            )
            seen_posts.append({
                'post_id': str(post.id),
                'newly_seen': created
            })
        
        return Response({
            'success': True,
            'message': f'Marked {len(seen_posts)} posts as seen',
            'results': seen_posts
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def seen_posts(self, request):
        """Get user's seen posts"""
        seen_posts = SeenPost.objects.filter(
            user=request.user
        ).select_related('post__author').order_by('-seen_at')
        
        # Get pagination parameters
        page = self.paginate_queryset(seen_posts)
        if page is not None:
            # Simple serialization for seen posts
            data = []
            for seen_post in page:
                data.append({
                    'post_id': str(seen_post.post.id),
                    'post_title': seen_post.post.title,
                    'post_author': seen_post.post.author.username,
                    'seen_at': seen_post.seen_at.isoformat(),
                    'viewed_from': seen_post.viewed_from,
                    'view_duration': seen_post.view_duration,
                })
            return self.get_paginated_response(data)
        
        # Non-paginated response
        data = []
        for seen_post in seen_posts:
            data.append({
                'post_id': str(seen_post.post.id),
                'post_title': seen_post.post.title,
                'post_author': seen_post.post.author.username,
                'seen_at': seen_post.seen_at.isoformat(),
                'viewed_from': seen_post.viewed_from,
                'view_duration': seen_post.view_duration,
            })
        
        return Response(data)
    
    @action(detail=False, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def clear_seen_posts(self, request):
        """Clear all seen posts for the user"""
        deleted_count = SeenPost.objects.filter(user=request.user).delete()[0]
        
        return Response({
            'success': True,
            'message': f'Cleared {deleted_count} seen posts',
            'deleted_count': deleted_count
        })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _send_notification(self, user, notification_type, message, **kwargs):
        """Send notification to user"""
        from apps.connect.models import Notification
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=message,
            message=message,
            **kwargs
        )
    
    def _send_mention_notifications(self, post):
        """Send notifications for mentions in post"""
        mentions = Mention.objects.filter(post=post).select_related('mentioned_user')
        for mention in mentions:
            if mention.mentioned_user != post.author:
                self._send_notification(
                    mention.mentioned_user,
                    'mention',
                    f"{post.author.get_full_name() or post.author.username} mentioned you in a post",
                    post_id=post.id,
                    from_user=post.author
                )
    
    def _notify_moderators(self, message, report):
        """Notify moderators about reports"""
        # Implementation depends on your moderation system
        pass
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote_poll(self, request, pk=None):
        """Vote in a poll"""
        post = self.get_object()
        
        # Check if post has a poll
        if not hasattr(post, 'poll'):
            return Response(
                {'error': 'This post does not have a poll.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        poll = post.poll
        option_id = request.data.get('option_id')
        
        if not option_id:
            return Response(
                {'error': 'option_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            option = poll.options.get(id=option_id)
        except PollOption.DoesNotExist:
            return Response(
                {'error': 'Invalid poll option.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the PollVoteSerializer for validation
        serializer = PollVoteSerializer(
            data={'option': option_id},
            context={'poll': poll, 'request': request}
        )
        
        if serializer.is_valid():
            # Create the vote
            with transaction.atomic():
                vote = PollVote.objects.create(
                    poll=poll,
                    option=option,
                    user=request.user
                )
                
                # Update counts
                option.vote_count = F('vote_count') + 1
                option.save(update_fields=['vote_count'])
                
                poll.total_votes = F('total_votes') + 1
                poll.save(update_fields=['total_votes'])
            
            # Return updated poll data
            poll_serializer = PollSerializer(poll, context={'request': request})
            return Response({
                'message': 'Vote recorded successfully.',
                'poll': poll_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def remove_poll_vote(self, request, pk=None):
        """Remove vote from a poll (for multiple choice polls)"""
        post = self.get_object()
        
        # Check if post has a poll
        if not hasattr(post, 'poll'):
            return Response(
                {'error': 'This post does not have a poll.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        poll = post.poll
        option_id = request.data.get('option_id')
        
        if not option_id:
            return Response(
                {'error': 'option_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vote = poll.votes.get(user=request.user, option_id=option_id)
        except PollVote.DoesNotExist:
            return Response(
                {'error': 'You have not voted for this option.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove the vote
        with transaction.atomic():
            vote.delete()
            
            # Update counts
            option = vote.option
            option.vote_count = F('vote_count') - 1
            option.save(update_fields=['vote_count'])
            
            poll.total_votes = F('total_votes') - 1
            poll.save(update_fields=['total_votes'])
        
        # Return updated poll data
        poll_serializer = PollSerializer(poll, context={'request': request})
        return Response({
            'message': 'Vote removed successfully.',
            'poll': poll_serializer.data
        })
    
    def _update_user_metrics(self, user, action):
        """Update user metrics and reputation"""
        try:
            profile = user.connect_profile
            if action == 'post_created':
                profile.reputation_score = F('reputation_score') + 5
                profile.save(update_fields=['reputation_score'])
        except:
            pass

class CommentViewSet(viewsets.ModelViewSet):
    """Enhanced ViewSet for comments with threading"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        queryset = Comment.objects.all()
        
        # Optimize with select_related and prefetch_related
        queryset = queryset.select_related('author', 'parent', 'post').prefetch_related(
            'replies__author',
            'reactions',
            'mentions'
        )
        
        # Filter by post if provided
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id, parent=None)
        
        # Filter by parent for thread view
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        
        return queryset.order_by('created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        
        # Update parent reply count if this is a reply
        if comment.parent:
            comment.parent.reply_count = F('reply_count') + 1
            comment.parent.save(update_fields=['reply_count'])
            
            # Notify parent comment author
            if comment.parent.author != self.request.user:
                self._send_notification(
                    comment.parent.author,
                    'reply',
                    f"{self.request.user.get_full_name() or self.request.user.username} replied to your comment",
                    post_id=comment.post.id,
                    comment_id=comment.id,
                    from_user=self.request.user
                )
    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """Like/unlike comment"""
        comment = self.get_object()
        
        if request.method == 'DELETE':
            # Unlike
            deleted, _ = CommentReaction.objects.filter(
                comment=comment,
                user=request.user
            ).delete()
            
            if deleted:
                comment.like_count = comment.reactions.filter(is_like=True).count()
                comment.save(update_fields=['like_count'])
                
                return Response({
                    'success': True,
                    'liked': False,
                    'like_count': comment.like_count
                })
            
            return Response({'error': 'Like not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Like comment
        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment,
            user=request.user,
            defaults={'is_like': True}
        )
        
        if not created:
            # Already liked
            return Response({
                'success': True,
                'liked': True,
                'like_count': comment.like_count,
                'message': 'Already liked'
            })
        
        # Update like count
        comment.like_count = comment.reactions.filter(is_like=True).count()
        comment.save(update_fields=['like_count'])
        
        return Response({
            'success': True,
            'liked': True,
            'like_count': comment.like_count
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def more_replies(self, request, pk=None):
        """Load more replies for a comment"""
        comment = self.get_object()
        
        # Get pagination parameters
        offset = int(request.query_params.get('offset', 3))  # Default to skip first 3
        limit = int(request.query_params.get('limit', 10))   # Load 10 more at a time
        
        try:
            # Get remaining replies
            all_replies = comment.replies.all().order_by('created_at')
            more_replies = all_replies[offset:offset + limit]
            remaining_after_load = max(0, all_replies.count() - offset - limit)
            
            replies_data = []
            for reply in more_replies:
                try:
                    replies_data.append({
                        'id': str(reply.id),
                        'author': {
                            'id': reply.author.id,
                            'username': reply.author.username,
                            'display_name': reply.author.get_full_name() or reply.author.username,
                            'avatar_url': reply.author.get_avatar_url(),
                        },
                        'content': reply.content,
                        'created_at': reply.created_at.isoformat(),
                        'like_count': reply.like_count,
                        'time_since': "recently",
                        'is_liked': False,
                    })
                except Exception as e:
                    logger.error(f"Error serializing reply {reply.id}: {e}")
                    continue
            
            return Response({
                'replies': replies_data,
                'has_more': remaining_after_load > 0,
                'remaining_count': remaining_after_load,
                'loaded_count': len(replies_data)
            })
            
        except Exception as e:
            logger.error(f"Error loading more replies: {e}")
            return Response(
                {'error': 'Failed to load more replies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _send_notification(self, user, notification_type, message, **kwargs):
        """Send notification to user"""
        from apps.connect.models import Notification
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=message,
            message=message,
            **kwargs
        )