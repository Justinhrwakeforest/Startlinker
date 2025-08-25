# apps/users/activity_api_views.py - Activity Feed API Views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import User
from .social_models import PointsHistory

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_feed(request, user_id):
    """Get comprehensive user activity feed with filtering options"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Only allow users to see their own activity or make it public
        if request.user != user and not getattr(user, 'profile_is_public', True):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get query parameters
        limit = int(request.GET.get('limit', 50))
        category = request.GET.get('category', 'all')
        time_range = request.GET.get('time_range', 'all')
        search = request.GET.get('search', '')
        
        # Base queryset
        activities = PointsHistory.objects.filter(user=user)
        
        # Apply category filter
        if category != 'all':
            category_mapping = {
                'milestone': ['first_', 'milestone_', 'login_streak_', 'early_adopter', 'platform_anniversary'],
                'content': ['post_', 'story_', 'comment_', 'quality_content'],
                'social': ['follow_', 'like_', 'share_', 'message_', 'profile_', 'login', 'signup_', 'email_', 'phone_'],
                'startup': ['startup_'],
                'job': ['job_', 'resume_']
            }
            
            if category in category_mapping:
                q_objects = Q()
                for prefix in category_mapping[category]:
                    q_objects |= Q(reason__startswith=prefix)
                activities = activities.filter(q_objects)
        
        # Apply time range filter
        if time_range != 'all':
            now = timezone.now()
            if time_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == 'week':
                start_date = now - timedelta(days=7)
            elif time_range == 'month':
                start_date = now - timedelta(days=30)
            else:
                start_date = None
            
            if start_date:
                activities = activities.filter(created_at__gte=start_date)
        
        # Apply search filter
        if search:
            activities = activities.filter(
                Q(description__icontains=search) | 
                Q(reason__icontains=search)
            )
        
        # Order and limit
        activities = activities.order_by('-created_at')[:limit]
        
        # Prepare response data
        data = []
        for entry in activities:
            data.append({
                'id': entry.id,
                'points': entry.points,
                'reason': entry.reason,
                'reason_display': entry.get_reason_display(),
                'description': entry.description,
                'created_at': entry.created_at,
                'achievement_id': entry.achievement.id if entry.achievement else None,
                'achievement_name': entry.achievement.name if entry.achievement else None,
            })
        
        # Get activity statistics
        total_activities = PointsHistory.objects.filter(user=user).count()
        total_points_earned = PointsHistory.objects.filter(
            user=user, 
            points__gt=0
        ).aggregate(total=Sum('points'))['total'] or 0
        
        # Get category breakdown
        category_stats = {}
        for category_name, prefixes in {
            'milestone': ['first_', 'milestone_', 'login_streak_'],
            'content': ['post_', 'story_', 'comment_'],
            'social': ['follow_', 'like_', 'share_', 'message_', 'profile_', 'login'],
            'startup': ['startup_'],
            'job': ['job_', 'resume_']
        }.items():
            q_objects = Q()
            for prefix in prefixes:
                q_objects |= Q(reason__startswith=prefix)
            
            stats = PointsHistory.objects.filter(user=user).filter(q_objects).aggregate(
                count=Count('id'),
                points=Sum('points')
            )
            category_stats[category_name] = {
                'count': stats['count'] or 0,
                'points': stats['points'] or 0
            }
        
        return Response({
            'results': data,
            'count': len(data),
            'total_activities': total_activities,
            'total_points_earned': total_points_earned,
            'category_stats': category_stats,
            'filters': {
                'category': category,
                'time_range': time_range,
                'search': search
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )