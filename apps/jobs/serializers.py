# startup_hub/apps/jobs/serializers.py - Updated without email verification checks

from rest_framework import serializers
from django.db import models
from django.contrib.auth import get_user_model
from apps.startups.models import Startup
from .models import JobType, Job, JobSkill, JobApplication, JobEditRequest

User = get_user_model()

class JobTypeSerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobType
        fields = ['id', 'name', 'job_count']
    
    def get_job_count(self, obj):
        return obj.job_set.filter(is_active=True, status='active').count()

class JobSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSkill
        fields = ['id', 'skill', 'is_required', 'proficiency_level']

class JobSkillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSkill
        fields = ['skill', 'is_required', 'proficiency_level']

class JobListSerializer(serializers.ModelSerializer):
    startup_name = serializers.SerializerMethodField()
    startup_logo = serializers.SerializerMethodField()
    startup_location = serializers.SerializerMethodField()
    startup_industry = serializers.SerializerMethodField()
    startup_employee_count = serializers.SerializerMethodField()
    job_type_name = serializers.CharField(source='job_type.name', read_only=True)
    skills_list = serializers.StringRelatedField(source='skills', many=True, read_only=True)
    posted_ago = serializers.ReadOnlyField()
    has_applied = serializers.SerializerMethodField()
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_since_posted = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    posted_by_username = serializers.CharField(source='posted_by.username', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'location', 'salary_range', 'is_remote',
            'is_urgent', 'experience_level', 'experience_level_display', 'status', 
            'status_display', 'posted_at', 'startup', 'startup_name', 'startup_logo', 
            'startup_location', 'startup_industry', 'startup_employee_count', 
            'job_type', 'job_type_name', 'skills_list', 'posted_ago', 'has_applied', 
            'days_since_posted', 'application_count', 'can_edit', 'posted_by_username',
            'view_count'
        ]
    
    def get_startup_name(self, obj):
        return obj.startup.name if obj.startup else 'Independent Job Posting'
    
    def get_startup_logo(self, obj):
        return obj.startup.logo if obj.startup else ''
    
    def get_startup_location(self, obj):
        return obj.startup.location if obj.startup else ''
    
    def get_startup_industry(self, obj):
        return obj.startup.industry.name if obj.startup and obj.startup.industry else 'Not specified'
    
    def get_startup_employee_count(self, obj):
        return obj.startup.employee_count if obj.startup else 0
    
    def get_has_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobApplication.objects.filter(job=obj, user=request.user).exists()
        return False
    
    def get_days_since_posted(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.posted_at
        return diff.days
    
    def get_application_count(self, obj):
        return obj.applications.count()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_edit(request.user)
        return False

class JobDetailSerializer(JobListSerializer):
    startup_detail = serializers.SerializerMethodField()
    skills = JobSkillSerializer(many=True, read_only=True)
    similar_jobs = serializers.SerializerMethodField()
    requirements_list = serializers.SerializerMethodField()
    benefits_list = serializers.SerializerMethodField()
    posted_by_info = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + [
            'startup_detail', 'skills', 'similar_jobs', 'requirements', 'benefits',
            'requirements_list', 'benefits_list', 'posted_by_info', 'company_email',
            'application_deadline', 'expires_at', 'can_delete', 'rejection_reason'
        ]
    
    def get_startup_detail(self, obj):
        if not obj.startup:
            return {
                'id': None,
                'name': 'Independent Job Posting',
                'logo': '',
                'description': 'This job was posted independently without a company profile.',
                'industry_name': 'Not specified',
                'industry_icon': '',
                'location': '',
                'website': '',
                'employee_count': 0,
                'founded_year': None,
                'is_featured': False,
                'funding_amount': '',
                'valuation': '',
                'cover_image_display_url': None,
            }
            
        startup = obj.startup
        return {
            'id': startup.id,
            'name': startup.name,
            'logo': startup.logo,
            'description': startup.description,
            'industry_name': startup.industry.name if startup.industry else 'Not specified',
            'industry_icon': startup.industry.icon if startup.industry else '',
            'location': startup.location,
            'website': startup.website,
            'employee_count': startup.employee_count,
            'founded_year': startup.founded_year,
            'is_featured': startup.is_featured,
            'funding_amount': startup.funding_amount,
            'valuation': startup.valuation,
            'cover_image_display_url': getattr(startup, 'cover_image_display_url', None),
        }
    
    def get_similar_jobs(self, obj):
        query_filter = models.Q(skills__skill__in=obj.skills.values_list('skill', flat=True))
        
        # Only add startup filter if the job has a startup
        if obj.startup:
            query_filter |= models.Q(startup=obj.startup)
            
        similar = Job.objects.filter(query_filter).exclude(
            id=obj.id
        ).filter(is_active=True, status='active').distinct()[:3]
        
        return [{
            'id': job.id,
            'title': job.title,
            'startup_name': job.startup.name if job.startup else 'Independent Job Posting',
            'location': job.location,
            'is_remote': job.is_remote,
            'posted_ago': job.posted_ago
        } for job in similar]
    
    def get_requirements_list(self, obj):
        requirements = []
        if obj.requirements:
            # Split by line breaks and filter empty lines
            requirements = [req.strip() for req in obj.requirements.split('\n') if req.strip()]
        
        # Add skills as requirements
        skills = [skill.skill for skill in obj.skills.all()]
        if skills:
            requirements.extend(skills)
        
        # Add experience level
        requirements.append(f"{obj.get_experience_level_display()} experience")
        
        return requirements
    
    def get_benefits_list(self, obj):
        if obj.benefits:
            return [benefit.strip() for benefit in obj.benefits.split('\n') if benefit.strip()]
        return []
    
    def get_posted_by_info(self, obj):
        request = self.context.get('request')
        # Only show poster info to admins or the poster themselves
        if request and request.user.is_authenticated:
            if (request.user.is_staff or request.user.is_superuser or 
                request.user == obj.posted_by):
                return {
                    'username': obj.posted_by.username,
                    'email': obj.company_email
                }
        return None
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_delete(request.user)
        return False

class JobCreateSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False,
        help_text="List of skill objects with skill, is_required, and proficiency_level"
    )
    startup = serializers.PrimaryKeyRelatedField(
        queryset=Startup.objects.filter(is_approved=True),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'startup', 'location', 'job_type', 'salary_range',
            'is_remote', 'is_urgent', 'experience_level', 'requirements', 'benefits',
            'application_deadline', 'expires_at', 'company_email', 'skills'
        ]
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
            'location': {'required': True},
            'job_type': {'required': True},
            'company_email': {'required': False, 'allow_blank': True},
            'application_deadline': {'required': True},
            'expires_at': {'required': True},
        }
    
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Job title must be at least 5 characters long")
        if len(value) > 100:
            raise serializers.ValidationError("Job title must be less than 100 characters")
        return value.strip()
    
    def validate_description(self, value):
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Job description must be at least 50 characters long")
        if len(value) > 5000:
            raise serializers.ValidationError("Job description must be less than 5000 characters")
        return value.strip()
    
    def validate_company_email(self, value):
        # Email is now optional
        if not value:
            return ''
        
        # If provided, validate it
        if '@' not in value:
            raise serializers.ValidationError("Please provide a valid email address")
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please provide a valid email address")
        
        return value.lower()
    
    def validate_startup(self, value):
        if value and not value.is_approved:
            raise serializers.ValidationError("Can only post jobs for approved startups")
        return value
    
    def validate_skills(self, value):
        if not value:
            return []
        
        valid_skills = []
        for skill_data in value:
            if not isinstance(skill_data, dict):
                raise serializers.ValidationError("Each skill must be an object")
            
            skill_name = skill_data.get('skill', '').strip()
            if not skill_name:
                continue
            
            if len(skill_name) > 30:
                raise serializers.ValidationError("Skill name too long (max 30 characters)")
            
            is_required = skill_data.get('is_required', True)
            proficiency_level = skill_data.get('proficiency_level', 'intermediate')
            
            if proficiency_level not in ['beginner', 'intermediate', 'advanced', 'expert']:
                proficiency_level = 'intermediate'
            
            valid_skills.append({
                'skill': skill_name,
                'is_required': bool(is_required),
                'proficiency_level': proficiency_level
            })
        
        if len(valid_skills) > 20:
            raise serializers.ValidationError("Maximum 20 skills allowed")
        
        return valid_skills
    
    def validate_application_deadline(self, value):
        from django.utils import timezone
        from datetime import timedelta
        
        if not value:
            raise serializers.ValidationError("Application deadline is required")
        
        now = timezone.now()
        min_deadline = now + timedelta(days=1)  # At least 24 hours from now
        max_deadline = now + timedelta(days=365)  # Maximum 1 year from now
        
        if value <= now:
            raise serializers.ValidationError("Application deadline must be in the future")
        
        if value < min_deadline:
            raise serializers.ValidationError("Application deadline must be at least 24 hours from now")
        
        if value > max_deadline:
            raise serializers.ValidationError("Application deadline cannot be more than 1 year from now")
        
        return value
    
    def validate_expires_at(self, value):
        from django.utils import timezone
        from datetime import timedelta
        
        if not value:
            raise serializers.ValidationError("Job expiry date is required")
        
        now = timezone.now()
        min_expiry = now + timedelta(days=7)  # At least 1 week from now
        max_expiry = now + timedelta(days=365)  # Maximum 1 year from now
        
        if value <= now:
            raise serializers.ValidationError("Job expiry date must be in the future")
        
        if value < min_expiry:
            raise serializers.ValidationError("Job expiry date must be at least 1 week from now")
        
        if value > max_expiry:
            raise serializers.ValidationError("Job expiry date cannot be more than 1 year from now")
        
        return value
    
    def validate(self, attrs):
        # Validate application deadline vs expiry date
        application_deadline = attrs.get('application_deadline')
        expires_at = attrs.get('expires_at')
        
        if application_deadline and expires_at:
            if application_deadline >= expires_at:
                raise serializers.ValidationError({
                    'application_deadline': 'Application deadline must be before job expiry date'
                })
            
            # Ensure there's at least a day between deadline and expiry
            from datetime import timedelta
            if expires_at - application_deadline < timedelta(days=1):
                raise serializers.ValidationError({
                    'expires_at': 'Job expiry date must be at least 1 day after application deadline'
                })
        
        return attrs
    
    def create(self, validated_data):
        from django.conf import settings
        
        skills_data = validated_data.pop('skills', [])
        user = self.context['request'].user
        validated_data['posted_by'] = user
        
        # Determine if job should be auto-approved
        job_settings = getattr(settings, 'JOB_POSTING_SETTINGS', {})
        
        # Add logging for debugging
        import logging
        logger = logging.getLogger(__name__)
        
        # FORCE ALL JOBS TO REQUIRE APPROVAL
        # Check if REQUIRE_REVIEW is explicitly set to True
        require_review = job_settings.get('REQUIRE_REVIEW', False)
        auto_approve = job_settings.get('AUTO_APPROVE', True)
        
        logger.info(f"Job creation approval check: user={user.username}, "
                   f"REQUIRE_REVIEW={require_review}, AUTO_APPROVE={auto_approve}, "
                   f"is_staff={user.is_staff}, is_superuser={user.is_superuser}")
        
        should_auto_approve = False
        
        # If REQUIRE_REVIEW is True, NEVER auto-approve
        if require_review:
            should_auto_approve = False
            logger.info("Job approval decision: REQUIRE_REVIEW=True -> forcing pending status")
        else:
            # Only check other conditions if REQUIRE_REVIEW is False
            if (job_settings.get('AUTO_APPROVE_STAFF', True) and 
                (user.is_staff or user.is_superuser)):
                should_auto_approve = True
                logger.info("Job approval decision: Staff/superuser auto-approval triggered")
            elif auto_approve:
                should_auto_approve = True
                logger.info("Job approval decision: General auto-approval triggered")
            elif (job_settings.get('AUTO_APPROVE_VERIFIED_STARTUPS', True) and 
                  validated_data.get('startup') and 
                  validated_data['startup'].is_approved):
                should_auto_approve = True
                logger.info("Job approval decision: Verified startup auto-approval triggered")
            else:
                logger.info("Job approval decision: No auto-approval conditions met")
        
        # FORCE ALL JOBS TO PENDING STATUS - NO EXCEPTIONS
        # This is a temporary override to completely disable auto-approval
        validated_data['status'] = 'pending'
        validated_data['is_active'] = False
        logger.info("OVERRIDE: ALL JOBS FORCED TO PENDING STATUS")
        
        # Create the job
        job = Job.objects.create(**validated_data)
        
        # NO AUTO-APPROVAL INFO SET - ALL JOBS REQUIRE MANUAL APPROVAL
        
        # Create skills
        for skill_data in skills_data:
            JobSkill.objects.create(job=job, **skill_data)
        
        return job

class JobEditSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False
    )
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'location', 'salary_range', 'is_remote', 
            'is_urgent', 'experience_level', 'requirements', 'benefits',
            'application_deadline', 'expires_at', 'skills'
        ]
    
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Job title must be at least 5 characters long")
        return value.strip()
    
    def validate_description(self, value):
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Job description must be at least 50 characters long")
        return value.strip()
    
    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)
        
        # Check if job can be edited (additional validation)
        request = self.context.get('request')
        if request and not instance.can_user_edit(request.user):
            raise serializers.ValidationError("This job cannot be edited")
        
        # Store original status and check if this is a non-admin edit
        original_status = instance.status
        is_admin_edit = request and (request.user.is_staff or request.user.is_superuser)
        is_poster_edit = request and request.user == instance.posted_by and not is_admin_edit
        
        # Update job fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle approval workflow for non-admin edits
        if is_poster_edit:
            if original_status in ['active', 'rejected']:
                # Reset to pending for re-approval
                instance.status = 'pending'
                instance.is_active = False
                instance.approved_by = None
                instance.approved_at = None
                instance.rejection_reason = ''
            elif original_status in ['draft', 'pending']:
                # Keep as pending if already pending or draft
                instance.status = 'pending'
        
        instance.save()
        
        # Update skills if provided
        if skills_data is not None:
            # Clear existing skills
            instance.skills.all().delete()
            
            # Create new skills
            for skill_data in skills_data:
                if skill_data.get('skill'):
                    JobSkill.objects.create(job=instance, **skill_data)
        
        return instance

