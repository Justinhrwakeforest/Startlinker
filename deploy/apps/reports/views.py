from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

from .models import UserReport, PostReport, ReportAction, ReportStatistics, UserWarning, UserBan
from .serializers import (
    UserReportSerializer, UserReportListSerializer, AdminUserReportSerializer,
    PostReportSerializer, PostReportListSerializer, AdminPostReportSerializer,
    ReportActionSerializer, ReportDashboardSerializer, BulkReportActionSerializer
)

User = get_user_model()

class ReportPagination(PageNumberPagination):
    """Custom pagination for reports"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserReportCreateView(generics.CreateAPIView):
    """
    Create a new user report.
    Only authenticated users can submit reports.
    """
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Auto-assign priority based on report type
        report_type = serializer.validated_data.get('report_type')
        
        # Set higher priority for serious violations
        high_priority_types = ['harassment', 'hate_speech', 'scam', 'impersonation']
        critical_priority_types = ['harassment', 'hate_speech']
        
        if report_type in critical_priority_types:
            serializer.save(priority='critical')
        elif report_type in high_priority_types:
            serializer.save(priority='high')
        else:
            serializer.save(priority='medium')


class UserReportListView(generics.ListAPIView):
    """
    List user's submitted reports.
    Users can only see their own reports.
    """
    serializer_class = UserReportListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReportPagination
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status', 'report_type', 'priority']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return UserReport.objects.filter(reporter=self.request.user)


class UserReportDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific report.
    Users can only view their own reports.
    """
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserReport.objects.filter(reporter=self.request.user)


# Post Report Views
class PostReportCreateView(generics.CreateAPIView):
    """
    Create a new post report.
    Only authenticated users can submit reports.
    """
    serializer_class = PostReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Auto-assign priority based on report type
        report_type = serializer.validated_data.get('report_type')
        
        # Set higher priority for serious violations
        high_priority_types = ['harassment', 'hate_speech', 'violence', 'nudity']
        critical_priority_types = ['harassment', 'hate_speech', 'violence']
        
        if report_type in critical_priority_types:
            serializer.save(priority='critical')
        elif report_type in high_priority_types:
            serializer.save(priority='high')
        else:
            serializer.save(priority='medium')


class PostReportListView(generics.ListAPIView):
    """
    List user's submitted post reports.
    Users can only see their own reports.
    """
    serializer_class = PostReportListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReportPagination
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status', 'report_type', 'priority']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return PostReport.objects.filter(reporter=self.request.user).select_related('post__author')


class PostReportDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific post report.
    Users can only view their own reports.
    """
    serializer_class = PostReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PostReport.objects.filter(reporter=self.request.user).select_related('post__author')


# Admin Views
class AdminReportListView(generics.ListAPIView):
    """
    Admin view to list all reports with filtering and search.
    """
    serializer_class = AdminUserReportSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = ReportPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'report_type', 'assigned_admin']
    search_fields = ['reason', 'reporter__username', 'reported_user__username']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return UserReport.objects.select_related(
            'reporter', 'reported_user', 'assigned_admin'
        ).prefetch_related('actions__admin')


class AdminReportDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin view to get and update report details.
    """
    serializer_class = AdminUserReportSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return UserReport.objects.select_related(
            'reporter', 'reported_user', 'assigned_admin'
        ).prefetch_related('actions__admin')


# Admin Post Report Views
class AdminPostReportListView(generics.ListAPIView):
    """
    Admin view to list all post reports with filtering and search.
    """
    serializer_class = AdminPostReportSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = ReportPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'report_type', 'assigned_admin']
    search_fields = ['reason', 'reporter__username', 'post__author__username', 'post__title', 'post__content']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return PostReport.objects.select_related(
            'reporter', 'post__author', 'assigned_admin'
        )


class AdminPostReportDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin view to get and update post report details.
    """
    serializer_class = AdminPostReportSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return PostReport.objects.select_related(
            'reporter', 'post__author', 'assigned_admin'
        )


class ReportActionCreateView(generics.CreateAPIView):
    """
    Create a new action on a report (admin only).
    """
    serializer_class = ReportActionSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(admin=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_dashboard_stats(request):
    """
    Get comprehensive dashboard statistics for admin.
    """
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    # Basic counts
    total_reports = UserReport.objects.count()
    pending_reports = UserReport.objects.filter(status='pending').count()
    investigating_reports = UserReport.objects.filter(status='investigating').count()
    resolved_reports = UserReport.objects.filter(status='resolved').count()
    dismissed_reports = UserReport.objects.filter(status='dismissed').count()
    
    # Priority counts
    high_priority_reports = UserReport.objects.filter(priority='high').count()
    critical_reports = UserReport.objects.filter(priority='critical').count()
    
    # Time-based counts
    reports_last_24h = UserReport.objects.filter(created_at__gte=last_24h).count()
    reports_last_week = UserReport.objects.filter(created_at__gte=last_week).count()
    
    # Average response time
    resolved_reports_qs = UserReport.objects.filter(
        status__in=['resolved', 'dismissed'],
        resolved_at__isnull=False
    )
    
    avg_response_time = 0
    if resolved_reports_qs.exists():
        # Calculate average response time in hours
        response_times = []
        for report in resolved_reports_qs:
            diff = report.resolved_at - report.created_at
            response_times.append(diff.total_seconds() / 3600)  # Convert to hours
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
    
    # Breakdown by type
    report_type_breakdown = dict(
        UserReport.objects.values('report_type').annotate(
            count=Count('id')
        ).values_list('report_type', 'count')
    )
    
    # Breakdown by priority
    priority_breakdown = dict(
        UserReport.objects.values('priority').annotate(
            count=Count('id')
        ).values_list('priority', 'count')
    )
    
    # Breakdown by status
    status_breakdown = dict(
        UserReport.objects.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )
    
    # Top reported users (users with most reports against them)
    top_reported_users = list(
        UserReport.objects.values(
            'reported_user__username', 'reported_user__id'
        ).annotate(
            report_count=Count('id')
        ).filter(
            report_count__gt=1
        ).order_by('-report_count')[:10]
    )
    
    # Recent reports (last 10)
    recent_reports = UserReport.objects.select_related(
        'reporter', 'reported_user', 'assigned_admin'
    ).order_by('-created_at')[:10]
    
    data = {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'investigating_reports': investigating_reports,
        'resolved_reports': resolved_reports,
        'dismissed_reports': dismissed_reports,
        'high_priority_reports': high_priority_reports,
        'critical_reports': critical_reports,
        'avg_response_time_hours': round(avg_response_time, 2),
        'reports_last_24h': reports_last_24h,
        'reports_last_week': reports_last_week,
        'report_type_breakdown': report_type_breakdown,
        'priority_breakdown': priority_breakdown,
        'status_breakdown': status_breakdown,
        'top_reported_users': top_reported_users,
        'recent_reports': AdminUserReportSerializer(recent_reports, many=True).data
    }
    
    serializer = ReportDashboardSerializer(data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def bulk_report_action(request):
    """
    Perform bulk actions on multiple reports.
    """
    serializer = BulkReportActionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    report_ids = serializer.validated_data['report_ids']
    action_type = serializer.validated_data['action_type']
    reason = serializer.validated_data.get('reason', '')
    
    reports = UserReport.objects.filter(id__in=report_ids)
    updated_count = 0
    
    with transaction.atomic():
        for report in reports:
            old_status = report.status
            old_priority = report.priority
            old_assigned = report.assigned_admin
            
            # Apply the action
            if action_type == 'mark_investigating':
                report.status = 'investigating'
            elif action_type == 'mark_resolved':
                report.status = 'resolved'
                if not report.resolved_at:
                    report.resolved_at = timezone.now()
            elif action_type == 'mark_dismissed':
                report.status = 'dismissed'
                if not report.resolved_at:
                    report.resolved_at = timezone.now()
            elif action_type == 'set_high_priority':
                report.priority = 'high'
            elif action_type == 'set_medium_priority':
                report.priority = 'medium'
            elif action_type == 'assign_to_me':
                report.assigned_admin = request.user
            
            report.save()
            
            # Create action record
            action_description = f"Bulk action: {action_type.replace('_', ' ').title()}"
            if reason:
                action_description += f" - Reason: {reason}"
            
            ReportAction.objects.create(
                report=report,
                admin=request.user,
                action_type='other',
                description=action_description,
                metadata={
                    'bulk_action': True,
                    'action_type': action_type,
                    'reason': reason,
                    'old_status': old_status,
                    'old_priority': old_priority,
                    'old_assigned_id': old_assigned.id if old_assigned else None
                }
            )
            
            updated_count += 1
    
    return Response({
        'message': f'Successfully applied {action_type} to {updated_count} reports.',
        'updated_count': updated_count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_report_exists(request, user_id):
    """
    Check if the current user has already reported a specific user.
    """
    try:
        reported_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check for existing reports
    existing_report = UserReport.objects.filter(
        reporter=request.user,
        reported_user=reported_user
    ).first()
    
    if existing_report:
        return Response({
            'has_reported': True,
            'report_id': existing_report.id,
            'report_status': existing_report.status,
            'created_at': existing_report.created_at
        })
    
    return Response({'has_reported': False})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_post_report_exists(request, post_id):
    """
    Check if the current user has already reported a specific post.
    """
    try:
        from apps.posts.models import Post
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check for existing reports
    existing_report = PostReport.objects.filter(
        reporter=request.user,
        post=post
    ).first()
    
    if existing_report:
        return Response({
            'has_reported': True,
            'report_id': existing_report.id,
            'report_status': existing_report.status,
            'created_at': existing_report.created_at
        })
    
    return Response({'has_reported': False})


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def user_report_history(request, user_id):
    """
    Get all reports related to a specific user (both as reporter and reported user).
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Reports made by this user
    reports_made = UserReport.objects.filter(reporter=user).order_by('-created_at')
    
    # Reports made against this user
    reports_received = UserReport.objects.filter(reported_user=user).order_by('-created_at')
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'reports_made': UserReportListSerializer(reports_made, many=True).data,
        'reports_received': AdminUserReportSerializer(reports_received, many=True).data,
        'reports_made_count': reports_made.count(),
        'reports_received_count': reports_received.count()
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_user_action(request):
    """
    Perform administrative actions on users (warn, temporary ban, permanent ban).
    """
    from apps.notifications.models import Notification
    
    print("=== admin_user_action called ===")
    print("Request data:", request.data)
    print("User:", request.user)
    
    user_id = request.data.get('user_id')
    action_type = request.data.get('action_type')
    report_id = request.data.get('report_id')
    message = request.data.get('message', '')
    ban_duration_days = request.data.get('ban_duration_days')
    reason = request.data.get('reason', '')
    
    print(f"Parsed data: user_id={user_id}, action_type={action_type}, report_id={report_id}")
    
    # Validate required fields
    if not action_type:
        return Response({'error': 'action_type is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not user_id and not report_id:
        return Response({'error': 'Either user_id or report_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if action_type not in ['warn', 'temp_ban', 'permanent_ban']:
        return Response({'error': 'Invalid action_type. Must be warn, temp_ban, or permanent_ban'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the related report if provided and determine target user
    report = None
    post_report = None
    target_user = None
    
    try:
        if report_id:
            print(f"Looking for report with ID: {report_id}")
            try:
                # Try to find it as a UserReport first
                report = UserReport.objects.get(id=report_id)
                print(f"Found UserReport: {report}")
                # For user reports, use the provided user_id or the reported_user
                if user_id:
                    target_user = User.objects.get(id=user_id)
                else:
                    target_user = report.reported_user
                    print(f"Target user from UserReport: {target_user}")
            except UserReport.DoesNotExist:
                print("UserReport not found, trying PostReport...")
                try:
                    # Try to find it as a PostReport
                    post_report = PostReport.objects.get(id=report_id)
                    print(f"Found PostReport: {post_report}")
                    # For post reports, target the post author
                    if user_id:
                        target_user = User.objects.get(id=user_id)
                    else:
                        target_user = post_report.post.author
                        print(f"Target user from PostReport: {target_user}")
                except PostReport.DoesNotExist:
                    print("PostReport not found either")
                    return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # No report_id provided, use user_id directly
            print(f"No report_id, using user_id: {user_id}")
            if not user_id:
                return Response({'error': 'Either user_id or report_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            target_user = User.objects.get(id=user_id)
            print(f"Target user from user_id: {target_user}")
    except User.DoesNotExist as e:
        print(f"User.DoesNotExist error: {e}")
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Unexpected error in user lookup: {e}")
        return Response({'error': f'Internal error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    with transaction.atomic():
        if action_type == 'warn':
            if not message:
                return Response({'error': 'Message is required for warnings'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create warning record
            warning = UserWarning.objects.create(
                user=target_user,
                admin=request.user,
                report=report,
                post_report=post_report,
                message=message,
                reason=reason
            )
            
            # Send notification to user
            Notification.create_notification(
                recipient=target_user,
                notification_type='system',
                title='⚠️ Official Warning - Action Required',
                message=f"IMPORTANT: You have received an official warning from our moderation team.\n\nMessage: {message}\n\n⚠️ This is a formal warning. Continued violations of our community guidelines may result in temporary or permanent account suspension. Please review our terms of service immediately.",
                sender=None,
                extra_data={
                    'warning_id': warning.id,
                    'admin_username': request.user.username,
                    'action_type': 'warning',
                    'severity': 'high'
                }
            )
            
            # Create action record if there's a report
            if report:
                ReportAction.objects.create(
                    report=report,
                    admin=request.user,
                    action_type='user_warned',
                    description=f"User {target_user.username} was warned for violating community guidelines",
                    metadata={
                        'warning_id': warning.id,
                        'message': message,
                        'reason': reason
                    }
                )
            
            return Response({
                'message': f'Warning sent to {target_user.username} successfully.',
                'warning_id': warning.id
            })
            
        elif action_type == 'temp_ban':
            if not ban_duration_days:
                return Response({'error': 'ban_duration_days is required for temporary bans'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                duration = int(ban_duration_days)
                if duration <= 0:
                    raise ValueError("Duration must be positive")
            except (ValueError, TypeError):
                return Response({'error': 'ban_duration_days must be a positive integer'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user already has an active ban
            existing_ban = UserBan.objects.filter(user=target_user, is_active=True).first()
            if existing_ban:
                return Response({'error': f'User already has an active {existing_ban.get_ban_type_display().lower()}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create ban record
            ban = UserBan.objects.create(
                user=target_user,
                admin=request.user,
                report=report,
                post_report=post_report,
                ban_type='temporary',
                reason=reason,
                duration_days=duration
            )
            
            # Send notification to user
            Notification.create_notification(
                recipient=target_user,
                notification_type='system',
                title='🚫 Account Temporarily Suspended',
                message=f"Your account has been temporarily suspended for {duration} days due to community guideline violations. Reason: {reason}",
                sender=None,
                extra_data={
                    'ban_id': ban.id,
                    'admin_username': request.user.username,
                    'action_type': 'temporary_ban',
                    'duration_days': duration,
                    'expires_at': ban.expires_at.isoformat() if ban.expires_at else None
                }
            )
            
            # Create action record if there's a report
            if report:
                ReportAction.objects.create(
                    report=report,
                    admin=request.user,
                    action_type='user_suspended',
                    description=f"User {target_user.username} was temporarily banned for {duration} days",
                    metadata={
                        'ban_id': ban.id,
                        'duration_days': duration,
                        'reason': reason,
                        'expires_at': ban.expires_at.isoformat() if ban.expires_at else None
                    }
                )
            
            return Response({
                'message': f'User {target_user.username} temporarily banned for {duration} days.',
                'ban_id': ban.id,
                'expires_at': ban.expires_at
            })
            
        elif action_type == 'permanent_ban':
            # Show confirmation requirement
            confirmation = request.data.get('confirmed', False)
            if not confirmation:
                return Response({
                    'error': 'Permanent bans require confirmation',
                    'confirmation_required': True,
                    'message': f'Are you sure you want to permanently ban {target_user.username}? This action cannot be undone.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user already has an active ban
            existing_ban = UserBan.objects.filter(user=target_user, is_active=True).first()
            if existing_ban:
                return Response({'error': f'User already has an active {existing_ban.get_ban_type_display().lower()}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create ban record
            ban = UserBan.objects.create(
                user=target_user,
                admin=request.user,
                report=report,
                post_report=post_report,
                ban_type='permanent',
                reason=reason
            )
            
            # Send notification to user
            Notification.create_notification(
                recipient=target_user,
                notification_type='system',
                title='🚫 Account Permanently Suspended',
                message=f"Your account has been permanently suspended due to severe violations of our community guidelines. Reason: {reason}",
                sender=None,
                extra_data={
                    'ban_id': ban.id,
                    'admin_username': request.user.username,
                    'action_type': 'permanent_ban'
                }
            )
            
            # Create action record if there's a report
            if report:
                ReportAction.objects.create(
                    report=report,
                    admin=request.user,
                    action_type='user_banned',
                    description=f"User {target_user.username} was permanently banned",
                    metadata={
                        'ban_id': ban.id,
                        'reason': reason
                    }
                )
            
            return Response({
                'message': f'User {target_user.username} permanently banned.',
                'ban_id': ban.id
            })
    
    return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)