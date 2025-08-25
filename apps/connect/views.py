# startup_hub/apps/connect/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, F, Count, Avg, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import json

from .models import (
    UserProfile, Follow, Space, SpaceMembership, Event, EventRegistration,
    CofounderMatch, MatchScore, ResourceTemplate, Notification
)
from .serializers import (
    UserProfileSerializer, FollowSerializer, SpaceSerializer,
    SpaceDetailSerializer, EventSerializer, EventRegistrationSerializer,
    CofounderMatchSerializer, MatchScoreSerializer, 
    ResourceTemplateSerializer, NotificationSerializer
)
from .utils import calculate_match_score, send_notification_email

User = get_user_model()

class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profiles in Connect"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserProfile.objects.select_related('user').prefetch_related(
            'user__following_relationships',
            'user__follower_relationships'
        )
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(headline__icontains=search) |
                Q(expertise__icontains=search)
            )
        
        # Filter by expertise
        expertise = self.request.query_params.get('expertise')
        if expertise:
            queryset = queryset.filter(expertise__contains=expertise)
        
        # Filter by looking_for
        looking_for = self.request.query_params.get('looking_for')
        if looking_for:
            queryset = queryset.filter(looking_for__contains=looking_for)
        
        # Filter by open to opportunities
        open_to_opportunities = self.request.query_params.get('open_to_opportunities')
        if open_to_opportunities is not None:
            queryset = queryset.filter(is_open_to_opportunities=open_to_opportunities.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        """Update current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow/unfollow a user"""
        profile = self.get_object()
        target_user = profile.user
        
        if target_user == request.user:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        
        if not created:
            follow.delete()
            # Update follower counts
            profile.follower_count = F('follower_count') - 1
            profile.save()
            
            requester_profile = request.user.connect_profile
            requester_profile.following_count = F('following_count') - 1
            requester_profile.save()
            
            return Response({'message': 'Unfollowed successfully', 'is_following': False})
        
        # Update follower counts
        profile.follower_count = F('follower_count') + 1
        profile.save()
        
        requester_profile = request.user.connect_profile
        requester_profile.following_count = F('following_count') + 1
        requester_profile.save()
        
        # Send notification
        Notification.objects.create(
            user=target_user,
            notification_type='follow',
            title='New Follower',
            message=f'{request.user.get_full_name() or request.user.username} started following you',
            from_user=request.user
        )
        
        return Response({'message': 'Followed successfully', 'is_following': True})
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get user recommendations based on interests and activity"""
        # Get users with similar interests
        user_profile = request.user.connect_profile
        
        similar_users = UserProfile.objects.exclude(
            user=request.user
        ).filter(
            Q(expertise__overlap=user_profile.expertise) |
            Q(looking_for__overlap=user_profile.looking_for)
        ).annotate(
            mutual_connections=Count(
                'user__follower_relationships',
                filter=Q(user__follower_relationships__follower__in=request.user.following_relationships.values('following'))
            )
        ).order_by('-mutual_connections', '-reputation_score')[:10]
        
        serializer = self.get_serializer(similar_users, many=True)
        return Response(serializer.data)

class FollowViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for follow relationships"""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        follow_type = self.request.query_params.get('type', 'following')
        
        if follow_type == 'followers':
            return Follow.objects.filter(following=user).select_related(
                'follower', 'follower__connect_profile'
            )
        else:
            return Follow.objects.filter(follower=user).select_related(
                'following', 'following__connect_profile'
            )

class SpaceViewSet(viewsets.ModelViewSet):
    """ViewSet for Connect Spaces"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SpaceDetailSerializer
        return SpaceSerializer
    
    def get_queryset(self):
        queryset = Space.objects.all()
        
        # Filter by space type
        space_type = self.request.query_params.get('type')
        if space_type:
            queryset = queryset.filter(space_type=space_type)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter user's spaces
        if self.request.user.is_authenticated:
            my_spaces = self.request.query_params.get('my_spaces')
            if my_spaces:
                queryset = queryset.filter(
                    memberships__user=self.request.user,
                    memberships__is_approved=True
                )
        
        return queryset.select_related('created_by').prefetch_related('moderators')
    
    def perform_create(self, serializer):
        space = serializer.save(created_by=self.request.user)
        
        # Add creator as admin member
        SpaceMembership.objects.create(
            space=space,
            user=self.request.user,
            role='admin',
            is_approved=True
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a space"""
        space = self.get_object()
        
        membership, created = SpaceMembership.objects.get_or_create(
            space=space,
            user=request.user,
            defaults={
                'is_approved': space.auto_approve_members or space.space_type == 'public'
            }
        )
        
        if not created:
            return Response({'error': 'Already a member'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update member count
        space.member_count = F('member_count') + 1
        space.save()
        
        return Response({
            'message': 'Joined successfully' if membership.is_approved else 'Membership request sent',
            'is_approved': membership.is_approved
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a space"""
        space = self.get_object()
        
        try:
            membership = SpaceMembership.objects.get(space=space, user=request.user)
            
            if membership.role == 'admin' and space.memberships.filter(role='admin').count() == 1:
                return Response(
                    {'error': 'Cannot leave space as the only admin'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            membership.delete()
            
            # Update member count
            space.member_count = F('member_count') - 1
            space.save()
            
            return Response({'message': 'Left space successfully'})
        except SpaceMembership.DoesNotExist:
            return Response({'error': 'Not a member'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get space members"""
        space = self.get_object()
        memberships = space.memberships.filter(
            is_approved=True
        ).select_related('user', 'user__connect_profile')
        
        members_data = []
        for membership in memberships:
            profile = membership.user.connect_profile
            members_data.append({
                'user_id': membership.user.id,
                'username': membership.user.username,
                'display_name': profile.display_name,
                'avatar_url': profile.avatar_url,
                'headline': profile.headline,
                'role': membership.role,
                'joined_at': membership.joined_at
            })
        
        return Response(members_data)

class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for Events"""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Event.objects.filter(is_published=True, is_cancelled=False)
        
        # Filter by time
        time_filter = self.request.query_params.get('filter')
        now = timezone.now()
        
        if time_filter == 'upcoming':
            queryset = queryset.filter(start_datetime__gt=now)
        elif time_filter == 'past':
            queryset = queryset.filter(end_datetime__lt=now)
        elif time_filter == 'ongoing':
            queryset = queryset.filter(start_datetime__lte=now, end_datetime__gte=now)
        
        # Filter by type
        event_type = self.request.query_params.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by space
        space_id = self.request.query_params.get('space')
        if space_id:
            queryset = queryset.filter(space_id=space_id)
        
        return queryset.select_related('host', 'space').prefetch_related('registrations')
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register for an event"""
        event = self.get_object()
        
        if event.is_cancelled:
            return Response({'error': 'Event is cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        
        if event.registration_deadline and timezone.now() > event.registration_deadline:
            return Response({'error': 'Registration deadline passed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already registered
        if EventRegistration.objects.filter(event=event, user=request.user).exists():
            return Response({'error': 'Already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check capacity
        current_registrations = event.registrations.filter(
            status__in=['registered', 'attended']
        ).count()
        
        if event.max_attendees and current_registrations >= event.max_attendees:
            status_value = 'waitlisted'
        else:
            status_value = 'registered'
        
        registration = EventRegistration.objects.create(
            event=event,
            user=request.user,
            status=status_value
        )
        
        # Send confirmation notification
        Notification.objects.create(
            user=request.user,
            notification_type='event_reminder',
            title=f'{"Registered" if status_value == "registered" else "Waitlisted"} for {event.title}',
            message=f'You have been {status_value} for the event',
            event_id=event.id
        )
        
        serializer = EventRegistrationSerializer(registration)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel_registration(self, request, pk=None):
        """Cancel event registration"""
        event = self.get_object()
        
        try:
            registration = EventRegistration.objects.get(event=event, user=request.user)
            registration.status = 'cancelled'
            registration.cancelled_at = timezone.now()
            registration.save()
            
            return Response({'message': 'Registration cancelled'})
        except EventRegistration.DoesNotExist:
            return Response({'error': 'Not registered'}, status=status.HTTP_404_NOT_FOUND)

class CofounderMatchViewSet(viewsets.ModelViewSet):
    """ViewSet for Co-founder Matching"""
    serializer_class = CofounderMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CofounderMatch.objects.filter(
            user=self.request.user,
            is_active=True
        )
    
    def perform_create(self, serializer):
        # Deactivate existing profiles
        CofounderMatch.objects.filter(user=self.request.user).update(is_active=False)
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def matches(self, request):
        """Get potential co-founder matches"""
        try:
            user_profile = CofounderMatch.objects.get(user=request.user, is_active=True)
        except CofounderMatch.DoesNotExist:
            return Response({'error': 'Create a co-founder profile first'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get potential matches
        potential_matches = CofounderMatch.objects.exclude(
            user=request.user
        ).filter(
            is_active=True,
            startup_stage_preference=user_profile.startup_stage_preference
        )
        
        # Calculate match scores
        matches_with_scores = []
        for match in potential_matches:
            score = calculate_match_score(user_profile, match)
            
            # Store or update match score
            MatchScore.objects.update_or_create(
                user1=request.user,
                user2=match.user,
                defaults={
                    'overall_score': score['overall'],
                    'skills_complementarity': score['skills'],
                    'interest_alignment': score['interests'],
                    'experience_balance': score['experience']
                }
            )
            
            if score['overall'] > 60:  # Only show good matches
                matches_with_scores.append({
                    'profile': CofounderMatchSerializer(match).data,
                    'score': score
                })
        
        # Sort by score
        matches_with_scores.sort(key=lambda x: x['score']['overall'], reverse=True)
        
        return Response(matches_with_scores[:20])  # Top 20 matches

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('from_user').order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        now = timezone.now()
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=now)
        
        return Response({'message': f'{updated} notifications marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark single notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'count': count})

class ResourceTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for Resource Templates"""
    serializer_class = ResourceTemplateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = ResourceTemplate.objects.all()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by premium status
        if not self.request.user.is_authenticated or not getattr(self.request.user, 'is_premium', False):
            queryset = queryset.filter(is_premium=False)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Track resource download"""
        resource = self.get_object()
        
        # All resources are now free to access
        # Premium restriction removed
        
        # Update download count
        resource.download_count = F('download_count') + 1
        resource.save()
        
        return Response({
            'download_url': resource.file_url,
            'content': resource.content if not resource.file_url else None
        })

# Additional API endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_stats(request):
    """Get user statistics for Connect"""
    user = request.user
    profile = user.connect_profile
    
    stats = {
        'profile': {
            'reputation_score': profile.reputation_score,
            'helpful_votes': profile.helpful_votes,
            'follower_count': profile.follower_count,
            'following_count': profile.following_count,
            'badges': profile.badges
        },
        'activity': {
            'posts_created': user.posts.count(),
            'comments_made': user.comments.count(),
            'reactions_given': user.post_reactions.count() + user.comment_reactions.count(),
            'events_attended': user.event_registrations.filter(status='attended').count(),
            'spaces_joined': user.space_memberships.filter(is_approved=True).count()
        },
        'engagement': {
            'total_post_views': user.posts.aggregate(total=Count('views'))['total'] or 0,
            'total_post_likes': user.posts.aggregate(total=Count('reactions'))['total'] or 0,
            'avg_post_engagement': user.posts.aggregate(
                avg=Avg(F('like_count') + F('comment_count'))
            )['avg'] or 0
        }
    }
    
    return Response(stats)

@api_view(['GET'])
def search_users(request):
    """Search users across the platform"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'results': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).select_related('connect_profile')[:20]
    
    results = []
    for user in users:
        profile = getattr(user, 'connect_profile', None)
        results.append({
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'avatar_url': profile.avatar_url if profile else None,
            'headline': profile.headline if profile else '',
            'is_verified': user.is_staff
        })
    
    return Response({'results': results})

@api_view(['GET'])
def get_trending_users(request):
    """Get trending users based on recent activity"""
    # Users with highest engagement in last 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    trending = User.objects.filter(
        posts__created_at__gte=thirty_days_ago
    ).annotate(
        recent_posts=Count('posts', filter=Q(posts__created_at__gte=thirty_days_ago)),
        total_engagement=Count('posts__reactions') + Count('posts__comments'),
        follower_growth=Count(
            'follower_relationships',
            filter=Q(follower_relationships__created_at__gte=thirty_days_ago)
        )
    ).order_by('-total_engagement', '-follower_growth')[:10]
    
    results = []
    for user in trending:
        profile = getattr(user, 'connect_profile', None)
        results.append({
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'avatar_url': profile.avatar_url if profile else None,
            'headline': profile.headline if profile else '',
            'recent_posts': user.recent_posts,
            'total_engagement': user.total_engagement
        })
    
    return Response(results)