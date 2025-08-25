# startup_hub/apps/startups/serializers.py - Complete file with startup claiming support

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import (
    Industry, Startup, StartupFounder, StartupTag, StartupRating, 
    StartupComment, StartupBookmark, StartupLike, UserProfile, 
    StartupEditRequest, StartupClaimRequest
)

User = get_user_model()

class IndustrySerializer(serializers.ModelSerializer):
    startup_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Industry
        fields = ['id', 'name', 'description', 'icon', 'startup_count']
    
    def get_startup_count(self, obj):
        # Use annotated value if available, otherwise count
        return getattr(obj, 'startup_count', obj.startups.count())

class UserProfileSerializer(serializers.ModelSerializer):
    is_premium_active = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = ['is_premium', 'premium_expires_at', 'is_premium_active']

class StartupFounderSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupFounder
        fields = ['id', 'name', 'title', 'bio']

class StartupTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupTag
        fields = ['id', 'tag']

class StartupRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = StartupRating
        fields = ['id', 'user', 'user_name', 'rating', 'created_at']
        read_only_fields = ['user', 'created_at']

class StartupCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_display_name = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StartupComment
        fields = ['id', 'user', 'user_name', 'user_first_name', 'user_last_name', 'user_display_name', 'text', 'likes', 'created_at', 'time_ago']
        read_only_fields = ['user', 'likes', 'created_at']
    
    def get_user_display_name(self, obj):
        """Get the best display name for the user"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        elif obj.user.first_name:
            return obj.user.first_name
        elif obj.user.username:
            return obj.user.username
        return "Anonymous User"
    
    def get_time_ago(self, obj):
        """Get human-readable time since comment was created"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return obj.created_at.strftime("%b %d, %Y")

# Claim Request Serializers
class StartupClaimRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating claim requests"""
    startup_name = serializers.CharField(source='startup.name', read_only=True)
    startup_domain = serializers.SerializerMethodField(read_only=True)
    email_domain_valid = serializers.SerializerMethodField(read_only=True)
    time_ago = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = StartupClaimRequest
        fields = [
            'id', 'startup', 'startup_name', 'startup_domain', 'email', 'position', 
            'reason', 'email_verified', 'email_verified_at', 'status', 'created_at', 
            'expires_at', 'email_domain_valid', 'time_ago'
        ]
        read_only_fields = [
            'id', 'email_verified', 'email_verified_at', 'status', 'created_at', 
            'expires_at'
        ]
    
    def get_startup_domain(self, obj):
        return obj.startup.get_company_domain()
    
    def get_email_domain_valid(self, obj):
        return obj.is_email_domain_valid()
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours ago"
        else:
            return f"{diff.seconds // 60} minutes ago"
    
    def validate_email(self, value):
        """Validate email format and domain"""
        if not value:
            raise serializers.ValidationError("Email is required")
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Invalid email format")
        
        return value.lower()
    
    def validate_position(self, value):
        """Validate position field"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Position must be at least 2 characters long")
        if len(value) > 100:
            raise serializers.ValidationError("Position must be less than 100 characters")
        return value.strip()
    
    def validate_reason(self, value):
        """Validate reason field"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters long")
        if len(value) > 1000:
            raise serializers.ValidationError("Reason must be less than 1000 characters")
        return value.strip()
    
    def validate(self, attrs):
        """Validate the entire claim request"""
        startup_id = attrs.get('startup')
        email = attrs.get('email')
        
        if startup_id and email:
            # Get the startup object (startup_id could be an ID or object)
            if hasattr(startup_id, 'get_company_domain'):
                startup = startup_id  # It's already a startup object
            else:
                # It's an ID, fetch the startup object
                try:
                    startup = Startup.objects.get(id=startup_id)
                except Startup.DoesNotExist:
                    raise serializers.ValidationError({
                        'startup': 'Invalid startup ID.'
                    })
            
            # Check if email domain matches startup domain
            email_domain = email.split('@')[1].lower()
            startup_domain = startup.get_company_domain()
            
            if not startup_domain:
                raise serializers.ValidationError({
                    'startup': 'This startup does not have a website configured for domain verification.'
                })
            
            # Check domain match
            if not (email_domain == startup_domain or email_domain.endswith('.' + startup_domain)):
                raise serializers.ValidationError({
                    'email': f'Email domain ({email_domain}) does not match startup domain ({startup_domain}). Please use a company email address.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create claim request with verification token"""
        # Set expiration time (24 hours)
        validated_data['expires_at'] = timezone.now() + timedelta(hours=24)
        
        # Create the claim request
        claim_request = StartupClaimRequest.objects.create(**validated_data)
        
        # Generate verification token
        claim_request.generate_verification_token()
        claim_request.save()
        
        return claim_request

