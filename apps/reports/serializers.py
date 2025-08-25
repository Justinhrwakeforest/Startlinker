from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserReport, PostReport, ReportAction, ReportStatistics

User = get_user_model()

class UserReportSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing user reports"""
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    reported_user_username = serializers.CharField(source='reported_user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    age_in_days = serializers.ReadOnlyField()
    response_time = serializers.ReadOnlyField()
    
    class Meta:
        model = UserReport
        fields = [
            'id', 'reporter', 'reporter_username', 'reported_user', 'reported_user_username',
            'report_type', 'report_type_display', 'reason', 'evidence_urls',
            'status', 'status_display', 'priority', 'priority_display',
            'created_at', 'updated_at', 'resolved_at', 'age_in_days', 'response_time'
        ]
        read_only_fields = [
            'id', 'reporter', 'status', 'priority', 'created_at', 'updated_at', 
            'resolved_at', 'age_in_days', 'response_time'
        ]
    
    def validate_reason(self, value):
        """Validate reason field"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Please provide a detailed explanation (at least 10 characters) of why you are reporting this user."
            )
        if len(value) > 2000:
            raise serializers.ValidationError(
                "Report reason must be less than 2000 characters."
            )
        return value.strip()
    
    def validate_evidence_urls(self, value):
        """Validate evidence URLs"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Evidence URLs must be provided as a list.")
        
        if len(value) > 10:
            raise serializers.ValidationError("You can provide a maximum of 10 evidence URLs.")
        
        # Basic URL validation
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for url in value:
            if not isinstance(url, str) or not url_pattern.match(url):
                raise serializers.ValidationError(f"'{url}' is not a valid URL.")
        
        return value
    
    def validate(self, attrs):
        """Validate the entire report"""
        reporter = self.context['request'].user
        reported_user = attrs.get('reported_user')
        
        # Users cannot report themselves
        if reporter == reported_user:
            raise serializers.ValidationError({
                'reported_user': 'You cannot report yourself.'
            })
        
        # Check for recent duplicate reports
        recent_reports = UserReport.objects.filter(
            reporter=reporter,
            reported_user=reported_user,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        )
        
        if recent_reports.exists():
            raise serializers.ValidationError({
                'non_field_errors': 'You have already reported this user in the last 24 hours. Please wait before submitting another report.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create a new report"""
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class UserReportListSerializer(UserReportSerializer):
    """Simplified serializer for listing user reports"""
    class Meta(UserReportSerializer.Meta):
        fields = [
            'id', 'reported_user_username', 'report_type', 'report_type_display',
            'status', 'status_display', 'priority', 'priority_display',
            'created_at', 'age_in_days'
        ]


class ReportActionSerializer(serializers.ModelSerializer):
    """Serializer for report actions (admin use)"""
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = ReportAction
        fields = [
            'id', 'report', 'admin', 'admin_username', 'action_type', 
            'action_type_display', 'description', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'admin', 'created_at']
    
    def create(self, validated_data):
        """Create a new report action"""
        validated_data['admin'] = self.context['request'].user
        return super().create(validated_data)


class AdminUserReportSerializer(UserReportSerializer):
    """Extended serializer for admin use with additional fields"""
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    assigned_admin = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        allow_null=True
    )
    assigned_admin_username = serializers.CharField(
        source='assigned_admin.username', 
        read_only=True
    )
    actions = ReportActionSerializer(many=True, read_only=True)
    
    # Reporter details
    reporter_email = serializers.CharField(source='reporter.email', read_only=True)
    reporter_join_date = serializers.DateTimeField(source='reporter.date_joined', read_only=True)
    
    # Reported user details
    reported_user_email = serializers.CharField(source='reported_user.email', read_only=True)
    reported_user_join_date = serializers.DateTimeField(source='reported_user.date_joined', read_only=True)
    
    class Meta(UserReportSerializer.Meta):
        fields = UserReportSerializer.Meta.fields + [
            'admin_notes', 'assigned_admin', 'assigned_admin_username', 'actions',
            'reporter_email', 'reporter_join_date', 'reported_user_email', 'reported_user_join_date'
        ]
        read_only_fields = [
            'id', 'reporter', 'created_at', 'updated_at', 'resolved_at', 
            'age_in_days', 'response_time'
        ]
    
    def update(self, instance, validated_data):
        """Update report with admin actions tracking"""
        request = self.context.get('request')
        admin_user = request.user if request else None
        
        # Track status changes
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        if old_status != new_status and admin_user:
            # Create action record for status change
            ReportAction.objects.create(
                report=instance,
                admin=admin_user,
                action_type='status_change',
                description=f"Status changed from '{old_status}' to '{new_status}'",
                metadata={'old_status': old_status, 'new_status': new_status}
            )
        
        # Track priority changes
        old_priority = instance.priority
        new_priority = validated_data.get('priority', old_priority)
        
        if old_priority != new_priority and admin_user:
            ReportAction.objects.create(
                report=instance,
                admin=admin_user,
                action_type='priority_change',
                description=f"Priority changed from '{old_priority}' to '{new_priority}'",
                metadata={'old_priority': old_priority, 'new_priority': new_priority}
            )
        
        # Track assignment changes
        old_assigned = instance.assigned_admin
        new_assigned = validated_data.get('assigned_admin', old_assigned)
        
        if old_assigned != new_assigned and admin_user:
            old_name = old_assigned.username if old_assigned else 'Unassigned'
            new_name = new_assigned.username if new_assigned else 'Unassigned'
            ReportAction.objects.create(
                report=instance,
                admin=admin_user,
                action_type='assignment_change',
                description=f"Assigned to changed from '{old_name}' to '{new_name}'",
                metadata={
                    'old_assigned_id': old_assigned.id if old_assigned else None,
                    'new_assigned_id': new_assigned.id if new_assigned else None
                }
            )
        
        # Track admin notes
        old_notes = instance.admin_notes
        new_notes = validated_data.get('admin_notes', old_notes)
        
        if old_notes != new_notes and admin_user:
            ReportAction.objects.create(
                report=instance,
                admin=admin_user,
                action_type='note_added',
                description="Admin notes updated",
                metadata={'notes_added': True}
            )
        
        return super().update(instance, validated_data)


class ReportStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for report statistics"""
    
    class Meta:
        model = ReportStatistics
        fields = [
            'id', 'date', 'total_reports', 'pending_reports', 'resolved_reports',
            'avg_response_time_hours', 'report_type_breakdown', 'priority_breakdown',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard statistics"""
    total_reports = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    investigating_reports = serializers.IntegerField()
    resolved_reports = serializers.IntegerField()
    dismissed_reports = serializers.IntegerField()
    
    high_priority_reports = serializers.IntegerField()
    critical_reports = serializers.IntegerField()
    
    avg_response_time_hours = serializers.FloatField()
    reports_last_24h = serializers.IntegerField()
    reports_last_week = serializers.IntegerField()
    
    report_type_breakdown = serializers.DictField()
    priority_breakdown = serializers.DictField()
    status_breakdown = serializers.DictField()
    
    top_reported_users = serializers.ListField()
    recent_reports = AdminUserReportSerializer(many=True)


class PostReportSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing post reports"""
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    post_author_username = serializers.CharField(source='post.author.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    age_in_days = serializers.ReadOnlyField()
    
    class Meta:
        model = PostReport
        fields = [
            'id', 'reporter', 'reporter_username', 'post', 'post_author_username', 'post_title',
            'report_type', 'report_type_display', 'reason', 'additional_context',
            'status', 'status_display', 'priority', 'priority_display',
            'action_taken', 'created_at', 'updated_at', 'resolved_at', 'age_in_days'
        ]
        read_only_fields = [
            'id', 'reporter', 'status', 'priority', 'action_taken',
            'created_at', 'updated_at', 'resolved_at', 'age_in_days'
        ]
    
    def validate_reason(self, value):
        """Validate reason field"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Please provide a detailed explanation (at least 10 characters) of why you are reporting this post."
            )
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Report reason must be less than 1000 characters."
            )
        return value.strip()
    
    def validate(self, attrs):
        """Validate the entire report"""
        reporter = self.context['request'].user
        post = attrs.get('post')
        
        # Users cannot report their own posts
        if reporter == post.author:
            raise serializers.ValidationError({
                'post': 'You cannot report your own post.'
            })
        
        # Check for existing report from this user for this post
        if PostReport.objects.filter(reporter=reporter, post=post).exists():
            raise serializers.ValidationError({
                'non_field_errors': 'You have already reported this post.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create a new post report"""
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class PostReportListSerializer(PostReportSerializer):
    """Simplified serializer for listing post reports"""
    class Meta(PostReportSerializer.Meta):
        fields = [
            'id', 'post_author_username', 'post_title', 'report_type', 'report_type_display',
            'status', 'status_display', 'priority', 'priority_display',
            'created_at', 'age_in_days'
        ]


class AdminPostReportSerializer(PostReportSerializer):
    """Extended serializer for admin use with additional fields"""
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    assigned_admin = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        allow_null=True
    )
    assigned_admin_username = serializers.CharField(
        source='assigned_admin.username', 
        read_only=True
    )
    
    # Reporter details
    reporter_email = serializers.CharField(source='reporter.email', read_only=True)
    reporter_join_date = serializers.DateTimeField(source='reporter.date_joined', read_only=True)
    
    # Post details
    post_author_id = serializers.IntegerField(source='post.author.id', read_only=True)
    post_content_preview = serializers.SerializerMethodField()
    post_created_at = serializers.DateTimeField(source='post.created_at', read_only=True)
    
    class Meta(PostReportSerializer.Meta):
        fields = PostReportSerializer.Meta.fields + [
            'admin_notes', 'assigned_admin', 'assigned_admin_username',
            'reporter_email', 'reporter_join_date', 'post_author_id', 'post_content_preview', 'post_created_at'
        ]
        read_only_fields = [
            'id', 'reporter', 'created_at', 'updated_at', 'resolved_at', 'age_in_days'
        ]
    
    def get_post_content_preview(self, obj):
        """Get truncated post content for preview"""
        content = obj.post.content
        if len(content) > 200:
            return content[:200] + "..."
        return content


class BulkReportActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on reports"""
    report_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=50
    )
    action_type = serializers.ChoiceField(choices=[
        ('mark_investigating', 'Mark as Investigating'),
        ('mark_resolved', 'Mark as Resolved'),
        ('mark_dismissed', 'Mark as Dismissed'),
        ('set_high_priority', 'Set High Priority'),
        ('set_medium_priority', 'Set Medium Priority'),
        ('assign_to_me', 'Assign to Me'),
    ])
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Optional reason for the bulk action"
    )
    
    def validate_report_ids(self, value):
        """Validate that all report IDs exist"""
        existing_ids = UserReport.objects.filter(id__in=value).values_list('id', flat=True)
        missing_ids = set(value) - set(existing_ids)
        
        if missing_ids:
            raise serializers.ValidationError(
                f"Report IDs not found: {list(missing_ids)}"
            )
        
        return value