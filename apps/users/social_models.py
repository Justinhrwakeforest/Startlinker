# apps/users/social_models.py - Enhanced Social Features Models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid
from datetime import timedelta, date

User = get_user_model()

class UserPoints(models.Model):
    """User points and scoring system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    total_points = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)  # Never decreases
    points_this_month = models.PositiveIntegerField(default=0)
    points_this_week = models.PositiveIntegerField(default=0)
    
    # Point categories
    achievement_points = models.PositiveIntegerField(default=0)
    content_points = models.PositiveIntegerField(default=0)
    social_points = models.PositiveIntegerField(default=0)
    startup_points = models.PositiveIntegerField(default=0)
    job_points = models.PositiveIntegerField(default=0)
    
    # Tracking
    last_updated = models.DateTimeField(auto_now=True)
    last_weekly_reset = models.DateTimeField(auto_now_add=True)
    last_monthly_reset = models.DateTimeField(auto_now_add=True)
    
    # Level system
    level = models.PositiveIntegerField(default=1)
    level_progress = models.FloatField(default=0.0)  # Progress to next level (0-100%)
    
    class Meta:
        indexes = [
            models.Index(fields=['-total_points']),
            models.Index(fields=['-lifetime_points']),
            models.Index(fields=['level', '-total_points']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.total_points} points (Level {self.level})"
    
    def add_points(self, points, category='general'):
        """Add points to user account"""
        self.total_points += points
        self.lifetime_points += points
        self.points_this_month += points
        self.points_this_week += points
        
        # Add to category
        if category == 'achievement':
            self.achievement_points += points
        elif category == 'content':
            self.content_points += points
        elif category == 'social':
            self.social_points += points
        elif category == 'startup':
            self.startup_points += points
        elif category == 'job':
            self.job_points += points
        
        # Calculate level
        self.calculate_level()
        self.save()
    
    def calculate_level(self):
        """Calculate user level based on total points"""
        # Level formula: Level = floor(sqrt(total_points / 100)) + 1
        import math
        new_level = max(1, int(math.sqrt(self.total_points / 100)) + 1)
        
        if new_level != self.level:
            self.level = new_level
        
        # Calculate progress to next level
        points_for_current_level = (self.level - 1) ** 2 * 100
        points_for_next_level = self.level ** 2 * 100
        
        if points_for_next_level > points_for_current_level:
            self.level_progress = min(100.0, 
                ((self.total_points - points_for_current_level) / 
                 (points_for_next_level - points_for_current_level)) * 100
            )
        else:
            self.level_progress = 100.0
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create points record for user"""
        points, created = cls.objects.get_or_create(user=user)
        return points

class PointsHistory(models.Model):
    """Track individual point transactions"""
    POINT_REASONS = [
        # Achievements
        ('achievement', 'Achievement Unlocked'),
        
        # Onboarding & Profile
        ('signup_bonus', 'Welcome Bonus'),
        ('email_verify', 'Email Verified'),
        ('phone_verify', 'Phone Verified'),
        ('profile_picture_upload', 'Profile Picture Added'),
        ('profile_bio_complete', 'Bio Added'),
        ('profile_location_add', 'Location Added'),
        ('profile_website_add', 'Website Added'),
        ('profile_complete', 'Profile Completed'),
        ('first_interests_select', 'Interests Selected'),
        
        # Engagement & Login
        ('daily_login', 'Daily Login'),
        ('login_streak_3', '3-Day Login Streak'),
        ('login_streak_7', '7-Day Login Streak'),
        ('login_streak_30', '30-Day Login Streak'),
        ('first_session', 'First Platform Visit'),
        
        # Content Creation
        ('first_post', 'First Post Created'),
        ('post_create', 'Post Created'),
        ('post_with_image', 'Post with Image'),
        ('post_with_video', 'Post with Video'),
        ('first_story', 'First Story Created'),
        ('story_create', 'Story Created'),
        ('story_with_media', 'Story with Media'),
        ('comment_create', 'Comment Added'),
        ('first_comment', 'First Comment'),
        
        # Startup Activities
        ('first_startup_submit', 'First Startup Submitted'),
        ('startup_submit', 'Startup Submitted'),
        ('startup_claim', 'Startup Claimed'),
        ('startup_verify', 'Startup Verified'),
        ('startup_update', 'Startup Updated'),
        ('startup_logo_upload', 'Startup Logo Added'),
        
        # Job Activities
        ('first_job_post', 'First Job Posted'),
        ('job_post', 'Job Posted'),
        ('job_apply', 'Applied for Job'),
        ('job_bookmark', 'Job Bookmarked'),
        ('resume_upload', 'Resume Uploaded'),
        ('resume_update', 'Resume Updated'),
        
        # Social Activities
        ('first_follow', 'First User Followed'),
        ('follow_user', 'User Followed'),
        ('get_followed', 'Gained Follower'),
        ('like_post', 'Post Liked'),
        ('share_post', 'Post Shared'),
        ('bookmark_post', 'Post Bookmarked'),
        ('join_community', 'Community Joined'),
        ('message_send', 'Message Sent'),
        ('first_message', 'First Message Sent'),
        
        # Milestones
        ('milestone_10_posts', '10 Posts Milestone'),
        ('milestone_50_posts', '50 Posts Milestone'),
        ('milestone_100_followers', '100 Followers Milestone'),
        ('milestone_verified', 'Account Verified'),
        
        # Bonuses & Special
        ('weekly_bonus', 'Weekly Activity Bonus'),
        ('monthly_bonus', 'Monthly Activity Bonus'),
        ('referral', 'User Referred'),
        ('early_adopter', 'Early Adopter Bonus'),
        ('beta_tester', 'Beta Tester Bonus'),
        ('feedback_submit', 'Feedback Submitted'),
        ('bug_report', 'Bug Reported'),
        
        # Streaks & Consistency
        ('posting_streak_7', '7-Day Posting Streak'),
        ('posting_streak_30', '30-Day Posting Streak'),
        ('engagement_streak_7', '7-Day Engagement Streak'),
        ('platform_anniversary', 'Platform Anniversary'),
        
        # Special Contributions
        ('quality_content', 'Quality Content'),
        ('helpful_comment', 'Helpful Comment'),
        ('mentor_activity', 'Mentoring Activity'),
        ('event_participation', 'Event Participation'),
        ('survey_complete', 'Survey Completed'),
        
        ('other', 'Other Activity'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_history')
    points = models.IntegerField()  # Can be negative for penalties
    reason = models.CharField(max_length=30, choices=POINT_REASONS)
    description = models.CharField(max_length=200)
    
    # Optional references
    achievement = models.ForeignKey('Achievement', on_delete=models.SET_NULL, null=True, blank=True)
    post_id = models.UUIDField(null=True, blank=True)  # Reference to post
    startup_id = models.UUIDField(null=True, blank=True)  # Reference to startup
    job_id = models.UUIDField(null=True, blank=True)  # Reference to job
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['reason', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.points:+d} points - {self.description}"

class UserFollow(models.Model):
    """User following system - users can follow other users"""
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    following = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Notification preferences for this follow relationship
    notify_on_posts = models.BooleanField(default=True)
    notify_on_stories = models.BooleanField(default=True)
    notify_on_achievements = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    @classmethod
    def get_mutual_follows(cls, user1, user2):
        """Check if users follow each other"""
        return cls.objects.filter(
            models.Q(follower=user1, following=user2) |
            models.Q(follower=user2, following=user1)
        ).count() == 2

class Story(models.Model):
    """Instagram-style stories for quick updates"""
    STORY_TYPES = [
        ('text', 'Text Story'),
        ('image', 'Image Story'),
        ('video', 'Video Story'),
        ('link', 'Link Story'),
        ('achievement', 'Achievement Story'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    story_type = models.CharField(max_length=20, choices=STORY_TYPES, default='text')
    
    # Content fields
    text_content = models.TextField(blank=True, max_length=500)
    image = models.ImageField(
        upload_to='stories/images/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    video = models.FileField(
        upload_to='stories/videos/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['mp4', 'webm', 'mov'])]
    )
    link_url = models.URLField(blank=True)
    link_title = models.CharField(max_length=200, blank=True)
    link_description = models.TextField(max_length=300, blank=True)
    
    # Related objects
    related_startup = models.ForeignKey(
        'startups.Startup', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stories'
    )
    related_job = models.ForeignKey(
        'jobs.Job', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stories'
    )
    
    # Story settings
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    background_color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    text_color = models.CharField(max_length=7, default='#FFFFFF')
    
    # Video editing metadata (JSON field to store editing settings)
    video_metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="JSON object containing video editing settings like trim, filters, overlays"
    )
    
    # Image editing metadata (JSON field to store image editing settings)
    image_metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="JSON object containing image editing settings like filters, transforms, overlays"
    )
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_active', 'expires_at']),
            models.Index(fields=['-created_at', 'is_active']),
        ]
    
    def __str__(self):
        return f"Story by {self.author.username} - {self.story_type}"
    
    def save(self, *args, **kwargs):
        # Set expiration to 24 hours from creation if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def time_remaining(self):
        """Get remaining time in seconds"""
        if self.is_expired:
            return 0
        return (self.expires_at - timezone.now()).total_seconds()
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

class StoryView(models.Model):
    """Track story views for analytics and prevent duplicate counting"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='story_views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_duration = models.PositiveIntegerField(default=0)  # seconds
    
    class Meta:
        unique_together = ['story', 'viewer']
        indexes = [
            models.Index(fields=['story', '-viewed_at']),
            models.Index(fields=['viewer', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.viewer.username} viewed {self.story.author.username}'s story"

class StartupCollaboration(models.Model):
    """Pinterest-style collaborations of startups - Extended for collaboration"""
    COLLABORATION_TYPES = [
        ('public', 'Public Collaboration'),
        ('private', 'Private Collaboration'),
        ('collaborative', 'Collaborative Collaboration'),
    ]
    
    # Project collaboration types
    PROJECT_TYPES = [
        ('collection', 'Startup Collection'),
        ('project', 'Collaboration Project'),
        ('startup', 'Startup Development'),
        ('research', 'Research Project'),
        ('hackathon', 'Hackathon Team'),
        ('networking', 'Networking Group'),
        ('mentorship', 'Mentorship Circle'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='startup_collaborations')
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    collaboration_type = models.CharField(max_length=20, choices=COLLABORATION_TYPES, default='public')
    
    # New collaboration fields
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES, default='collection')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Project details
    goals = models.TextField(max_length=1000, blank=True, help_text="Project goals and objectives")
    requirements = models.TextField(max_length=1000, blank=True, help_text="Skills and resources needed")
    timeline = models.JSONField(default=dict, blank=True, help_text="Project milestones and deadlines")
    
    # Project dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Team settings
    max_team_size = models.PositiveIntegerField(default=10, help_text="Maximum number of collaborators")
    skills_needed = models.JSONField(default=list, blank=True, help_text="List of required skills")
    
    # Communication preferences
    communication_methods = models.JSONField(
        default=list, 
        blank=True,
        help_text="Preferred communication methods (email, slack, discord, etc.)"
    )
    meeting_frequency = models.CharField(
        max_length=20, 
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'), 
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
            ('as_needed', 'As Needed'),
        ],
        default='weekly'
    )
    
    # Collaboration Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extended metadata for the collaboration including resources, tools, progress tracking, etc."
    )
    
    # Visual customization
    cover_image = models.ImageField(
        upload_to='collaborations/covers/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    theme_color = models.CharField(max_length=7, default='#3B82F6')
    
    # Settings
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    
    # Collaborators for collaborative collaborations
    collaborators = models.ManyToManyField(
        User, 
        through='CollaborationCollaborator',
        through_fields=('collaboration', 'user'),
        related_name='collaborated_collaborations',
        blank=True
    )
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['collaboration_type', '-updated_at']),
            models.Index(fields=['is_featured', '-updated_at']),
            models.Index(fields=['project_type', '-updated_at']),
            models.Index(fields=['status', '-updated_at']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.owner.username}"
    
    @property
    def startup_count(self):
        return self.items.filter(is_active=True).count()
    
    @property
    def task_count(self):
        """Get total number of tasks in this project"""
        return self.tasks.count() if hasattr(self, 'tasks') else 0
    
    @property
    def completed_task_count(self):
        """Get number of completed tasks"""
        return self.tasks.filter(status='completed').count() if hasattr(self, 'tasks') else 0
    
    @property
    def progress_percentage(self):
        """Calculate project progress based on completed tasks"""
        if self.task_count == 0:
            return 0
        return round((self.completed_task_count / self.task_count) * 100)
    
    @property
    def team_size(self):
        """Get current team size including owner and collaborators"""
        if self.collaboration_type == 'collaborative':
            return self.collaborators.count() + 1  # +1 for owner
        return 1
    
    @property
    def is_project(self):
        """Check if this is a collaboration project vs regular collection"""
        return self.project_type != 'collection'
    
    def can_edit(self, user):
        """Check if user can edit this collection/project"""
        if self.owner == user:
            return True
        if self.collaboration_type == 'collaborative':
            try:
                collaborator = self.collaborationcollaborator_set.get(user=user)
                return collaborator.permission_level in ['edit', 'admin']
            except:
                return False
        return False
    
    def can_view(self, user):
        """Check if user can view this collection/project"""
        if self.collaboration_type == 'public':
            return True
        if self.owner == user:
            return True
        if self.collaboration_type == 'collaborative':
            return self.collaborators.filter(id=user.id).exists()
        return False
    
    def get_permission_level(self, user):
        """Get user's permission level for this project"""
        if self.owner == user:
            return 'admin'
        if self.collaboration_type == 'collaborative':
            try:
                collaborator = self.collaborationcollaborator_set.get(user=user)
                return collaborator.permission_level
            except:
                return None
        return 'view' if self.collaboration_type == 'public' else None

class CollaborationCollaborator(models.Model):
    """Collaborators for collaborations"""
    PERMISSION_LEVELS = [
        ('view', 'Can View'),
        ('comment', 'Can Comment'),
        ('edit', 'Can Edit'),
        ('admin', 'Admin Access'),
    ]
    
    collaboration = models.ForeignKey(StartupCollaboration, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=10, choices=PERMISSION_LEVELS, default='edit')
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='added_collaborators'
    )
    
    class Meta:
        unique_together = ['collaboration', 'user']

