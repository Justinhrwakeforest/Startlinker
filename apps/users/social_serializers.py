# apps/users/social_serializers.py - Serializers for Enhanced Social Features
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .social_models import (
    UserFollow, Story, StoryView, StartupCollaboration, CollaborationItem, 
    CollaborationFollow, Achievement, UserAchievement, UserAchievementProgress,
    ScheduledPost, CollaborationCollaborator, ProjectTask, TaskComment,
    ProjectFile, ProjectMeeting, ProjectMilestone, CollaborationInvite
)
from apps.startups.models import Startup
from apps.posts.models import Post

User = get_user_model()

class UserFollowSerializer(serializers.ModelSerializer):
    """Serializer for user follow relationships"""
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    follower_avatar = serializers.CharField(source='follower.get_avatar_url', read_only=True)
    follower_display_name = serializers.CharField(source='follower.get_display_name', read_only=True)
    
    following_username = serializers.CharField(source='following.username', read_only=True)
    following_avatar = serializers.CharField(source='following.get_avatar_url', read_only=True)
    following_display_name = serializers.CharField(source='following.get_display_name', read_only=True)
    
    is_mutual = serializers.SerializerMethodField()
    
    class Meta:
        model = UserFollow
        fields = [
            'id', 'follower', 'following', 'created_at',
            'follower_username', 'follower_avatar', 'follower_display_name',
            'following_username', 'following_avatar', 'following_display_name',
            'notify_on_posts', 'notify_on_stories', 'notify_on_achievements',
            'is_mutual'
        ]
        read_only_fields = ['created_at']
    
    def get_is_mutual(self, obj):
        """Check if the follow relationship is mutual"""
        return UserFollow.get_mutual_follows(obj.follower, obj.following)

class UserFollowCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating follow relationships"""
    class Meta:
        model = UserFollow
        fields = ['following', 'notify_on_posts', 'notify_on_stories', 'notify_on_achievements']
    
    def create(self, validated_data):
        validated_data['follower'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_following(self, value):
        """Validate that user is not trying to follow themselves"""
        if value == self.context['request'].user:
            raise serializers.ValidationError("You cannot follow yourself.")
        return value

class StorySerializer(serializers.ModelSerializer):
    """Serializer for stories"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.CharField(source='author.get_avatar_url', read_only=True)
    author_display_name = serializers.CharField(source='author.get_display_name', read_only=True)
    
    related_startup_name = serializers.CharField(source='related_startup.name', read_only=True)
    related_job_title = serializers.CharField(source='related_job.title', read_only=True)
    
    is_expired = serializers.BooleanField(read_only=True)
    time_remaining = serializers.FloatField(read_only=True)
    has_viewed = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'author', 'author_username', 'author_avatar', 'author_display_name',
            'story_type', 'text_content', 'image', 'video', 'video_metadata', 'image_metadata', 'link_url', 'link_title', 
            'link_description', 'related_startup', 'related_startup_name',
            'related_job', 'related_job_title', 'background_color', 'text_color',
            'view_count', 'is_expired', 'time_remaining', 'has_viewed',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['author', 'view_count', 'created_at', 'expires_at']
    
    def get_has_viewed(self, obj):
        """Check if current user has viewed this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryView.objects.filter(story=obj, viewer=request.user).exists()
        return False
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class StoryViewSerializer(serializers.ModelSerializer):
    """Serializer for story views"""
    viewer_username = serializers.CharField(source='viewer.username', read_only=True)
    viewer_avatar = serializers.CharField(source='viewer.get_avatar_url', read_only=True)
    
    class Meta:
        model = StoryView
        fields = ['id', 'viewer', 'viewer_username', 'viewer_avatar', 'viewed_at', 'view_duration']
        read_only_fields = ['viewer', 'viewed_at']

class StartupCollaborationSerializer(serializers.ModelSerializer):
    """Serializer for startup collaborations"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_avatar = serializers.CharField(source='owner.get_avatar_url', read_only=True)
    owner_display_name = serializers.CharField(source='owner.get_display_name', read_only=True)
    
    startup_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    collaborator_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StartupCollaboration
        fields = [
            'id', 'owner', 'owner_username', 'owner_avatar', 'owner_display_name',
            'name', 'description', 'collaboration_type', 'cover_image', 'theme_color',
            'is_featured', 'allow_comments', 'startup_count', 'view_count', 
            'follower_count', 'is_following', 'can_edit', 'collaborator_count',
            # New collaboration fields
            'project_type', 'status', 'goals', 'requirements', 'timeline',
            'start_date', 'end_date', 'max_team_size', 'skills_needed',
            'communication_methods', 'meeting_frequency', 'metadata',
            # Computed fields
            'task_count', 'completed_task_count', 'progress_percentage', 'team_size', 'is_project',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'view_count', 'follower_count', 'task_count', 'completed_task_count', 'progress_percentage', 'team_size', 'is_project', 'created_at', 'updated_at']
    
    def get_is_following(self, obj):
        """Check if current user follows this collaboration"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CollaborationFollow.objects.filter(user=request.user, collaboration=obj).exists()
        return False
    
    def get_can_edit(self, obj):
        """Check if current user can edit this collaboration"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_collaborator_count(self, obj):
        """Get number of collaborators"""
        return obj.collaborators.count()
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class CollaborationItemSerializer(serializers.ModelSerializer):
    """Serializer for collaboration items"""
    startup_name = serializers.CharField(source='startup.name', read_only=True)
    startup_logo = serializers.CharField(source='startup.logo', read_only=True)
    startup_description = serializers.CharField(source='startup.description', read_only=True)
    startup_industry = serializers.CharField(source='startup.industry.name', read_only=True)
    startup_location = serializers.CharField(source='startup.location', read_only=True)
    startup_average_rating = serializers.FloatField(source='startup.average_rating', read_only=True)
    
    added_by_username = serializers.CharField(source='added_by.username', read_only=True)
    
    class Meta:
        model = CollaborationItem
        fields = [
            'id', 'collaboration', 'startup', 'startup_name', 'startup_logo',
            'startup_description', 'startup_industry', 'startup_location',
            'startup_average_rating', 'added_by', 'added_by_username',
            'custom_note', 'custom_tags', 'position', 'added_at'
        ]
        read_only_fields = ['added_by', 'added_at']
    
    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user
        return super().create(validated_data)

