# startup_hub/apps/connect/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from .models import (
    UserProfile, Follow, Space, SpaceMembership, Event, EventRegistration,
    CofounderMatch, MatchScore, ResourceTemplate, Notification
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

class UserProfileSerializer(serializers.ModelSerializer):
    """Enhanced user profile serializer"""
    user = UserSerializer(read_only=True)
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    mutual_connections = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'display_name', 'avatar_url', 'headline',
            'expertise', 'looking_for', 'linkedin_url', 'twitter_handle',
            'github_username', 'personal_website', 'is_open_to_opportunities',
            'preferred_contact_method', 'reputation_score', 'helpful_votes',
            'follower_count', 'following_count', 'badges', 'is_online',
            'last_seen', 'created_at', 'is_following', 'mutual_connections',
            'recent_activity', 'show_online_status', 'allow_direct_messages'
        ]
        read_only_fields = [
            'reputation_score', 'helpful_votes', 'follower_count',
            'following_count', 'is_online', 'last_seen', 'created_at'
        ]
    
    def get_display_name(self, obj):
        return obj.display_name
    
    def get_avatar_url(self, obj):
        if obj.avatar_url:
            return obj.avatar_url
        # Generate default avatar
        name = obj.display_name
        return f"https://ui-avatars.com/api/?name={name}&background=6366f1&color=fff"
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj.user:
            return Follow.objects.filter(
                follower=request.user,
                following=obj.user
            ).exists()
        return False
    
    def get_mutual_connections(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj.user:
            # Get users that both follow
            my_following = set(
                Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            their_following = set(
                Follow.objects.filter(follower=obj.user).values_list('following_id', flat=True)
            )
            mutual = my_following.intersection(their_following)
            return len(mutual)
        return 0
    
    def get_recent_activity(self, obj):
        # Get last 5 activities
        activities = []
        
        # Recent posts
        recent_posts = obj.user.posts.filter(is_approved=True)[:2]
        for post in recent_posts:
            activities.append({
                'type': 'post',
                'title': post.title or 'New post',
                'time': post.created_at,
                'id': str(post.id)
            })
        
        # Recent events hosted
        recent_events = obj.user.hosted_events.filter(is_published=True)[:2]
        for event in recent_events:
            activities.append({
                'type': 'event',
                'title': f'Hosting: {event.title}',
                'time': event.created_at,
                'id': str(event.id)
            })
        
        # Sort by time and return top 5
        activities.sort(key=lambda x: x['time'], reverse=True)
        return activities[:5]

class FollowSerializer(serializers.ModelSerializer):
    """Follow relationship serializer"""
    follower_profile = serializers.SerializerMethodField()
    following_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at', 
                 'follower_profile', 'following_profile']
        read_only_fields = ['created_at']
    
    def get_follower_profile(self, obj):
        if hasattr(obj.follower, 'connect_profile'):
            return UserProfileSerializer(
                obj.follower.connect_profile,
                context=self.context
            ).data
        return None
    
    def get_following_profile(self, obj):
        if hasattr(obj.following, 'connect_profile'):
            return UserProfileSerializer(
                obj.following.connect_profile,
                context=self.context
            ).data
        return None

class SpaceMembershipSerializer(serializers.ModelSerializer):
    """Space membership serializer"""
    user_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = SpaceMembership
        fields = ['id', 'user', 'role', 'is_approved', 'joined_at', 'user_profile']
    
    def get_user_profile(self, obj):
        if hasattr(obj.user, 'connect_profile'):
            return UserProfileSerializer(
                obj.user.connect_profile,
                context=self.context
            ).data
        return None

class SpaceSerializer(serializers.ModelSerializer):
    """Space serializer"""
    created_by_profile = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    member_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Space
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'cover_image_url',
            'space_type', 'created_by', 'created_by_profile', 'member_count',
            'post_count', 'created_at', 'updated_at', 'is_member', 'member_role',
            'auto_approve_members', 'allow_member_posts'
        ]
        read_only_fields = ['slug', 'created_by', 'member_count', 'post_count']
    
    def get_created_by_profile(self, obj):
        if obj.created_by and hasattr(obj.created_by, 'connect_profile'):
            return UserProfileSerializer(
                obj.created_by.connect_profile,
                context=self.context
            ).data
        return None
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.memberships.filter(
                user=request.user,
                is_approved=True
            ).exists()
        return False
    
    def get_member_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.memberships.filter(user=request.user).first()
            return membership.role if membership else None
        return None

class SpaceDetailSerializer(SpaceSerializer):
    """Detailed space serializer"""
    moderators = UserSerializer(many=True, read_only=True)
    recent_members = serializers.SerializerMethodField()
    recent_posts = serializers.SerializerMethodField()
    upcoming_events = serializers.SerializerMethodField()
    
    class Meta(SpaceSerializer.Meta):
        fields = SpaceSerializer.Meta.fields + [
            'moderators', 'recent_members', 'recent_posts', 'upcoming_events',
            'require_post_approval'
        ]
    
    def get_recent_members(self, obj):
        recent_memberships = obj.memberships.filter(
            is_approved=True
        ).select_related('user__connect_profile').order_by('-joined_at')[:5]
        
        return SpaceMembershipSerializer(recent_memberships, many=True).data
    
    def get_recent_posts(self, obj):
        # This would need integration with posts app
        return []
    
    def get_upcoming_events(self, obj):
        from django.utils import timezone
        upcoming = obj.events.filter(
            start_datetime__gt=timezone.now(),
            is_published=True,
            is_cancelled=False
        ).order_by('start_datetime')[:3]
        
        return EventSerializer(upcoming, many=True, context=self.context).data