class CollaborationItem(models.Model):
    """Items in a startup collaboration"""
    collaboration = models.ForeignKey(
        StartupCollaboration, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    startup = models.ForeignKey(
        'startups.Startup', 
        on_delete=models.CASCADE,
        related_name='collaboration_items'
    )
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Optional customization for this item in the collaboration
    custom_note = models.TextField(max_length=300, blank=True)
    custom_tags = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)  # For ordering
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['collaboration', 'startup']
        ordering = ['position', '-added_at']
        indexes = [
            models.Index(fields=['collaboration', 'position']),
            models.Index(fields=['startup', '-added_at']),
        ]
    
    def __str__(self):
        return f"{self.startup.name} in {self.collaboration.name}"

class CollaborationFollow(models.Model):
    """Users can follow collaborations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_collaborations')
    collaboration = models.ForeignKey(
        StartupCollaboration, 
        on_delete=models.CASCADE, 
        related_name='collaboration_followers'
    )
    followed_at = models.DateTimeField(auto_now_add=True)
    
    # Notification preferences
    notify_on_updates = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'collaboration']
        indexes = [
            models.Index(fields=['user', '-followed_at']),
            models.Index(fields=['collaboration', '-followed_at']),
        ]

# ============================================================================
# COLLABORATION MODELS - New project collaboration features
# ============================================================================

class ProjectTask(models.Model):
    """Tasks within collaboration projects"""
    TASK_STATUS = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(StartupCollaboration, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    
    # Timing
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(null=True, blank=True)
    actual_hours = models.PositiveIntegerField(null=True, blank=True)
    
    # Dependencies
    depends_on = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='blocking_tasks')
    
    # File attachments
    attachments = models.JSONField(default=list, blank=True, help_text="List of file attachments")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"
    
    def can_edit(self, user):
        """Check if user can edit this task"""
        return (
            user == self.created_by or 
            user == self.assigned_to or 
            self.project.can_edit(user)
        )

class TaskComment(models.Model):
    """Comments on project tasks"""
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    
    # File attachments for comments
    attachments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

class ProjectFile(models.Model):
    """File sharing within collaboration projects"""
    FILE_CATEGORIES = [
        ('document', 'Document'),
        ('presentation', 'Presentation'),
        ('spreadsheet', 'Spreadsheet'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('code', 'Code'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(StartupCollaboration, on_delete=models.CASCADE, related_name='project_files')
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=500, blank=True)
    category = models.CharField(max_length=20, choices=FILE_CATEGORIES, default='other')
    
    # File storage
    file = models.FileField(upload_to='collaboration/files/%Y/%m/%d/')
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    file_type = models.CharField(max_length=50, blank=True)
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    is_latest = models.BooleanField(default=True)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Access control
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    is_public = models.BooleanField(default=False)  # Public within project team
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['project', '-updated_at']),
            models.Index(fields=['category', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"

class ProjectMeeting(models.Model):
    """Scheduled meetings for collaboration projects"""
    MEETING_STATUS = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(StartupCollaboration, on_delete=models.CASCADE, related_name='meetings')
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    agenda = models.TextField(max_length=2000, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=MEETING_STATUS, default='scheduled')
    
    # Meeting details
    meeting_url = models.URLField(blank=True, help_text="Zoom, Meet, or other meeting link")
    location = models.CharField(max_length=200, blank=True, help_text="Physical location or virtual platform")
    
    # Attendees
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    attendees = models.ManyToManyField(User, related_name='project_meetings', blank=True)
    
    # Meeting notes and outcomes
    notes = models.TextField(max_length=5000, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    recording_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['project', 'scheduled_at']),
            models.Index(fields=['organizer', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"

class ProjectMilestone(models.Model):
    """Project milestones and deadlines"""
    MILESTONE_STATUS = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(StartupCollaboration, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=MILESTONE_STATUS, default='planned')
    
    # Timing
    target_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(default=0, help_text="0-100%")
    
    # Dependencies
    depends_on = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='blocking_milestones')
    related_tasks = models.ManyToManyField(ProjectTask, blank=True, related_name='milestones')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_milestones')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['target_date']
        indexes = [
            models.Index(fields=['project', 'target_date']),
            models.Index(fields=['status', 'target_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"

class CollaborationInvite(models.Model):
    """Invitations to join collaboration projects"""
    INVITE_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(StartupCollaboration, on_delete=models.CASCADE, related_name='invites')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')
    
    # Invitation details
    message = models.TextField(max_length=500, blank=True)
    role_description = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=INVITE_STATUS, default='pending')
    
    # Permissions for the invitee
    permission_level = models.CharField(
        max_length=10,
        choices=[
            ('view', 'Can View'),
            ('comment', 'Can Comment'),
            ('edit', 'Can Edit'),
            ('admin', 'Admin Access'),
        ],
        default='edit'
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['project', 'invitee']
        indexes = [
            models.Index(fields=['invitee', 'status']),
            models.Index(fields=['project', 'status']),
        ]
    
    def __str__(self):
        return f"Invite to {self.project.name} for {self.invitee.username}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'pending'

class Achievement(models.Model):
    """Achievement definitions"""
    ACHIEVEMENT_CATEGORIES = [
        ('profile', 'Profile Completion'),
        ('social', 'Social Engagement'),
        ('content', 'Content Creation'),
        ('networking', 'Networking'),
        ('startup', 'Startup Activities'),
        ('jobs', 'Job Activities'),
        ('special', 'Special Events'),
    ]
    
    RARITY_LEVELS = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=300)
    category = models.CharField(max_length=20, choices=ACHIEVEMENT_CATEGORIES)
    rarity = models.CharField(max_length=20, choices=RARITY_LEVELS, default='common')
    
    # Visual elements
    icon = models.CharField(max_length=50, default='🏆')  # Emoji or icon class
    color = models.CharField(max_length=7, default='#FFD700')  # Hex color
    image = models.ImageField(
        upload_to='achievements/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'svg'])]
    )
    
    # Requirements (stored as JSON for flexibility)
    requirements = models.JSONField(
        default=dict,
        help_text="JSON object defining achievement requirements"
    )
    
    # Rewards
    points = models.PositiveIntegerField(default=10)
    badge_text = models.CharField(max_length=50, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_secret = models.BooleanField(default=False)  # Hidden until earned
    is_repeatable = models.BooleanField(default=False)
    
    # Statistics
    earned_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'rarity', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['rarity', '-earned_count']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"
    
    def get_rarity_color(self):
        """Get color based on rarity"""
        colors = {
            'common': '#6B7280',
            'uncommon': '#10B981', 
            'rare': '#3B82F6',
            'epic': '#8B5CF6',
            'legendary': '#F59E0B',
        }
        return colors.get(self.rarity, '#6B7280')

class UserAchievement(models.Model):
    """User's earned achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    
    # Tracking
    earned_at = models.DateTimeField(auto_now_add=True)
    progress_data = models.JSONField(default=dict, blank=True)  # Progress when earned
    
    # Display settings
    is_pinned = models.BooleanField(default=False)  # Pin to profile
    is_public = models.BooleanField(default=True)   # Show on public profile
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', '-earned_at']),
            models.Index(fields=['achievement', '-earned_at']),
            models.Index(fields=['user', 'is_pinned', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"

class UserAchievementProgress(models.Model):
    """Track progress towards achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievement_progress')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    
    # Progress tracking
    current_progress = models.JSONField(default=dict)
    progress_percentage = models.FloatField(default=0.0)
    
    # Status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['achievement', '-progress_percentage']),
        ]

# Add to existing Post model for scheduling
class ScheduledPost(models.Model):
    """Scheduled posts that will be published later"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_posts')
    
    # Post content (same as regular Post model)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=[
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('resource', 'Resource'),
        ('event', 'Event'),
    ], default='discussion')
    
    # Scheduling
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Content attachments (stored as JSON until published)
    images_data = models.JSONField(default=list, blank=True)
    links_data = models.JSONField(default=list, blank=True)
    topics_data = models.JSONField(default=list, blank=True)
    
    # Related objects
    related_startup = models.ForeignKey(
        'startups.Startup', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    related_job = models.ForeignKey(
        'jobs.Job', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Privacy settings
    is_anonymous = models.BooleanField(default=False)
    
    # Result tracking
    published_post = models.ForeignKey(
        'posts.Post', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='scheduled_from'
    )
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['author', 'status', 'scheduled_for']),
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Scheduled post by {self.author.username} for {self.scheduled_for}"
    
    @property
    def is_ready_to_publish(self):
        return (
            self.status == 'scheduled' and 
            timezone.now() >= self.scheduled_for
        )
    
    def can_edit(self, user):
        """Check if user can edit this scheduled post"""
        return self.author == user and self.status == 'scheduled'
    
    def can_cancel(self, user):
        """Check if user can cancel this scheduled post"""
        return self.author == user and self.status == 'scheduled'

class UserLoginStreak(models.Model):
    """Track user login streaks for daily login points and achievements"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='login_streak')
    
    # Streak tracking
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)
    
    # Statistics
    total_login_days = models.PositiveIntegerField(default=0)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-current_streak']),
            models.Index(fields=['-longest_streak']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.current_streak} day streak"
    
    @classmethod
    def update_login_streak(cls, user):
        """Update user's login streak and award points if applicable"""
        from .points_service import PointsService
        
        streak, created = cls.objects.get_or_create(user=user)
        today = date.today()
        
        # If this is the first time or user hasn't logged in today
        if streak.last_login_date != today:
            yesterday = today - timedelta(days=1)
            
            if streak.last_login_date == yesterday:
                # Consecutive day - increment streak
                streak.current_streak += 1
            elif streak.last_login_date is None or streak.last_login_date < yesterday:
                # First login or streak broken - reset to 1
                streak.current_streak = 1
            # If last_login_date == today, do nothing (already counted today)
            
            # Update tracking
            streak.last_login_date = today
            streak.total_login_days += 1
            
            # Update longest streak if needed
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            
            streak.save()
            
            # Award daily login points
            try:
                PointsService.award_points(
                    user,
                    'daily_login',
                    description=f"Daily login - {streak.current_streak} day streak!"
                )
                
                # Award bonus points for streak milestones
                if streak.current_streak == 7:
                    PointsService.award_points(
                        user,
                        'login_streak_7',
                        description="Logged in for 7 consecutive days!"
                    )
                elif streak.current_streak == 30:
                    PointsService.award_points(
                        user,
                        'login_streak_30',
                        description="Logged in for 30 consecutive days!"
                    )
            except Exception as e:
                pass  # Don't fail login if points service has issues
        
        return streak