class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for achievements"""
    rarity_color = serializers.CharField(source='get_rarity_color', read_only=True)
    earned_by_user = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'rarity', 'rarity_color',
            'icon', 'color', 'image', 'points', 'badge_text', 'is_secret',
            'is_repeatable', 'earned_count', 'earned_by_user', 'user_progress'
        ]
    
    def get_earned_by_user(self, obj):
        """Check if current user has earned this achievement"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserAchievement.objects.filter(user=request.user, achievement=obj).exists()
        return False
    
    def get_user_progress(self, obj):
        """Get current user's progress towards this achievement"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserAchievementProgress.objects.get(user=request.user, achievement=obj)
                return {
                    'progress_percentage': progress.progress_percentage,
                    'current_progress': progress.current_progress,
                    'is_completed': progress.is_completed
                }
            except UserAchievementProgress.DoesNotExist:
                return {
                    'progress_percentage': 0.0,
                    'current_progress': {},
                    'is_completed': False
                }
        return None

class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user achievements"""
    achievement_name = serializers.CharField(source='achievement.name', read_only=True)
    achievement_description = serializers.CharField(source='achievement.description', read_only=True)
    achievement_icon = serializers.CharField(source='achievement.icon', read_only=True)
    achievement_color = serializers.CharField(source='achievement.color', read_only=True)
    achievement_rarity = serializers.CharField(source='achievement.rarity', read_only=True)
    achievement_rarity_color = serializers.CharField(source='achievement.get_rarity_color', read_only=True)
    achievement_points = serializers.IntegerField(source='achievement.points', read_only=True)
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.CharField(source='user.get_avatar_url', read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'user', 'user_username', 'user_avatar', 'achievement',
            'achievement_name', 'achievement_description', 'achievement_icon',
            'achievement_color', 'achievement_rarity', 'achievement_rarity_color',
            'achievement_points', 'earned_at', 'is_pinned', 'is_public'
        ]
        read_only_fields = ['user', 'achievement', 'earned_at']

