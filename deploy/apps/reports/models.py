from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinLengthValidator
from datetime import timedelta

User = get_user_model()

class UserReport(models.Model):
    """
    Model to track user reports for inappropriate behavior, content, or violations.
    """
    
    REPORT_TYPE_CHOICES = [
        ('harassment', 'Harassment or Bullying'),
        ('spam', 'Spam or Unwanted Content'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('fake_profile', 'Fake Profile'),
        ('impersonation', 'Impersonation'),
        ('intellectual_property', 'Intellectual Property Violation'),
        ('privacy_violation', 'Privacy Violation'),
        ('scam', 'Scam or Fraud'),
        ('hate_speech', 'Hate Speech'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Core report information
    reporter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='submitted_reports',
        help_text="User who submitted the report"
    )
    reported_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_reports',
        help_text="User being reported"
    )
    
    # Report details
    report_type = models.CharField(
        max_length=50, 
        choices=REPORT_TYPE_CHOICES,
        help_text="Category of the report"
    )
    reason = models.TextField(
        validators=[MinLengthValidator(10)],
        help_text="Detailed explanation of the issue (minimum 10 characters)"
    )
    evidence_urls = models.JSONField(
        default=list, 
        blank=True,
        help_text="URLs to screenshots or other evidence"
    )
    
    # Status and priority
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Current status of the report"
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        help_text="Priority level assigned by admin"
    )
    
    # Admin management
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin use only"
    )
    assigned_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_reports',
        help_text="Admin user assigned to handle this report"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the report was submitted"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time the report was modified"
    )
    resolved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the report was resolved"
    )
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['reported_user', 'created_at']),
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['assigned_admin', 'status']),
        ]
        
    def __str__(self):
        return f"Report #{self.id}: {self.get_report_type_display()} - {self.reported_user.username}"
    
    def save(self, *args, **kwargs):
        # Auto-set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved' and self.resolved_at:
            self.resolved_at = None
            
        super().save(*args, **kwargs)
    
    @property
    def is_resolved(self):
        """Check if the report is resolved or dismissed"""
        return self.status in ['resolved', 'dismissed']
    
    @property
    def response_time(self):
        """Calculate response time if resolved"""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    @property
    def age_in_days(self):
        """Calculate how many days old the report is"""
        return (timezone.now() - self.created_at).days


class UserWarning(models.Model):
    """Model to track user warnings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warnings')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_warnings')
    report = models.ForeignKey('UserReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='warnings')
    post_report = models.ForeignKey('PostReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='warnings')
    
    message = models.TextField(help_text="Warning message sent to the user")
    reason = models.TextField(help_text="Admin reason for the warning")
    
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['admin', '-created_at']),
        ]
    
    def __str__(self):
        return f"Warning for {self.user.username} by {self.admin.username}"


class UserBan(models.Model):
    """Model to track user bans"""
    BAN_TYPES = [
        ('temporary', 'Temporary Ban'),
        ('permanent', 'Permanent Ban'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_bans')
    report = models.ForeignKey('UserReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='bans')
    post_report = models.ForeignKey('PostReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='bans')
    
    ban_type = models.CharField(max_length=20, choices=BAN_TYPES)
    reason = models.TextField(help_text="Admin reason for the ban")
    
    # For temporary bans
    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in days for temporary bans")
    expires_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    lifted_at = models.DateTimeField(null=True, blank=True)
    lifted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifted_bans')
    lift_reason = models.TextField(blank=True, help_text="Reason for lifting the ban early")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        ban_status = "Active" if self.is_active else "Lifted"
        return f"{self.get_ban_type_display()} for {self.user.username} ({ban_status})"
    
    def save(self, *args, **kwargs):
        # Set expiration date for temporary bans
        if self.ban_type == 'temporary' and self.duration_days and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.duration_days)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if temporary ban has expired"""
        if self.ban_type == 'permanent':
            return False
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def lift_ban(self, admin, reason=""):
        """Lift the ban"""
        self.is_active = False
        self.lifted_at = timezone.now()
        self.lifted_by = admin
        self.lift_reason = reason
        self.save()
    
    def get_priority_color(self):
        """Get color for priority display"""
        colors = {
            'low': 'green',
            'medium': 'yellow', 
            'high': 'orange',
            'critical': 'red'
        }
        return colors.get(self.priority, 'gray')
    
    def get_status_color(self):
        """Get color for status display"""
        colors = {
            'pending': 'yellow',
            'investigating': 'blue',
            'resolved': 'green',
            'dismissed': 'gray',
            'escalated': 'red'
        }
        return colors.get(self.status, 'gray')