class StartupClaimRequestDetailSerializer(StartupClaimRequestSerializer):
    """Detailed serializer for viewing claim requests (admin)"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    startup_website = serializers.CharField(source='startup.website', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta(StartupClaimRequestSerializer.Meta):
        fields = StartupClaimRequestSerializer.Meta.fields + [
            'user_username', 'user_email', 'reviewed_by', 'reviewed_by_username', 
            'reviewed_at', 'review_notes', 'startup_website', 'verification_token', 
            'is_expired', 'updated_at'
        ]
        read_only_fields = StartupClaimRequestSerializer.Meta.read_only_fields + [
            'user', 'reviewed_by', 'reviewed_at', 'review_notes', 'verification_token',
            'updated_at'
        ]
    
    def get_is_expired(self, obj):
        return obj.is_expired()

# Base list serializer - MUST come before DetailSerializer
class StartupListSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    industry_icon = serializers.CharField(source='industry.icon', read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_ratings = serializers.ReadOnlyField()
    is_bookmarked = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    tags_list = serializers.StringRelatedField(source='tags', many=True, read_only=True)
    total_likes = serializers.SerializerMethodField()
    total_bookmarks = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_claim = serializers.SerializerMethodField()
    has_pending_edits = serializers.SerializerMethodField()
    has_pending_claims = serializers.SerializerMethodField()
    cover_image_display_url = serializers.ReadOnlyField()
    
    # Claim information
    is_claimed = serializers.ReadOnlyField()
    claim_verified = serializers.ReadOnlyField()
    claimed_by_username = serializers.CharField(source='claimed_by.username', read_only=True, allow_null=True)
    
    has_analytics_access = serializers.SerializerMethodField()
    has_advanced_search = serializers.SerializerMethodField()
    is_featured = serializers.SerializerMethodField()
    
    class Meta:
        model = Startup
        fields = [
            'id', 'name', 'description', 'industry', 'industry_name', 'industry_icon',
            'location', 'website', 'logo', 'funding_amount', 'valuation', 'employee_count',
            'founded_year', 'is_featured', 'revenue', 'user_count', 'growth_rate',
            'views', 'average_rating', 'total_ratings', 'is_bookmarked', 'is_liked',
            'tags_list', 'created_at', 'total_likes', 'total_bookmarks', 'total_comments',
            'cover_image_url', 'cover_image_display_url', 'can_edit', 'can_delete', 'can_claim', 'has_pending_edits',
            'has_pending_claims', 'is_approved', 'contact_email', 'contact_phone', 
            'business_model', 'target_market', 'is_claimed', 'claim_verified', 'claimed_by_username',
            'has_analytics_access', 'has_advanced_search'
        ]
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return StartupBookmark.objects.filter(startup=obj, user=request.user).exists()
        return False
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return StartupLike.objects.filter(startup=obj, user=request.user).exists()
        return False
    
    def get_total_likes(self, obj):
        return obj.likes.count()
    
    def get_total_bookmarks(self, obj):
        return obj.bookmarks.count()
    
    def get_total_comments(self, obj):
        return obj.comments.count()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            # Only admins can delete startups
            return user.is_staff or user.is_superuser
        return False
    
    def get_can_claim(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.can_claim(request.user)
        return False
    
    def get_has_pending_edits(self, obj):
        return obj.has_pending_edits()
    
    def get_has_pending_claims(self, obj):
        return obj.has_pending_claims()
    
    
    def get_has_analytics_access(self, obj):
        """Check if user has analytics access"""
        # Disabled while subscriptions app is not active
        return True
    
    def get_has_advanced_search(self, obj):
        """Check if user has advanced search"""
        # Disabled while subscriptions app is not active
        return True
    
    def get_is_featured(self, obj):
        """Check if startup should display featured badge (owner is Pro user)"""
        # Disabled while subscriptions app is not active
        return False
    
# Add these serializers to the END of your serializers.py file

# Detailed serializers for ratings and comments
class StartupRatingDetailSerializer(StartupRatingSerializer):
    """Detailed serializer for startup ratings"""
    pass  # Uses the same structure as base StartupRatingSerializer

class StartupCommentDetailSerializer(StartupCommentSerializer):
    """Detailed serializer for startup comments"""
    pass  # Uses the same structure as base StartupCommentSerializer

# Create serializer for new startups
class StartupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new startups"""
    founders = StartupFounderSerializer(many=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    
    class Meta:
        model = Startup
        fields = [
            'name', 'description', 'industry', 'location', 'website', 'logo',
            'funding_amount', 'valuation', 'employee_count', 'founded_year',
            'revenue', 'user_count', 'growth_rate', 'contact_email', 'contact_phone',
            'business_model', 'target_market', 'cover_image_url', 'is_featured', 'founders', 'tags'
        ]
    
    def create(self, validated_data):
        founders_data = validated_data.pop('founders', [])
        tags_data = validated_data.pop('tags', [])
        
        # Handle is_featured - only staff/admin can set featured status directly
        # For regular users, we'll treat it as a "feature request" and set to False
        request = self.context.get('request')
        if request and request.user and not (request.user.is_staff or request.user.is_superuser):
            # Regular users can request featured status, but it's set to False initially
            # The request will be stored for admin review
            validated_data['is_featured'] = False
        
        # Create startup
        startup = Startup.objects.create(**validated_data)
        
        # Create founders
        for founder_data in founders_data:
            StartupFounder.objects.create(startup=startup, **founder_data)
        
        # Create tags
        for tag_name in tags_data:
            if tag_name.strip():
                StartupTag.objects.create(startup=startup, tag=tag_name.strip())
        
        return startup

# Detail serializer that extends the list serializer with more fields
class StartupDetailSerializer(StartupListSerializer):
    """Detailed serializer for startup detail view"""
    founders = StartupFounderSerializer(many=True, read_only=True)
    tags = StartupTagSerializer(many=True, read_only=True)
    ratings = StartupRatingSerializer(many=True, read_only=True)
    comments = StartupCommentSerializer(many=True, read_only=True)
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
    
    class Meta(StartupListSerializer.Meta):
        fields = StartupListSerializer.Meta.fields + [
            'founders', 'tags', 'ratings', 'comments', 'submitted_by_username',
            'social_media', 'updated_at'
        ]

# Edit Request Serializers
class StartupEditRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating edit requests"""
    startup_name = serializers.CharField(source='startup.name', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    
    class Meta:
        model = StartupEditRequest
        fields = [
            'id', 'startup', 'startup_name', 'requested_by', 'requested_by_username',
            'proposed_changes', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'requested_by', 'status', 'created_at']

class StartupEditRequestDetailSerializer(StartupEditRequestSerializer):
    """Detailed serializer for edit requests"""
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    
    class Meta(StartupEditRequestSerializer.Meta):
        fields = StartupEditRequestSerializer.Meta.fields + [
            'original_values', 'reviewed_by', 'reviewed_by_username', 
            'reviewed_at', 'review_notes', 'updated_at'
        ]
        read_only_fields = StartupEditRequestSerializer.Meta.read_only_fields + [
            'original_values', 'reviewed_by', 'reviewed_at', 'review_notes', 'updated_at'
        ]

class StartupAnalyticsSerializer(serializers.Serializer):
    """Serializer for startup analytics (premium feature)"""
    views_last_30_days = serializers.IntegerField()
    views_last_7_days = serializers.IntegerField()
    bookmarks_last_30_days = serializers.IntegerField()
    likes_last_30_days = serializers.IntegerField()
    comments_last_30_days = serializers.IntegerField()
    ratings_last_30_days = serializers.IntegerField()
    average_rating_last_30_days = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Geographic data
    top_countries = serializers.ListField(child=serializers.DictField())
    top_cities = serializers.ListField(child=serializers.DictField())
    
    # Engagement metrics
    engagement_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Trending data
    is_trending = serializers.BooleanField()
    trending_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    is_trial = serializers.BooleanField()
    days_until_expiry = serializers.IntegerField()
    
    # Feature access
    can_claim_startups = serializers.BooleanField()
    can_edit_startups = serializers.BooleanField()
    has_analytics_access = serializers.BooleanField()
    has_advanced_search = serializers.BooleanField()
    priority_support = serializers.BooleanField()
    verified_badge = serializers.BooleanField()
    
    # Usage limits
    max_startup_submissions = serializers.IntegerField()
    max_job_applications = serializers.IntegerField()
    startup_submissions_used = serializers.IntegerField()
    job_applications_used = serializers.IntegerField()
    startup_submissions_remaining = serializers.IntegerField()
    job_applications_remaining = serializers.IntegerField()