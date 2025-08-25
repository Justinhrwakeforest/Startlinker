# apps/users/social_views.py - API Views for Enhanced Social Features
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Prefetch, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .social_models import (
    UserFollow, Story, StoryView, StartupCollaboration, CollaborationItem,
    CollaborationFollow, Achievement, UserAchievement, UserAchievementProgress,
    ScheduledPost, CollaborationCollaborator, ProjectTask, TaskComment,
    ProjectFile, ProjectMeeting, ProjectMilestone, CollaborationInvite
)
from apps.connect.models import Follow
from .social_serializers import (
    UserFollowSerializer, UserFollowCreateSerializer, StorySerializer,
    StoryViewSerializer, StartupCollaborationSerializer, CollaborationItemSerializer,
    AchievementSerializer, UserAchievementSerializer, ScheduledPostSerializer,
    UserSocialStatsSerializer, MentionUserSerializer, PersonalizedFeedSerializer,
    ProjectTaskSerializer, TaskCommentSerializer, ProjectFileSerializer,
    ProjectMeetingSerializer, ProjectMilestoneSerializer, CollaborationInviteSerializer
)
from apps.posts.models import Post
from apps.startups.models import Startup

User = get_user_model()

class SocialPagination(PageNumberPagination):
    """Custom pagination for social features"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserFollowViewSet(viewsets.ModelViewSet):
    """ViewSet for user follow relationships"""
    serializer_class = UserFollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        return UserFollow.objects.filter(
            follower=self.request.user
        ).select_related('follower', 'following')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserFollowCreateSerializer
        return UserFollowSerializer
    
    @action(detail=False, methods=['get'])
    def followers(self, request):
        """Get user's followers (current user by default, or specified user)"""
        user_id = request.query_params.get('user')
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            target_user = request.user
            
        followers = UserFollow.objects.filter(
            following=target_user
        ).select_related('follower', 'following')
        
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def following(self, request):
        """Get users that specified user is following (current user by default)"""
        user_id = request.query_params.get('user')
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            target_user = request.user
            
        following = UserFollow.objects.filter(
            follower=target_user
        ).select_related('follower', 'following')
        
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = self.get_serializer(page, many=True)  
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def follow_user(self, request):
        """Follow a user by username or ID"""
        user_identifier = request.data.get('user')
        if not user_identifier:
            return Response(
                {'error': 'User identifier required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find user by username or ID
        try:
            if user_identifier.isdigit():
                target_user = User.objects.get(id=user_identifier)
            else:
                target_user = User.objects.get(username=user_identifier)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already following
        if UserFollow.objects.filter(follower=request.user, following=target_user).exists():
            return Response(
                {'error': 'Already following this user'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create follow relationship
        follow = UserFollow.objects.create(
            follower=request.user,
            following=target_user,
            notify_on_posts=request.data.get('notify_on_posts', True),
            notify_on_stories=request.data.get('notify_on_stories', True),
            notify_on_achievements=request.data.get('notify_on_achievements', False)
        )
        
        # Update follower counts - use actual count to prevent sync issues
        target_user.follower_count = UserFollow.objects.filter(following=target_user).count()
        target_user.save(update_fields=['follower_count'])
        
        request.user.following_count = UserFollow.objects.filter(follower=request.user).count()
        request.user.save(update_fields=['following_count'])
        
        serializer = self.get_serializer(follow)
        
        # Return updated counts in response to help frontend stay in sync
        response_data = serializer.data
        response_data['updated_counts'] = {
            'follower_following_count': request.user.following_count,
            'target_follower_count': target_user.follower_count,
            'follower_user_id': request.user.id,
            'target_user_id': target_user.id
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def unfollow_user(self, request):
        """Unfollow a user"""
        user_identifier = request.data.get('user')
        if not user_identifier:
            return Response(
                {'error': 'User identifier required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if user_identifier.isdigit():
                target_user = User.objects.get(id=user_identifier)
            else:
                target_user = User.objects.get(username=user_identifier)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remove follow relationship
        deleted_count, _ = UserFollow.objects.filter(
            follower=request.user, 
            following=target_user
        ).delete()
        
        if deleted_count == 0:
            return Response(
                {'error': 'Not following this user'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update follower counts - use actual count to prevent sync issues
        target_user.follower_count = UserFollow.objects.filter(following=target_user).count()
        target_user.save(update_fields=['follower_count'])
        
        request.user.following_count = UserFollow.objects.filter(follower=request.user).count()
        request.user.save(update_fields=['following_count'])
        
        # Return updated counts in response to help frontend stay in sync
        return Response({
            'message': 'Successfully unfollowed user',
            'updated_counts': {
                'follower_following_count': request.user.following_count,
                'target_follower_count': target_user.follower_count,
                'follower_user_id': request.user.id,
                'target_user_id': target_user.id
            }
        })
    
    @action(detail=False, methods=['get'])
    def check_follow_status(self, request):
        """Check if current user is following a specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_following = UserFollow.objects.filter(
            follower=request.user, 
            following=target_user
        ).exists()
        
        return Response({
            'is_following': is_following,
            'user_id': int(user_id),
            'username': target_user.username
        })

class StoryViewSet(viewsets.ModelViewSet):
    """ViewSet for stories"""
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        queryset = Story.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'related_startup', 'related_job')
        
        # Filter by story type
        story_type = self.request.query_params.get('type')
        if story_type:
            queryset = queryset.filter(story_type=story_type)
        
        # Filter by author
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def view_story(self, request, pk=None):
        """Mark story as viewed"""
        story = self.get_object()
        
        # Create or update view record
        view, created = StoryView.objects.get_or_create(
            story=story,
            viewer=request.user,
            defaults={'view_duration': request.data.get('duration', 0)}
        )
        
        if not created:
            # Update view duration if viewing again
            view.view_duration = request.data.get('duration', view.view_duration)
            view.save()
        else:
            # Increment story view count
            story.increment_view_count()
        
        return Response({'message': 'Story viewed'})
    
    @action(detail=True, methods=['get'])
    def viewers(self, request, pk=None):
        """Get story viewers"""
        story = self.get_object()
        
        # Only author can see viewers
        if story.author != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        viewers = StoryView.objects.filter(story=story).select_related('viewer')
        page = self.paginate_queryset(viewers)
        if page is not None:
            serializer = StoryViewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = StoryViewSerializer(viewers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """Get story feed from followed users and own stories only"""
        # Get list of users that current user is following
        following_users = UserFollow.objects.filter(
            follower=request.user
        ).values_list('following', flat=True)
        
        # Include user's own ID to see their own stories
        user_ids = list(following_users) + [request.user.id]
        
        # Get stories only from followed users and self
        stories = Story.objects.filter(
            author__in=user_ids,
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author', 'related_startup', 'related_job')
        
        # Group by author for better UX
        stories_by_author = {}
        for story in stories.order_by('-created_at'):
            author_id = story.author.id
            if author_id not in stories_by_author:
                stories_by_author[author_id] = []
            stories_by_author[author_id].append(story)
        
        # Flatten and maintain order - put user's own stories first
        ordered_stories = []
        
        # Add user's own stories first
        if request.user.id in stories_by_author:
            ordered_stories.extend(stories_by_author[request.user.id])
            del stories_by_author[request.user.id]
        
        # Then add stories from followed users
        for author_stories in stories_by_author.values():
            ordered_stories.extend(author_stories)
        
        page = self.paginate_queryset(ordered_stories)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(ordered_stories, many=True)
        return Response(serializer.data)

class StartupCollaborationViewSet(viewsets.ModelViewSet):
    """ViewSet for startup collaborations"""
    serializer_class = StartupCollaborationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        queryset = StartupCollaboration.objects.select_related('owner').prefetch_related(
            'items__startup__industry'
        )
        
        # Filter by collaboration type
        collaboration_type = self.request.query_params.get('type')
        if collaboration_type:
            queryset = queryset.filter(collaboration_type=collaboration_type)
        
        # Filter by owner
        owner = self.request.query_params.get('owner')
        if owner:
            queryset = queryset.filter(owner__username=owner)
        
        # Only show public collaborations or user's own collaborations
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(collaboration_type='public') | 
                Q(owner=self.request.user) |
                Q(collaborators=self.request.user)
            ).distinct()
        
        return queryset.order_by('-updated_at')
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a collaboration"""
        collaboration = self.get_object()
        
        follow, created = CollaborationFollow.objects.get_or_create(
            user=request.user,
            collaboration=collaboration,
            defaults={'notify_on_updates': request.data.get('notify_on_updates', True)}
        )
        
        if created:
            # Increment follower count
            collaboration.follower_count += 1
            collaboration.save(update_fields=['follower_count'])
            return Response({'message': 'Collaboration followed'})
        else:
            return Response(
                {'error': 'Already following this collaboration'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post']) 
    def unfollow(self, request, pk=None):
        """Unfollow a collaboration"""
        collaboration = self.get_object()
        
        deleted_count, _ = CollaborationFollow.objects.filter(
            user=request.user,
            collection=collection
        ).delete()
        
        if deleted_count > 0:
            # Decrement follower count
            collection.follower_count = max(0, collection.follower_count - 1)
            collection.save(update_fields=['follower_count'])
            return Response({'message': 'Collection unfollowed'})
        else:
            return Response(
                {'error': 'Not following this collection'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        """Get or add items to collection"""
        collection = self.get_object()
        
        if request.method == 'GET':
            items = CollectionItem.objects.filter(
                collection=collection,
                is_active=True
            ).select_related('startup__industry', 'added_by').order_by('position', '-added_at')
            
            page = self.paginate_queryset(items)
            if page is not None:
                serializer = CollectionItemSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = CollectionItemSerializer(items, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Check if user can edit collection
            if not collection.can_edit(request.user):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = CollectionItemSerializer(
                data=request.data, 
                context={'request': request}
            )
            if serializer.is_valid():
                # Check if startup already in collection
                startup_id = serializer.validated_data['startup'].id
                if CollectionItem.objects.filter(
                    collection=collection, 
                    startup_id=startup_id,
                    is_active=True
                ).exists():
                    return Response(
                        {'error': 'Startup already in collection'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                serializer.save(collection=collection)
                
                # Update collection timestamp
                collection.save(update_fields=['updated_at'])
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for achievements (read-only)"""
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        queryset = Achievement.objects.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by rarity
        rarity = self.request.query_params.get('rarity')
        if rarity:
            queryset = queryset.filter(rarity=rarity)
        
        # Hide secret achievements unless earned
        if not self.request.user.is_staff:
            earned_achievements = UserAchievement.objects.filter(
                user=self.request.user
            ).values_list('achievement_id', flat=True)
            
            queryset = queryset.filter(
                Q(is_secret=False) | Q(id__in=earned_achievements)
            )
        
        return queryset.order_by('category', 'rarity', 'name')
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available achievement categories"""
        categories = Achievement.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct()
        
        return Response({
            'categories': [
                {'value': cat, 'label': cat.replace('_', ' ').title()}
                for cat in categories
            ]
        })

class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user achievements"""
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        return UserAchievement.objects.filter(
            user=self.request.user
        ).select_related('achievement', 'user').order_by('-earned_at')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get achievement statistics"""
        total_achievements = Achievement.objects.filter(is_active=True).count()
        earned_achievements = UserAchievement.objects.filter(user=request.user).count()
        total_points = UserAchievement.objects.filter(
            user=request.user
        ).aggregate(
            total=models.Sum('achievement__points')
        )['total'] or 0
        
        # Achievement breakdown by category
        category_stats = UserAchievement.objects.filter(
            user=request.user
        ).values('achievement__category').annotate(
            count=Count('id'),
            points=models.Sum('achievement__points')
        )
        
        return Response({
            'total_achievements': total_achievements,
            'earned_achievements': earned_achievements,
            'completion_percentage': (earned_achievements / total_achievements * 100) if total_achievements > 0 else 0,
            'total_points': total_points,
            'category_breakdown': list(category_stats)
        })

class ScheduledPostViewSet(viewsets.ModelViewSet):
    """ViewSet for scheduled posts"""
    serializer_class = ScheduledPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        return ScheduledPost.objects.filter(
            author=self.request.user
        ).order_by('scheduled_for')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled post"""
        scheduled_post = self.get_object()
        
        if not scheduled_post.can_cancel(request.user):
            return Response(
                {'error': 'Cannot cancel this post'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        scheduled_post.status = 'cancelled'
        scheduled_post.save(update_fields=['status'])
        
        return Response({'message': 'Post cancelled'})
    
    @action(detail=True, methods=['post'])
    def publish_now(self, request, pk=None):
        """Publish scheduled post immediately"""
        scheduled_post = self.get_object()
        
        if not scheduled_post.can_edit(request.user):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if scheduled_post.status != 'scheduled':
            return Response(
                {'error': 'Post is not in scheduled status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Publish the post immediately
        from .tasks import publish_scheduled_post
        result = publish_scheduled_post.delay(scheduled_post.id)
        
        return Response({'message': 'Post publishing initiated'})

# Social feed and discovery views
class SocialFeedViewSet(viewsets.ViewSet):
    """ViewSet for personalized social feeds"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """Get personalized feed with stories, posts, and collections"""
        # Get followed users
        following_users = UserFollow.objects.filter(
            follower=request.user
        ).values_list('following', flat=True)
        
        # Get recent stories from followed users
        stories = Story.objects.filter(
            author__in=following_users,
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('author')[:10]
        
        # Get recent posts from followed users  
        posts = Post.objects.filter(
            author__in=following_users,
            is_approved=True
        ).select_related('author')[:20]
        
        # Get recent collections from followed users
        collections = StartupCollaboration.objects.filter(
            owner__in=following_users
        ).select_related('owner')[:5]
        
        # Get recent achievements from followed users
        achievements = UserAchievement.objects.filter(
            user__in=following_users,
            is_public=True
        ).select_related('user', 'achievement')[:10]
        
        feed_data = {
            'stories': stories,
            'posts': posts,
            'collections': collections,
            'achievements': achievements
        }
        
        serializer = PersonalizedFeedSerializer(feed_data, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def discover(self, request):
        """Discover new users, collections, and content"""
        # Get trending collections
        trending_collections = StartupCollaboration.objects.filter(
            view_count__gte=10
        ).order_by('-view_count', '-updated_at')[:10]
        
        # Get recent achievements
        recent_achievements = UserAchievement.objects.filter(
            is_public=True,
            earned_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('user', 'achievement').order_by('-earned_at')[:15]
        
        # Get active story creators
        story_creators = User.objects.filter(
            stories__created_at__gte=timezone.now() - timedelta(hours=24),
            stories__is_active=True
        ).distinct().annotate(
            story_count=Count('stories')
        ).order_by('-story_count')[:10]
        
        return Response({
            'trending_collections': StartupCollaborationSerializer(
                trending_collections, many=True, context={'request': request}
            ).data,
            'recent_achievements': UserAchievementSerializer(
                recent_achievements, many=True
            ).data,
            'active_story_creators': MentionUserSerializer(
                story_creators, many=True
            ).data
        })

class UserMentionViewSet(viewsets.ViewSet):
    """ViewSet for user mentions autocomplete"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Search users for mentions"""
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response([])
        
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        serializer = MentionUserSerializer(users, many=True)
        return Response(serializer.data)

class UserSocialStatsViewSet(viewsets.ViewSet):
    """ViewSet for user social statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, pk=None):
        """Get social stats for a specific user"""
        user = get_object_or_404(User, pk=pk)
        
        # Calculate stats using real Follow model from connect app
        followers_count = Follow.objects.filter(following=user).count()
        following_count = Follow.objects.filter(follower=user).count()
        posts_count = Post.objects.filter(author=user).count()
        stories_count = Story.objects.filter(
            author=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        collections_count = StartupCollaboration.objects.filter(owner=user).count()
        achievements_count = UserAchievement.objects.filter(user=user).count()
        total_points = UserAchievement.objects.filter(user=user).aggregate(
            total=Sum('achievement__points')
        )['total'] or 0
        
        # Recent activity (only if viewing own profile or public)
        recent_stories = Story.objects.filter(
            author=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')[:5]
        
        recent_achievements = UserAchievement.objects.filter(
            user=user,
            is_public=True
        ).select_related('achievement').order_by('-earned_at')[:5]
        
        featured_collections = StartupCollaboration.objects.filter(
            owner=user
        ).order_by('-view_count')[:3]
        
        stats_data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'posts_count': posts_count,
            'stories_count': stories_count,
            'collections_count': collections_count,
            'achievements_count': achievements_count,
            'total_achievement_points': total_points,
            'recent_stories': recent_stories,
            'recent_achievements': recent_achievements,
            'featured_collections': featured_collections
        }
        
        serializer = UserSocialStatsSerializer(stats_data, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def suggested_users(self, request):
        """Get suggested users to follow"""
        current_user = request.user
        
        # Get users the current user is already following using real Follow model
        following_users = Follow.objects.filter(
            follower=current_user
        ).values_list('following_id', flat=True)
        
        # Get suggested users based on different criteria
        suggested_users = User.objects.filter(
            is_active=True
        ).exclude(
            id=current_user.id
        ).exclude(
            id__in=following_users
        ).annotate(
            follower_count_real=Count('follower_relationships', distinct=True),
            posts_count=Count('posts', distinct=True)
        ).order_by('-follower_count_real', '-posts_count', '-date_joined')[:10]
        
        from .social_serializers import MentionUserSerializer
        serializer = MentionUserSerializer(suggested_users, many=True)
        return Response({"suggested_users": serializer.data})

# ============================================================================
# COLLABORATION VIEWSETS - New project collaboration features  
# ============================================================================

class ProjectTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for project tasks"""
    serializer_class = ProjectTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        queryset = ProjectTask.objects.select_related(
            'assigned_to', 'created_by', 'project'
        ).prefetch_related('comments')
        
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            # Check if user has access to this project
            project = get_object_or_404(StartupCollaboration, id=project_id)
            if not project.can_view(self.request.user):
                return ProjectTask.objects.none()
        else:
            # Return tasks from projects user has access to
            accessible_projects = StartupCollaboration.objects.filter(
                Q(owner=self.request.user) |
                Q(collaborators=self.request.user) |
                Q(collaboration_type='public')
            ).distinct()
            queryset = queryset.filter(project__in=accessible_projects)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # Check if user can edit the project
        project = serializer.validated_data['project']
        if not project.can_edit(self.request.user):
            raise permissions.PermissionDenied("You don't have permission to add tasks to this project.")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to a user"""
        task = self.get_object()
        if not task.can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to assign this task.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                # Check if user is part of the project
                if not task.project.can_view(user):
                    return Response(
                        {'error': 'User is not part of this project.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                task.assigned_to = user
                task.save()
                
                serializer = self.get_serializer(task)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Unassign task
            task.assigned_to = None
            task.save()
            serializer = self.get_serializer(task)
            return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status"""
        task = self.get_object()
        if not task.can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to update this task.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status in ['todo', 'in_progress', 'review', 'completed', 'blocked']:
            task.status = new_status
            if new_status == 'completed':
                task.completed_at = timezone.now()
            else:
                task.completed_at = None
            task.save()
            
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Invalid status.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class TaskCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for task comments"""
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        task_id = self.request.query_params.get('task')
        if task_id:
            # Check if user has access to the task's project
            task = get_object_or_404(ProjectTask, id=task_id)
            if not task.project.can_view(self.request.user):
                return TaskComment.objects.none()
            return TaskComment.objects.filter(task_id=task_id).select_related('author')
        return TaskComment.objects.none()
    
    def perform_create(self, serializer):
        task = serializer.validated_data['task']
        if not task.project.can_view(self.request.user):
            raise permissions.PermissionDenied("You don't have permission to comment on this task.")
        serializer.save()

class ProjectFileViewSet(viewsets.ModelViewSet):
    """ViewSet for project files"""
    serializer_class = ProjectFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        if project_id:
            project = get_object_or_404(StartupCollaboration, id=project_id)
            if not project.can_view(self.request.user):
                return ProjectFile.objects.none()
            return ProjectFile.objects.filter(project_id=project_id).select_related('uploaded_by')
        
        # Return files from projects user has access to
        accessible_projects = StartupCollaboration.objects.filter(
            Q(owner=self.request.user) |
            Q(collaborators=self.request.user) |
            Q(collaboration_type='public')
        ).distinct()
        return ProjectFile.objects.filter(project__in=accessible_projects).select_related('uploaded_by')
    
    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if not project.can_edit(self.request.user):
            raise permissions.PermissionDenied("You don't have permission to upload files to this project.")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Track file downloads"""
        file_obj = self.get_object()
        if not file_obj.project.can_view(request.user):
            return Response(
                {'error': 'You do not have permission to access this file.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        file_obj.download_count += 1
        file_obj.save(update_fields=['download_count'])
        
        return Response({'download_url': file_obj.file.url})

class ProjectMeetingViewSet(viewsets.ModelViewSet):
    """ViewSet for project meetings"""
    serializer_class = ProjectMeetingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        queryset = ProjectMeeting.objects.select_related('organizer', 'project').prefetch_related('attendees')
        
        if project_id:
            project = get_object_or_404(StartupCollaboration, id=project_id)
            if not project.can_view(self.request.user):
                return ProjectMeeting.objects.none()
            queryset = queryset.filter(project_id=project_id)
        else:
            # Return meetings from projects user has access to
            accessible_projects = StartupCollaboration.objects.filter(
                Q(owner=self.request.user) |
                Q(collaborators=self.request.user) |
                Q(collaboration_type='public')
            ).distinct()
            queryset = queryset.filter(project__in=accessible_projects)
        
        return queryset.order_by('scheduled_at')
    
    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if not project.can_edit(self.request.user):
            raise permissions.PermissionDenied("You don't have permission to schedule meetings for this project.")
        serializer.save()

class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    """ViewSet for project milestones"""
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        queryset = ProjectMilestone.objects.select_related('created_by', 'project').prefetch_related('related_tasks')
        
        if project_id:
            project = get_object_or_404(StartupCollaboration, id=project_id)
            if not project.can_view(self.request.user):
                return ProjectMilestone.objects.none()
            queryset = queryset.filter(project_id=project_id)
        else:
            # Return milestones from projects user has access to
            accessible_projects = StartupCollaboration.objects.filter(
                Q(owner=self.request.user) |
                Q(collaborators=self.request.user) |
                Q(collaboration_type='public')
            ).distinct()
            queryset = queryset.filter(project__in=accessible_projects)
        
        return queryset.order_by('target_date')
    
    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if not project.can_edit(self.request.user):
            raise permissions.PermissionDenied("You don't have permission to create milestones for this project.")
        serializer.save()

class CollaborationInviteViewSet(viewsets.ModelViewSet):
    """ViewSet for collaboration invitations"""
    serializer_class = CollaborationInviteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SocialPagination
    
    def get_queryset(self):
        # Return invites sent by or received by the current user
        return CollaborationInvite.objects.filter(
            Q(inviter=self.request.user) | Q(invitee=self.request.user)
        ).select_related('inviter', 'invitee', 'project').order_by('-created_at')
    
    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if not project.can_edit(self.request.user):
            raise permissions.PermissionDenied("You don't have permission to invite users to this project.")
        
        # Check if team is not full
        if project.team_size >= project.max_team_size:
            raise serializers.ValidationError("Project team is full.")
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept collaboration invitation"""
        invite = self.get_object()
        if invite.invitee != request.user:
            return Response(
                {'error': 'You can only accept invitations sent to you.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if invite.status != 'pending':
            return Response(
                {'error': 'Invitation has already been responded to.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invite.is_expired:
            invite.status = 'expired'
            invite.save()
            return Response(
                {'error': 'Invitation has expired.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user as collaborator
        from .social_models import CollectionCollaborator
        CollectionCollaborator.objects.get_or_create(
            collection=invite.project,
            user=request.user,
            defaults={
                'permission_level': invite.permission_level,
                'added_by': invite.inviter
            }
        )
        
        invite.status = 'accepted'
        invite.responded_at = timezone.now()
        invite.save()
        
        serializer = self.get_serializer(invite)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline collaboration invitation"""
        invite = self.get_object()
        if invite.invitee != request.user:
            return Response(
                {'error': 'You can only decline invitations sent to you.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if invite.status != 'pending':
            return Response(
                {'error': 'Invitation has already been responded to.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invite.status = 'declined'
        invite.responded_at = timezone.now()
        invite.save()
        
        serializer = self.get_serializer(invite)
        return Response(serializer.data)