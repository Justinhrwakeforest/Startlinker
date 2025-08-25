# startup_hub/apps/posts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F, Q
import uuid
from django.core.validators import FileExtensionValidator

User = get_user_model()

class Topic(models.Model):
    """Topics/hashtags for posts"""
    name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True)  # Emoji icon
    created_at = models.DateTimeField(auto_now_add=True)
    post_count = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-post_count', 'name']
        indexes = [
            models.Index(fields=['-post_count', 'name']),
        ]
    
    def __str__(self):
        return f"#{self.name}"

class Post(models.Model):
    """Main post model for discussions"""
    POST_TYPES = [
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('resource', 'Resource'),
        ('event', 'Event'),
        ('poll', 'Poll'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()  # Rich text content
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    
    # Topics/hashtags
    topics = models.ManyToManyField(Topic, related_name='posts', blank=True)
    
    # Privacy
    is_anonymous = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)  # No new comments allowed
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    edit_count = models.PositiveIntegerField(default=0)
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)
    
    # SEO/Social
    slug = models.SlugField(max_length=250, blank=True)
    meta_description = models.TextField(blank=True, max_length=160)
    
    # Related startup/job (optional)
    related_startup = models.ForeignKey('startups.Startup', on_delete=models.SET_NULL, null=True, blank=True)
    related_job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'is_approved']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-like_count', '-created_at']),
            models.Index(fields=['-comment_count', '-created_at']),
            models.Index(fields=['is_pinned', '-created_at']),
        ]
    
    def __str__(self):
        return self.title or f"Post by {self.get_author_name()}"
    
    def get_author_name(self):
        if self.is_anonymous:
            return "Anonymous"
        return self.author.get_full_name() or self.author.username
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        # Can edit within 30 minutes of creation
        if self.author == user and (timezone.now() - self.created_at).total_seconds() < 1800:
            return True
        return user.is_staff
    
    def can_delete(self, user):
        if not user.is_authenticated:
            return False
        # Authors can delete their own posts, staff can delete any
        return self.author == user or user.is_staff
    
    def save(self, *args, **kwargs):
        # Track edits
        if self.pk:
            old = Post.objects.filter(pk=self.pk).first()
            if old and old.content != self.content:
                self.edited_at = timezone.now()
                self.edit_count = F('edit_count') + 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('posts:post-detail', kwargs={'pk': self.pk})

class PostImage(models.Model):
    """Images attached to posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='posts/images/%Y/%m/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'uploaded_at']

class PostLink(models.Model):
    """External links in posts with preview data"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='links')
    url = models.URLField()
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    domain = models.CharField(max_length=100, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['fetched_at']

class PostReaction(models.Model):
    """Likes on posts - simplified to only support thumbs up"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

class Comment(models.Model):
    """Comments on posts with threading support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    is_solution = models.BooleanField(default=False)  # For Q&A posts
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.get_author_name()} on {self.post}"
    
    def get_author_name(self):
        if self.is_anonymous:
            return "Anonymous"
        return self.author.get_full_name() or self.author.username
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        # Authors can edit their own comments, staff can edit any
        return self.author == user or user.is_staff
    
    def can_delete(self, user):
        if not user.is_authenticated:
            return False
        # Authors can delete their own comments, staff can delete any
        return self.author == user or user.is_staff

class CommentReaction(models.Model):
    """Reactions on comments"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comment', 'user']

class PostBookmark(models.Model):
    """Saved/bookmarked posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarked_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)  # Personal note about why saved
    
    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

class PostView(models.Model):
    """Track unique post views"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(default=0)  # Seconds spent
    
    class Meta:
        indexes = [
            models.Index(fields=['post', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
        ]

class PostShare(models.Model):
    """Track post shares"""
    PLATFORMS = [
        ('copy_link', 'Copy Link'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['post', '-shared_at']),
        ]

class Mention(models.Model):
    """Track @mentions in posts and comments"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions')
    mentioned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions_made')
    created_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['mentioned_user', '-created_at']),
        ]

