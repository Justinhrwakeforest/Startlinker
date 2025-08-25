from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re
from .profanity_filter import is_valid_name

# Reserved usernames that cannot be used
RESERVED_USERNAMES = {
    'admin', 'administrator', 'support', 'help', 'info', 'contact', 'api', 'www', 'mail',
    'email', 'ftp', 'blog', 'news', 'forum', 'test', 'demo', 'guest', 'user', 'users',
    'account', 'accounts', 'profile', 'profiles', 'settings', 'config', 'configuration',
    'root', 'system', 'startlinker', 'startuphub', 'startup', 'startups', 'founder',
    'founders', 'investor', 'investors', 'moderator', 'mod', 'staff', 'team',
    'null', 'undefined', 'none', 'void', 'bot', 'robot', 'service', 'no-reply',
    'noreply', 'security', 'abuse', 'legal', 'privacy', 'terms', 'billing',
    'sales', 'marketing', 'hr', 'careers', 'jobs', 'job', 'post', 'posts',
    'comment', 'comments', 'reply', 'replies', 'feed', 'home', 'dashboard',
    'login', 'logout', 'signin', 'signup', 'register', 'auth', 'oauth',
    'facebook', 'twitter', 'google', 'linkedin', 'github', 'instagram'
}

def validate_username(username):
    """
    Validate username according to our rules:
    - 3-20 characters
    - Letters, numbers, underscores, dots
    - No starting/ending with special characters
    - No double underscores or double dots
    - Not in reserved list
    - No offensive/vulgar content
    """
    if not username:
        raise ValidationError("Username is required.")
    
    # Length check
    if len(username) < 3 or len(username) > 20:
        raise ValidationError("Username must be between 3 and 20 characters.")
    
    # Character validation
    if not re.match(r'^[a-zA-Z0-9_.]+$', username):
        raise ValidationError("Username can only contain letters, numbers, underscores, and dots.")
    
    # Cannot start or end with special characters
    if username.startswith(('_', '.')) or username.endswith(('_', '.')):
        raise ValidationError("Username cannot start or end with underscores or dots.")
    
    # No double underscores or dots
    if '__' in username or '..' in username:
        raise ValidationError("Username cannot contain consecutive underscores or dots.")
    
    # Reserved usernames check (case-insensitive)
    if username.lower() in RESERVED_USERNAMES:
        raise ValidationError(f"'{username}' is a reserved username and cannot be used.")
    
    # Profanity check
    is_valid, error_message = is_valid_name(username)
    if not is_valid:
        raise ValidationError("This username contains inappropriate content and cannot be used. Please choose a different username.")

def validate_first_name(first_name):
    """
    Validate first name for inappropriate content.
    """
    if not first_name:
        return  # First name is optional
    
    # Length check
    if len(first_name) > 30:
        raise ValidationError("First name must be 30 characters or less.")
    
    # Basic character validation (allow letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-']+$", first_name):
        raise ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
    
    # Profanity check
    is_valid, error_message = is_valid_name(first_name)
    if not is_valid:
        raise ValidationError("This first name contains inappropriate content and cannot be used. Please use your real first name.")

def validate_last_name(last_name):
    """
    Validate last name for inappropriate content.
    """
    if not last_name:
        return  # Last name is optional
    
    # Length check
    if len(last_name) > 30:
        raise ValidationError("Last name must be 30 characters or less.")
    
    # Basic character validation (allow letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-']+$", last_name):
        raise ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
    
    # Profanity check
    is_valid, error_message = is_valid_name(last_name)
    if not is_valid:
        raise ValidationError("This last name contains inappropriate content and cannot be used. Please use your real last name.")

def user_profile_picture_upload_path(instance, filename):
    """Generate upload path for user profile pictures"""
    import os
    ext = filename.split('.')[-1]
    filename = f"profile_{instance.id}.{ext}"
    return os.path.join('profile_pictures', filename)