class ReportAction(models.Model):
    """
    Model to track all actions taken on a report for audit trail.
    """
    
    ACTION_TYPE_CHOICES = [
        ('status_change', 'Status Changed'),
        ('priority_change', 'Priority Changed'),
        ('assignment_change', 'Assignment Changed'),
        ('note_added', 'Note Added'),
        ('user_warned', 'User Warned'),
        ('user_suspended', 'User Suspended'),
        ('user_banned', 'User Banned'),
        ('content_removed', 'Content Removed'),
        ('profile_restricted', 'Profile Restricted'),
        ('report_escalated', 'Report Escalated'),
        ('evidence_added', 'Evidence Added'),
        ('other', 'Other Action'),
    ]
    
    # Relationships
    report = models.ForeignKey(
        UserReport, 
        on_delete=models.CASCADE, 
        related_name='actions',
        help_text="The report this action is related to"
    )
    admin = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='report_actions',
        help_text="Admin who performed this action"
    )
    
    # Action details
    action_type = models.CharField(
        max_length=30, 
        choices=ACTION_TYPE_CHOICES,
        help_text="Type of action performed"
    )
    description = models.TextField(
        help_text="Detailed description of the action taken"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional data related to the action (old/new values, etc.)"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this action was performed"
    )
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report', 'created_at']),
            models.Index(fields=['admin', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"Action on Report #{self.report.id}: {self.get_action_type_display()} by {self.admin.username}"


class ReportStatistics(models.Model):
    """
    Model to store aggregated statistics for reporting dashboard.
    Updated periodically via management command or signals.
    """
    
    # Date for the statistics
    date = models.DateField(
        help_text="Date these statistics are for"
    )
    
    # Count statistics
    total_reports = models.IntegerField(
        default=0,
        help_text="Total reports created on this date"
    )
    pending_reports = models.IntegerField(
        default=0,
        help_text="Reports in pending status"
    )
    resolved_reports = models.IntegerField(
        default=0,
        help_text="Reports resolved on this date"
    )
    
    # Response time statistics
    avg_response_time_hours = models.FloatField(
        null=True, 
        blank=True,
        help_text="Average response time in hours"
    )
    
    # Report type breakdown (stored as JSON)
    report_type_breakdown = models.JSONField(
        default=dict,
        help_text="Count of reports by type"
    )
    
    # Priority breakdown
    priority_breakdown = models.JSONField(
        default=dict,
        help_text="Count of reports by priority"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'reports'
        ordering = ['-date']
        unique_together = ['date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Report Statistics for {self.date}"


class PostReport(models.Model):
    """
    Model to track reports for inappropriate posts or content.
    """
    
    REPORT_TYPE_CHOICES = [
        ('spam', 'Spam or Unwanted Content'),
        ('harassment', 'Harassment or Bullying'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('misinformation', 'Misinformation or False Information'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence or Harmful Content'),
        ('nudity', 'Nudity or Sexual Content'),
        ('intellectual_property', 'Intellectual Property Violation'),
        ('privacy_violation', 'Privacy Violation'),
        ('scam', 'Scam or Fraud'),
        ('off_topic', 'Off-topic or Irrelevant'),
        ('duplicate', 'Duplicate Content'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Core report information
    reporter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='submitted_post_reports',
        help_text="User who submitted the report"
    )
    post = models.ForeignKey(
        'posts.Post', 
        on_delete=models.CASCADE, 
        related_name='content_reports',
        help_text="Post being reported"
    )
    
    # Report details
    report_type = models.CharField(
        max_length=50, 
        choices=REPORT_TYPE_CHOICES,
        help_text="Category of the report"
    )
    reason = models.TextField(
        help_text="Detailed explanation of the issue"
    )
    additional_context = models.TextField(
        blank=True,
        help_text="Additional context or information"
    )
    
    # Status and priority
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Current status of the report"
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        help_text="Priority level assigned by admin"
    )
    
    # Admin management
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin use only"
    )
    assigned_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_post_reports',
        help_text="Admin user assigned to handle this report"
    )
    
    # Resolution actions
    action_taken = models.CharField(
        max_length=100,
        blank=True,
        help_text="Action taken by admin (e.g., post removed, user warned)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the report was submitted"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time the report was modified"
    )
    resolved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the report was resolved"
    )
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        unique_together = ['reporter', 'post']  # Prevent duplicate reports from same user
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['assigned_admin', 'status']),
        ]
        
    def __str__(self):
        return f"Post Report #{self.id}: {self.get_report_type_display()} - Post by {self.post.author.username}"
    
    def save(self, *args, **kwargs):
        # Auto-set resolved_at when status changes to resolved
        if self.status in ['resolved', 'dismissed'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status not in ['resolved', 'dismissed'] and self.resolved_at:
            self.resolved_at = None
            
        super().save(*args, **kwargs)
    
    @property
    def is_resolved(self):
        """Check if the report is resolved or dismissed"""
        return self.status in ['resolved', 'dismissed']
    
    @property
    def response_time(self):
        """Calculate response time if resolved"""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    @property
    def age_in_days(self):
        """Calculate how many days old the report is"""
        return (timezone.now() - self.created_at).days


class UserWarning(models.Model):
    """Model to track user warnings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warnings')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_warnings')
    report = models.ForeignKey('UserReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='warnings')
    post_report = models.ForeignKey('PostReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='warnings')
    
    message = models.TextField(help_text="Warning message sent to the user")
    reason = models.TextField(help_text="Admin reason for the warning")
    
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['admin', '-created_at']),
        ]
    
    def __str__(self):
        return f"Warning for {self.user.username} by {self.admin.username}"


class UserBan(models.Model):
    """Model to track user bans"""
    BAN_TYPES = [
        ('temporary', 'Temporary Ban'),
        ('permanent', 'Permanent Ban'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_bans')
    report = models.ForeignKey('UserReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='bans')
    post_report = models.ForeignKey('PostReport', on_delete=models.SET_NULL, null=True, blank=True, related_name='bans')
    
    ban_type = models.CharField(max_length=20, choices=BAN_TYPES)
    reason = models.TextField(help_text="Admin reason for the ban")
    
    # For temporary bans
    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in days for temporary bans")
    expires_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    lifted_at = models.DateTimeField(null=True, blank=True)
    lifted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifted_bans')
    lift_reason = models.TextField(blank=True, help_text="Reason for lifting the ban early")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        ban_status = "Active" if self.is_active else "Lifted"
        return f"{self.get_ban_type_display()} for {self.user.username} ({ban_status})"
    
    def save(self, *args, **kwargs):
        # Set expiration date for temporary bans
        if self.ban_type == 'temporary' and self.duration_days and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.duration_days)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if temporary ban has expired"""
        if self.ban_type == 'permanent':
            return False
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def lift_ban(self, admin, reason=""):
        """Lift the ban"""
        self.is_active = False
        self.lifted_at = timezone.now()
        self.lifted_by = admin
        self.lift_reason = reason
        self.save()