class JobEditRequestSerializer(serializers.ModelSerializer):
    changes_display = serializers.SerializerMethodField(read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = JobEditRequest
        fields = [
            'id', 'job', 'job_title', 'requested_by', 'status', 'proposed_changes',
            'original_values', 'changes_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'requested_by', 'status', 'original_values', 'created_at', 'updated_at']
    
    def get_changes_display(self, obj):
        return obj.get_changes_display() if hasattr(obj, 'get_changes_display') else []

class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    startup_name = serializers.CharField(source='job.startup.name', read_only=True)
    startup_logo = serializers.CharField(source='job.startup.logo', read_only=True)
    job_location = serializers.CharField(source='job.location', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    selected_resume = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'startup_name', 'startup_logo', 
            'job_location', 'cover_letter', 'status', 'status_display', 
            'applied_at', 'selected_resume', 'resume_url', 'additional_info'
        ]
        read_only_fields = ['status', 'applied_at']
    
    def get_selected_resume(self, obj):
        if obj.selected_resume:
            from apps.users.serializers import ResumeSerializer
            return ResumeSerializer(obj.selected_resume, context=self.context).data
        return None
    
    def get_resume_url(self, obj):
        # Return resume URL from selected resume or legacy resume field
        if obj.selected_resume and obj.selected_resume.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.selected_resume.file.url)
        elif obj.resume:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.resume.url)
        return None


class JobApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for job poster to view applications"""
    job_title = serializers.CharField(source='job.title', read_only=True)
    startup_name = serializers.CharField(source='job.startup.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    selected_resume = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()
    applicant = serializers.SerializerMethodField()
    conversation_status = serializers.SerializerMethodField()
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'startup_name', 'user', 'applicant',
            'cover_letter', 'status', 'status_display', 'applied_at', 'updated_at',
            'selected_resume', 'resume_url', 'additional_info',
            'reviewed_by', 'reviewed_at', 'review_notes',
            'interview_scheduled_at', 'interview_notes', 'conversation_status'
        ]
    
    def get_selected_resume(self, obj):
        if obj.selected_resume:
            from apps.users.serializers import ResumeSerializer
            return ResumeSerializer(obj.selected_resume, context=self.context).data
        return None
    
    def get_resume_url(self, obj):
        # Return resume URL from selected resume or legacy resume field
        if obj.selected_resume and obj.selected_resume.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.selected_resume.file.url)
        elif obj.resume:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.resume.url)
        return None
    
    def get_applicant(self, obj):
        """Return detailed applicant information"""
        user = obj.user
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'display_name': user.get_display_name(),
            'bio': user.bio,
            'location': user.location,
            'avatar_url': user.get_avatar_url(),
            'member_since': user.date_joined,
            'is_premium': user.is_premium,
            # Add activity stats
            'total_applications': user.job_applications.count(),
            'profile_completeness': self._calculate_profile_completeness(user)
        }
    
    def _calculate_profile_completeness(self, user):
        """Calculate profile completeness percentage"""
        fields = [
            user.first_name, user.last_name, user.bio, user.location,
            user.profile_picture
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)
    
    def get_conversation_status(self, obj):
        """Check if conversation exists for this application"""
        try:
            from apps.messaging.models import Conversation
            conversation = Conversation.objects.filter(
                related_job_application=obj,
                conversation_type='job_application'
            ).first()
            
            if conversation:
                return {
                    'exists': True,
                    'conversation_id': str(conversation.id),
                    'last_message_at': conversation.updated_at,
                    'participants_count': conversation.participants.count()
                }
            else:
                return {
                    'exists': False,
                    'conversation_id': None,
                    'last_message_at': None,
                    'participants_count': 0
                }
        except Exception:
            return {
                'exists': False,
                'conversation_id': None,
                'last_message_at': None,
                'participants_count': 0
            }


class MyJobsSerializer(serializers.ModelSerializer):
    """Serializer for jobs posted by the current user"""
    startup_name = serializers.SerializerMethodField()
    job_type_name = serializers.CharField(source='job_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    application_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    approval_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'startup', 'startup_name', 'job_type_name', 'location',
            'status', 'status_display', 'is_active', 'posted_at',
            'view_count', 'application_count', 'can_edit', 'can_delete', 'approval_info'
        ]
    
    def get_startup_name(self, obj):
        return obj.startup.name if obj.startup else 'Independent Job Posting'
    
    def get_application_count(self, obj):
        return obj.applications.count()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_edit(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_delete(request.user)
        return False
    
    def get_approval_info(self, obj):
        info = {
            'approved_at': obj.approved_at,
            'rejection_reason': obj.rejection_reason
        }
        if obj.approved_by:
            info['approved_by'] = obj.approved_by.username
        return info