class ScheduledPostSerializer(serializers.ModelSerializer):
    """Serializer for scheduled posts"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    is_ready_to_publish = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ScheduledPost
        fields = [
            'id', 'author', 'author_username', 'title', 'content', 'post_type',
            'scheduled_for', 'status', 'images_data', 'links_data', 'topics_data',
            'related_startup', 'related_job', 'is_anonymous', 'error_message',
            'can_edit', 'can_cancel', 'is_ready_to_publish', 'created_at', 'published_at'
        ]
        read_only_fields = ['author', 'status', 'error_message', 'created_at', 'published_at']
    
    def get_can_edit(self, obj):
        """Check if current user can edit this scheduled post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_can_cancel(self, obj):
        """Check if current user can cancel this scheduled post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_cancel(request.user)
        return False
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_scheduled_for(self, value):
        """Validate that scheduled time is in the future"""
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value

class UserSocialStatsSerializer(serializers.Serializer):
    """Serializer for user social statistics"""
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    posts_count = serializers.IntegerField()
    stories_count = serializers.IntegerField()
    collections_count = serializers.IntegerField()
    achievements_count = serializers.IntegerField()
    total_achievement_points = serializers.IntegerField()
    
    # Recent activity
    recent_stories = StorySerializer(many=True, read_only=True)
    recent_achievements = UserAchievementSerializer(many=True, read_only=True)
    featured_collaborations = StartupCollaborationSerializer(many=True, read_only=True)

class MentionUserSerializer(serializers.ModelSerializer):
    """Serializer for user mentions autocomplete"""
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    avatar = serializers.CharField(source='get_avatar_url', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar']

# Feed serializers for personalized content
class PersonalizedFeedSerializer(serializers.Serializer):
    """Serializer for personalized feed content"""
    stories = StorySerializer(many=True, read_only=True)
    posts = serializers.SerializerMethodField()
    collaborations = StartupCollaborationSerializer(many=True, read_only=True)
    achievements = UserAchievementSerializer(many=True, read_only=True)
    
    def get_posts(self, obj):
        """Get posts with additional context"""
        from apps.posts.serializers import PostSerializer
        return PostSerializer(obj.get('posts', []), many=True, context=self.context).data

# ============================================================================
# COLLABORATION SERIALIZERS - New project collaboration features
# ============================================================================

class ProjectTaskSerializer(serializers.ModelSerializer):
    """Serializer for project tasks"""
    assigned_to_username = serializers.SerializerMethodField()
    assigned_to_avatar = serializers.SerializerMethodField()
    assigned_to_display_name = serializers.SerializerMethodField()
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_by_display_name = serializers.SerializerMethodField()
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    can_edit = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectTask
        fields = [
            'id', 'project', 'project_name', 'title', 'description', 'status', 'priority',
            'assigned_to', 'assigned_to_username', 'assigned_to_avatar', 'assigned_to_display_name',
            'created_by', 'created_by_username', 'created_by_display_name',
            'due_date', 'estimated_hours', 'actual_hours', 'attachments',
            'created_at', 'updated_at', 'completed_at', 'can_edit', 'comments_count'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'completed_at']
    
    def get_assigned_to_username(self, obj):
        """Get assigned user's username"""
        return obj.assigned_to.username if obj.assigned_to else None
    
    def get_assigned_to_avatar(self, obj):
        """Get assigned user's avatar"""
        return obj.assigned_to.get_avatar_url() if obj.assigned_to else None
    
    def get_assigned_to_display_name(self, obj):
        """Get assigned user's display name"""
        return obj.assigned_to.get_display_name() if obj.assigned_to else None
    
    def get_created_by_display_name(self, obj):
        """Get creator's display name"""
        return obj.created_by.get_display_name() if obj.created_by else None
    
    def get_can_edit(self, obj):
        """Check if current user can edit this task"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.can_edit(request.user)
            except Exception:
                return False
        return False
    
    def get_comments_count(self, obj):
        """Get number of comments on this task"""
        return obj.comments.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.CharField(source='author.get_avatar_url', read_only=True)
    author_display_name = serializers.CharField(source='author.get_display_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = [
            'id', 'task', 'author', 'author_username', 'author_avatar', 'author_display_name',
            'content', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class ProjectFileSerializer(serializers.ModelSerializer):
    """Serializer for project files"""
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    uploaded_by_display_name = serializers.CharField(source='uploaded_by.get_display_name', read_only=True)
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    file_url = serializers.CharField(source='file.url', read_only=True)
    
    class Meta:
        model = ProjectFile
        fields = [
            'id', 'project', 'project_name', 'name', 'description', 'category',
            'file', 'file_url', 'file_size', 'file_type', 'version', 'is_latest',
            'uploaded_by', 'uploaded_by_username', 'uploaded_by_display_name',
            'is_public', 'tags', 'download_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uploaded_by', 'file_size', 'download_count', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)

class ProjectMeetingSerializer(serializers.ModelSerializer):
    """Serializer for project meetings"""
    organizer_username = serializers.CharField(source='organizer.username', read_only=True)
    organizer_display_name = serializers.CharField(source='organizer.get_display_name', read_only=True)
    
    attendees_data = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectMeeting
        fields = [
            'id', 'project', 'project_name', 'title', 'description', 'agenda',
            'scheduled_at', 'duration_minutes', 'status', 'meeting_url', 'location',
            'organizer', 'organizer_username', 'organizer_display_name',
            'attendees', 'attendees_data', 'notes', 'action_items', 'recording_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['organizer', 'created_at', 'updated_at']
    
    def get_attendees_data(self, obj):
        """Get attendees with their details"""
        return [
            {
                'id': user.id,
                'username': user.username,
                'display_name': user.get_display_name(),
                'avatar': user.get_avatar_url()
            }
            for user in obj.attendees.all()
        ]
    
    def create(self, validated_data):
        attendees = validated_data.pop('attendees', [])
        validated_data['organizer'] = self.context['request'].user
        meeting = super().create(validated_data)
        meeting.attendees.set(attendees)
        return meeting

class ProjectMilestoneSerializer(serializers.ModelSerializer):
    """Serializer for project milestones"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_by_display_name = serializers.CharField(source='created_by.get_display_name', read_only=True)
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    related_tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMilestone
        fields = [
            'id', 'project', 'project_name', 'title', 'description', 'status',
            'target_date', 'completed_date', 'progress_percentage',
            'created_by', 'created_by_username', 'created_by_display_name',
            'related_tasks_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_related_tasks_count(self, obj):
        """Get number of related tasks"""
        return obj.related_tasks.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class CollaborationInviteSerializer(serializers.ModelSerializer):
    """Serializer for collaboration invitations"""
    inviter_username = serializers.CharField(source='inviter.username', read_only=True)
    inviter_display_name = serializers.CharField(source='inviter.get_display_name', read_only=True)
    inviter_avatar = serializers.CharField(source='inviter.get_avatar_url', read_only=True)
    
    invitee_username = serializers.CharField(source='invitee.username', read_only=True)
    invitee_display_name = serializers.CharField(source='invitee.get_display_name', read_only=True)
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_type = serializers.CharField(source='project.project_type', read_only=True)
    
    is_expired = serializers.BooleanField(read_only=True)
    
    # Add fields for frontend compatibility
    invitee_email = serializers.EmailField(write_only=True, required=False)
    role = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CollaborationInvite
        fields = [
            'id', 'project', 'project_name', 'project_type',
            'inviter', 'inviter_username', 'inviter_display_name', 'inviter_avatar',
            'invitee', 'invitee_username', 'invitee_display_name',
            'message', 'role_description', 'status', 'permission_level',
            'created_at', 'expires_at', 'responded_at', 'is_expired',
            'invitee_email', 'role'
        ]
        read_only_fields = ['inviter', 'status', 'created_at', 'responded_at']
        extra_kwargs = {
            'invitee': {'required': False},
            'expires_at': {'required': False}
        }
    
    def to_internal_value(self, data):
        """Convert invitee_email to invitee before validation"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Handle invitee_email -> invitee conversion
        if 'invitee_email' in data and 'invitee' not in data:
            try:
                user = User.objects.get(email=data['invitee_email'])
                data = data.copy()  # Make a copy to avoid mutating original
                data['invitee'] = user.pk
            except User.DoesNotExist:
                # Let validation handle the error
                pass
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation"""
        # Validate that invitee is provided (after to_internal_value conversion)
        if not data.get('invitee'):
            # Check if original data had invitee_email
            invitee_email = self.initial_data.get('invitee_email')
            if invitee_email:
                raise serializers.ValidationError(f"User with email {invitee_email} not found.")
            else:
                raise serializers.ValidationError("Invitee is required.")
            
        return data
    
    def create(self, validated_data):
        validated_data['inviter'] = self.context['request'].user
        
        # Remove frontend-only fields
        validated_data.pop('invitee_email', None)
        
        # Handle role -> permission_level conversion
        role = validated_data.pop('role', None)
        if role:
            role_mapping = {
                'member': 'edit',
                'admin': 'admin', 
                'viewer': 'view',
                'editor': 'edit'
            }
            validated_data['permission_level'] = role_mapping.get(role, 'edit')
        
        # Set expiration to 7 days from now if not provided
        if 'expires_at' not in validated_data:
            from django.utils import timezone
            validated_data['expires_at'] = timezone.now() + timezone.timedelta(days=7)
            
        return super().create(validated_data)