class User(AbstractUser):
    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_username],
        help_text="Required. 3-20 characters. Letters, numbers, underscores and dots only."
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(
        max_length=30,
        blank=True,
        validators=[validate_first_name],
        help_text="Your first name. Only letters, spaces, hyphens, and apostrophes allowed."
    )
    last_name = models.CharField(
        max_length=30,
        blank=True,
        validators=[validate_last_name],
        help_text="Your last name. Only letters, spaces, hyphens, and apostrophes allowed."
    )
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_upload_path,
        blank=True,
        null=True,
        help_text="Profile picture"
    )
    is_premium = models.BooleanField(default=False)
    
    # Social fields
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    
    # Subscription fields
    SUBSCRIPTION_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    subscription_status = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_CHOICES, 
        default='free'
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def get_avatar_url(self):
        """Get user avatar URL - profile picture or generated avatar"""
        if self.profile_picture:
            # Return full URL for profile picture
            from django.conf import settings
            import time
            if self.profile_picture.url.startswith('http'):
                return self.profile_picture.url
            else:
                # Build full URL with backend domain and cache-busting
                backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
                timestamp = int(time.time())
                return f"{backend_url}{self.profile_picture.url}?v={timestamp}"
        else:
            # Generate avatar using UI Avatars service
            display_name = self.get_display_name()
            return f"https://ui-avatars.com/api/?name={display_name}&background=3b82f6&color=fff&size=128"
    
    def get_display_name(self):
        """Get the best display name for the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        return "User"
    
    def is_pro(self):
        """Check if user has active pro subscription"""
        return self.subscription_status == 'pro'
    
    def is_enterprise(self):
        """Check if user has active enterprise subscription"""
        return self.subscription_status == 'enterprise'
    
    @staticmethod
    def generate_username_suggestions(base_username, max_suggestions=5):
        """
        Generate username suggestions when the desired username is taken
        """
        suggestions = []
        
        # Clean the base username
        base = re.sub(r'[^a-zA-Z0-9_.]', '', base_username.lower())
        if len(base) < 3:
            base = base + 'user'
        elif len(base) > 17:  # Leave room for numbers
            base = base[:17]
        
        # Try variations
        variations = [
            base,
            f"{base}_",
            f"{base}.",
            f"_{base}",
            f".{base}",
        ]
        
        # Add numbered variations
        for i in range(1, 100):
            variations.extend([
                f"{base}{i}",
                f"{base}_{i}",
                f"{base}.{i}",
            ])
        
        for variant in variations:
            if len(suggestions) >= max_suggestions:
                break
                
            # Skip if too long
            if len(variant) > 20:
                continue
                
            # Skip if invalid format
            try:
                validate_username(variant)
            except ValidationError:
                continue
                
            # Skip if already exists
            if User.objects.filter(username=variant).exists():
                continue
                
            suggestions.append(variant)
        
        return suggestions

class UserSettings(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends', 'Friends Only'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Notification settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=True)
    job_alerts = models.BooleanField(default=True)
    startup_updates = models.BooleanField(default=True)
    
    # Privacy settings
    profile_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    show_activity = models.BooleanField(default=True)
    show_bookmarks = models.BooleanField(default=False)
    show_ratings = models.BooleanField(default=True)
    allow_messages = models.BooleanField(default=True)
    
    # Preferences
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    items_per_page = models.IntegerField(default=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'
    
    def __str__(self):
        return f"Settings for {self.user.email}"

class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests')
    interest = models.CharField(max_length=50)
    
    class Meta:
        unique_together = ['user', 'interest']
        
    def __str__(self):
        return self.interest


def user_resume_upload_path(instance, filename):
    """Generate upload path for user resumes"""
    import os
    from datetime import datetime
    ext = filename.split('.')[-1]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"resume_{instance.user.id}_{timestamp}.{ext}"
    return os.path.join('resumes', str(instance.user.id), filename)


class Resume(models.Model):
    """Model to store multiple resumes per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(
        max_length=100, 
        help_text="Give your resume a descriptive title (e.g., 'Software Engineer Resume', 'Marketing Resume')"
    )
    file = models.FileField(
        upload_to=user_resume_upload_path,
        help_text="Upload your resume (PDF, DOC, DOCX)"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Set as default resume for job applications"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_size = models.IntegerField(blank=True, null=True)  # in bytes
    file_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['user', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Check if user has reached the maximum number of resumes (5)
        if not self.pk:  # Only check for new resumes
            existing_count = Resume.objects.filter(user=self.user).count()
            if existing_count >= 5:
                raise ValidationError("You can only upload up to 5 resumes. Please delete an existing resume before uploading a new one.")
        
        # Extract file info before saving
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].upper()
        
        # Ensure only one default resume per user
        if self.is_default:
            Resume.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        # If this is the first resume for the user, make it default
        if not self.pk and not Resume.objects.filter(user=self.user).exists():
            self.is_default = True
            
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        if not self.file_size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
