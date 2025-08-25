from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserInterest, UserSettings, validate_username, validate_first_name, validate_last_name, Resume
from .profanity_filter import validate_user_input

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def validate_email(self, value):
        """Check if email is already in use"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email address already exists. Please use a different email or try logging in.")
        return value
    
    def validate_password(self, value):
        validate_password(value)
        return value
    
    def validate_username(self, value):
        """Validate username for profanity and format during registration"""
        if value:
            try:
                validate_username(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_first_name(self, value):
        """Validate first name for profanity and format"""
        if value:
            try:
                validate_first_name(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_last_name(self, value):
        """Validate last name for profanity and format"""
        if value:
            try:
                validate_last_name(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(required=False, default=False)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Invalid email or password.')
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return data

class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        fields = ['id', 'interest']


class ResumeSerializer(serializers.ModelSerializer):
    file_size_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'title', 'file', 'file_url', 'is_default', 
            'uploaded_at', 'updated_at', 'file_size', 'file_size_display', 'file_type'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'file_size', 'file_type']
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_file(self, value):
        """Validate file type and size"""
        if value:
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'txt']
            ext = value.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
                )
            
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    "File size too large. Maximum allowed size is 10MB."
                )
        
        return value
    
    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    interests = UserInterestSerializer(many=True, read_only=True)
    resumes = ResumeSerializer(many=True, read_only=True)
    total_ratings = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    total_bookmarks = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    member_since = serializers.DateTimeField(source='date_joined', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'bio', 
            'location', 'profile_picture', 'avatar_url', 'display_name', 'is_premium', 'member_since', 'interests',
            'resumes', 'total_ratings', 'total_comments', 'total_bookmarks', 'total_likes',
            'follower_count', 'following_count',  # Social fields
            'is_staff', 'is_superuser'  # Added admin permission fields
        ]
        read_only_fields = ['id', 'email', 'is_premium', 'is_staff', 'is_superuser', 'member_since']  # Allow username updates
    
    def validate_username(self, value):
        """Validate username when updating profile"""
        if value:
            # Check if username is being changed
            if self.instance and self.instance.username != value:
                # Check if new username is already taken
                if User.objects.filter(username=value).exists():
                    raise serializers.ValidationError("Username is already taken.")
            
            # Apply our custom validation rules
            try:
                validate_username(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        
        return value
    
    def validate_first_name(self, value):
        """Validate first name for profanity and format when updating profile"""
        if value:
            try:
                validate_first_name(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_last_name(self, value):
        """Validate last name for profanity and format when updating profile"""
        if value:
            try:
                validate_last_name(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def get_avatar_url(self, obj):
        return obj.get_avatar_url()
    
    def get_display_name(self, obj):
        return obj.get_display_name()
    
    def get_total_ratings(self, obj):
        return obj.startuprating_set.count()
    
    def get_total_comments(self, obj):
        return obj.startupcomment_set.count()
    
    def get_total_bookmarks(self, obj):
        return obj.startupbookmark_set.count()
    
    def get_total_likes(self, obj):
        return obj.startuplike_set.count()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate_new_password(self, value):
        validate_password(value)
        return value
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return data

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'email_notifications', 'push_notifications', 'marketing_emails', 
            'weekly_digest', 'job_alerts', 'startup_updates',
            'profile_visibility', 'show_activity', 'show_bookmarks', 
            'show_ratings', 'allow_messages',
            'theme', 'language', 'timezone', 'items_per_page'
        ]