class PostReport(models.Model):
    """Reports/flags on posts"""
    REPORT_REASONS = [
        ('spam', 'Spam or misleading'),
        ('inappropriate', 'Inappropriate content'),
        ('harassment', 'Harassment or hate speech'),
        ('misinformation', 'False information'),
        ('other', 'Other'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['post', 'reported_by']


class UserInteraction(models.Model):
    """Track user interactions for ranking algorithm"""
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('bookmark', 'Bookmark'),
        ('click_profile', 'Click Profile'),
        ('click_link', 'Click Link'),
        ('time_spent', 'Time Spent Reading'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    
    # Additional data for different interaction types
    value = models.FloatField(default=1.0)  # Weight/value of interaction (e.g., time spent in seconds)
    metadata = models.JSONField(default=dict, blank=True)  # Additional context
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['post', 'interaction_type', '-created_at']),
            models.Index(fields=['user', 'interaction_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} on {self.post}"


class SeenPost(models.Model):
    """Track posts that users have seen/viewed"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seen_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='seen_by')
    seen_at = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    view_duration = models.FloatField(null=True, blank=True)  # Time spent viewing in seconds
    viewed_from = models.CharField(max_length=50, blank=True)  # Source: 'feed', 'direct', 'search', etc.
    
    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', '-seen_at']),
            models.Index(fields=['post', '-seen_at']),
            models.Index(fields=['user', 'post']),
        ]
    
    def __str__(self):
        return f"{self.user.username} seen {self.post} at {self.seen_at}"


class PostRankingScore(models.Model):
    """Pre-calculated ranking scores for posts"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='ranking_score')
    
    # Individual score components
    engagement_score = models.FloatField(default=0.0)
    recency_score = models.FloatField(default=0.0)
    quality_score = models.FloatField(default=0.0)
    author_reputation_score = models.FloatField(default=0.0)
    trending_score = models.FloatField(default=0.0)
    
    # Final composite score
    total_score = models.FloatField(default=0.0, db_index=True)
    
    # User-specific scores (for followed users)
    personalization_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-total_score', '-calculated_at']),
            models.Index(fields=['-engagement_score']),
            models.Index(fields=['-trending_score']),
        ]
    
    def __str__(self):
        return f"Ranking score for {self.post} - {self.total_score:.2f}"


class Poll(models.Model):
    """Poll associated with a post"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll')
    
    # Poll configuration
    multiple_choice = models.BooleanField(default=False)
    max_selections = models.PositiveSmallIntegerField(default=1)  # For multiple choice
    anonymous_voting = models.BooleanField(default=False)
    show_results_before_vote = models.BooleanField(default=False)
    allow_result_view_without_vote = models.BooleanField(default=True)
    
    # Timing
    ends_at = models.DateTimeField(null=True, blank=True)  # Optional end time
    
    # Metrics
    total_votes = models.PositiveIntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['ends_at']),
        ]
    
    def __str__(self):
        return f"Poll for {self.post}"
    
    def is_active(self):
        if not self.ends_at:
            return True
        return timezone.now() < self.ends_at
    
    def user_has_voted(self, user):
        if not user.is_authenticated:
            return False
        return self.votes.filter(user=user).exists()
    
    def get_user_votes(self, user):
        if not user.is_authenticated:
            return []
        return self.votes.filter(user=user).values_list('option_id', flat=True)


class PollOption(models.Model):
    """Options for a poll"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)
    
    # Metrics
    vote_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['poll', 'order']),
        ]
    
    def __str__(self):
        return self.text
    
    def get_percentage(self):
        if self.poll.total_votes == 0:
            return 0
        return (self.vote_count / self.poll.total_votes) * 100


class PollVote(models.Model):
    """User votes on polls"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    voted_at = models.DateTimeField(auto_now_add=True)
    
    # For anonymous polls, we still track user to prevent double voting
    # but don't expose this information
    
    class Meta:
        indexes = [
            models.Index(fields=['poll', 'user']),
            models.Index(fields=['option', '-voted_at']),
            models.Index(fields=['user', '-voted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} voted for {self.option.text}"