class EventSerializer(serializers.ModelSerializer):
    """Event serializer"""
    host_profile = serializers.SerializerMethodField()
    space_info = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    attendee_count = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'start_datetime',
            'end_datetime', 'timezone', 'is_online', 'location', 'meeting_url',
            'host', 'host_profile', 'space', 'space_info', 'requires_registration',
            'max_attendees', 'registration_deadline', 'is_published', 'is_cancelled',
            'created_at', 'is_upcoming', 'is_ongoing', 'is_registered',
            'attendee_count', 'can_register'
        ]
        read_only_fields = ['host', 'is_upcoming', 'is_ongoing']
    
    def get_host_profile(self, obj):
        if hasattr(obj.host, 'connect_profile'):
            return UserProfileSerializer(
                obj.host.connect_profile,
                context=self.context
            ).data
        return None
    
    def get_space_info(self, obj):
        if obj.space:
            return {
                'id': str(obj.space.id),
                'name': obj.space.name,
                'icon': obj.space.icon
            }
        return None
    
    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user,
                status__in=['registered', 'waitlisted']
            ).exists()
        return False
    
    def get_attendee_count(self, obj):
        return obj.registrations.filter(status='registered').count()
    
    def get_can_register(self, obj):
        if obj.is_cancelled or not obj.is_upcoming:
            return False
        
        if obj.registration_deadline:
            from django.utils import timezone
            if timezone.now() > obj.registration_deadline:
                return False
        
        if obj.max_attendees:
            current_count = self.get_attendee_count(obj)
            return current_count < obj.max_attendees
        
        return True

class EventRegistrationSerializer(serializers.ModelSerializer):
    """Event registration serializer"""
    event_info = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'user', 'status', 'registered_at',
            'registration_notes', 'event_info', 'user_info'
        ]
        read_only_fields = ['user', 'registered_at']
    
    def get_event_info(self, obj):
        return {
            'id': str(obj.event.id),
            'title': obj.event.title,
            'start_datetime': obj.event.start_datetime,
            'event_type': obj.event.event_type
        }
    
    def get_user_info(self, obj):
        profile = getattr(obj.user, 'connect_profile', None)
        return {
            'id': obj.user.id,
            'display_name': profile.display_name if profile else obj.user.username,
            'avatar_url': profile.avatar_url if profile else None
        }

class CofounderMatchSerializer(serializers.ModelSerializer):
    """Co-founder match profile serializer"""
    user_profile = serializers.SerializerMethodField()
    industry_names = serializers.SerializerMethodField()
    
    class Meta:
        model = CofounderMatch
        fields = [
            'id', 'user', 'user_profile', 'skills', 'experience_years',
            'commitment_level', 'equity_expectation', 'looking_for_skills',
            'startup_stage_preference', 'industry_preferences', 'industry_names',
            'bio', 'achievements', 'ideal_cofounder', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_user_profile(self, obj):
        if hasattr(obj.user, 'connect_profile'):
            return UserProfileSerializer(
                obj.user.connect_profile,
                context=self.context
            ).data
        return None
    
    def get_industry_names(self, obj):
        return [ind.name for ind in obj.industry_preferences.all()]

class MatchScoreSerializer(serializers.ModelSerializer):
    """Match score serializer"""
    other_user_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = MatchScore
        fields = [
            'id', 'user1', 'user2', 'overall_score', 'skills_complementarity',
            'interest_alignment', 'experience_balance', 'calculated_at',
            'other_user_profile'
        ]
    
    def get_other_user_profile(self, obj):
        request = self.context.get('request')
        if request and request.user == obj.user1:
            other_user = obj.user2
        else:
            other_user = obj.user1
        
        if hasattr(other_user, 'connect_profile'):
            return UserProfileSerializer(
                other_user.connect_profile,
                context=self.context
            ).data
        return None

class ResourceTemplateSerializer(serializers.ModelSerializer):
    """Resource template serializer"""
    contributor_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceTemplate
        fields = [
            'id', 'title', 'description', 'category', 'content', 'file_url',
            'preview_image_url', 'tags', 'is_premium', 'download_count',
            'contributed_by', 'contributor_info', 'created_at'
        ]
        read_only_fields = ['download_count', 'contributed_by', 'created_at']
    
    def get_contributor_info(self, obj):
        if obj.contributed_by and hasattr(obj.contributed_by, 'connect_profile'):
            profile = obj.contributed_by.connect_profile
            return {
                'id': obj.contributed_by.id,
                'display_name': profile.display_name,
                'avatar_url': profile.avatar_url
            }
        return None

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    from_user_info = serializers.SerializerMethodField()
    action_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'from_user',
            'from_user_info', 'post_id', 'comment_id', 'space_id', 'event_id',
            'is_read', 'read_at', 'created_at', 'action_url'
        ]
        read_only_fields = ['created_at']
    
    def get_from_user_info(self, obj):
        if obj.from_user and hasattr(obj.from_user, 'connect_profile'):
            profile = obj.from_user.connect_profile
            return {
                'id': obj.from_user.id,
                'display_name': profile.display_name,
                'avatar_url': profile.avatar_url,
                'username': obj.from_user.username
            }
        return None
    
    def get_action_url(self, obj):
        # Generate appropriate URL based on notification type
        if obj.post_id:
            return f'/posts/{obj.post_id}'
        elif obj.comment_id:
            return f'/posts/{obj.post_id}#comment-{obj.comment_id}'
        elif obj.space_id:
            return f'/connect/spaces/{obj.space_id}'
        elif obj.event_id:
            return f'/connect/events/{obj.event_id}'
        elif obj.from_user and obj.notification_type == 'follow':
            return f'/connect/profile/{obj.from_user.username}'
        return None