# apps/users/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import User, validate_username
from .social_models import UserPoints, PointsHistory, UserAchievement, Achievement
from .points_service import PointsService
import json

@api_view(['GET'])
@permission_classes([AllowAny])
def check_username_availability(request):
    """
    Check if a username is available and valid
    GET /api/users/check-username/?username=desired_name
    """
    username = request.GET.get('username', '').strip()
    
    if not username:
        return Response({
            'available': False,
            'valid': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check validation first
    try:
        validate_username(username)
        is_valid = True
        validation_message = None
    except ValidationError as e:
        is_valid = False
        validation_message = str(e)
    
    # Check availability if valid
    is_available = False
    suggestions = []
    
    if is_valid:
        # Check if username exists, but exclude current user if authenticated
        query = User.objects.filter(username=username)
        if request.user.is_authenticated:
            query = query.exclude(id=request.user.id)
        
        is_available = not query.exists()
        
        # If not available, generate suggestions
        if not is_available:
            suggestions = User.generate_username_suggestions(username)
    
    response_data = {
        'username': username,
        'available': is_available,
        'valid': is_valid,
        'message': validation_message if not is_valid else (
            'Username is available!' if is_available else 'Username is already taken'
        )
    }
    
    # Add suggestions if username is taken
    if is_valid and not is_available:
        response_data['suggestions'] = suggestions
    
    return Response(response_data)

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_username_format(request):
    """
    Validate username format without checking availability
    POST /api/users/validate-username/ 
    Body: {"username": "test_user"}
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.data
    
    username = data.get('username', '').strip()
    
    if not username:
        return Response({
            'valid': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        validate_username(username)
        return Response({
            'username': username,
            'valid': True,
            'message': 'Username format is valid'
        })
    except ValidationError as e:
        return Response({
            'username': username,
            'valid': False,
            'message': str(e)
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_username_suggestions(request):
    """
    Get username suggestions based on a base name
    GET /api/users/username-suggestions/?base=john
    """
    base_username = request.GET.get('base', '').strip()
    max_suggestions = min(int(request.GET.get('max', 5)), 10)  # Limit to 10 max
    
    if not base_username:
        return Response({
            'suggestions': [],
            'message': 'Base username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    suggestions = User.generate_username_suggestions(base_username, max_suggestions)
    
    return Response({
        'base': base_username,
        'suggestions': suggestions,
        'count': len(suggestions)
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_username_from_name(request):
    """
    Auto-generate username suggestions from full name or email
    POST /api/users/generate-username/
    Body: {"name": "John Doe"} or {"email": "john.doe@example.com"}
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.data
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    
    if not name and not email:
        return Response({
            'suggestions': [],
            'message': 'Name or email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Extract base username from name or email
    if name:
        # Convert "John Doe" to "john_doe", "johndoe", etc.
        base_parts = name.lower().split()
        base_options = [
            ''.join(base_parts),  # johndoe
            '_'.join(base_parts),  # john_doe
            '.'.join(base_parts),  # john.doe
            base_parts[0] if base_parts else 'user',  # john
        ]
    elif email:
        # Extract username from email
        email_username = email.split('@')[0]
        base_options = [email_username, email_username.replace('.', '_')]
    
    all_suggestions = []
    for base in base_options[:2]:  # Limit to first 2 base options
        suggestions = User.generate_username_suggestions(base, 3)
        all_suggestions.extend(suggestions)
        if len(all_suggestions) >= 5:
            break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for suggestion in all_suggestions:
        if suggestion not in seen:
            seen.add(suggestion)
            unique_suggestions.append(suggestion)
            if len(unique_suggestions) >= 5:
                break
    
    return Response({
        'input': name or email,
        'suggestions': unique_suggestions,
        'count': len(unique_suggestions)
    })

# Points and Achievements API endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_points_detail(request, user_id):
    """Get user's points and level information"""
    try:
        user = get_object_or_404(User, id=user_id)
        user_points = UserPoints.get_or_create_for_user(user)
        
        data = {
            'user_id': user.id,
            'username': user.username,
            'total_points': user_points.total_points,
            'lifetime_points': user_points.lifetime_points,
            'points_this_month': user_points.points_this_month,
            'points_this_week': user_points.points_this_week,
            'achievement_points': user_points.achievement_points,
            'content_points': user_points.content_points,
            'social_points': user_points.social_points,
            'startup_points': user_points.startup_points,
            'job_points': user_points.job_points,
            'level': user_points.level,
            'level_progress': user_points.level_progress,
            'last_updated': user_points.last_updated,
            'rank': PointsService.get_user_rank(user),
        }
        
        return Response(data)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                from django.db.models import Q
                q_objects = Q()
                for prefix in category_mapping[category]:
                    q_objects |= Q(reason__startswith=prefix)
                activities = activities.filter(q_objects)
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            
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
            from django.db.models import Q
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
        from django.db.models import Count, Sum
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
            from django.db.models import Q
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_points_history(request, user_id):
    """Get user's points transaction history"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Only allow users to see their own history or make it public
        if request.user != user and not getattr(user, 'profile_is_public', True):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        limit = int(request.GET.get('limit', 20))
        history = PointsHistory.objects.filter(user=user)[:limit]
        
        data = []
        for entry in history:
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
        
        return Response({'results': data})
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                from django.db.models import Q
                q_objects = Q()
                for prefix in category_mapping[category]:
                    q_objects |= Q(reason__startswith=prefix)
                activities = activities.filter(q_objects)
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            
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
            from django.db.models import Q
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
        from django.db.models import Count, Sum
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
            from django.db.models import Q
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_summary(request, user_id):
    """Get comprehensive user stats summary for profile"""
    try:
        user = get_object_or_404(User, id=user_id)
        user_points = UserPoints.get_or_create_for_user(user)
        
        # Count various activities
        from apps.posts.models import Post
        from apps.startups.models import Startup
        from apps.jobs.models import Job
        from .social_models import UserFollow, Story, UserAchievement
        
        achievement_count = UserAchievement.objects.filter(user=user).count()
        posts_count = Post.objects.filter(author=user, is_approved=True).count()
        stories_count = Story.objects.filter(author=user).count()
        followers_count = UserFollow.objects.filter(following=user).count()
        following_count = UserFollow.objects.filter(follower=user).count()
        startups_claimed = Startup.objects.filter(claimed_by=user, claim_verified=True).count()
        startups_submitted = Startup.objects.filter(submitted_by=user, is_approved=True).count()
        
        try:
            jobs_posted = Job.objects.filter(posted_by=user).count()
        except:
            jobs_posted = 0
        
        # Get recent achievements
        recent_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')[:6]
        achievements_data = []
        for ua in recent_achievements:
            achievements_data.append({
                'id': ua.id,
                'achievement_id': ua.achievement.id,
                'achievement_name': ua.achievement.name,
                'achievement_description': ua.achievement.description,
                'achievement_icon': ua.achievement.icon,
                'achievement_rarity': ua.achievement.rarity,
                'achievement_points': ua.achievement.points,
                'earned_at': ua.earned_at,
            })
        
        data = {
            'user_id': user.id,
            'username': user.username,
            'points': {
                'total_points': user_points.total_points,
                'level': user_points.level,
                'level_progress': user_points.level_progress,
                'rank': PointsService.get_user_rank(user),
                'points_this_month': user_points.points_this_month,
                'achievement_points': user_points.achievement_points,
                'content_points': user_points.content_points,
                'social_points': user_points.social_points,
                'startup_points': user_points.startup_points,
                'job_points': user_points.job_points,
            },
            'activity_counts': {
                'achievements': achievement_count,
                'posts': posts_count,
                'stories': stories_count,
                'followers': followers_count,
                'following': following_count,
                'startups_claimed': startups_claimed,
                'startups_submitted': startups_submitted,
                'jobs_posted': jobs_posted,
            },
            'recent_achievements': achievements_data,
        }
        
        return Response(data)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                from django.db.models import Q
                q_objects = Q()
                for prefix in category_mapping[category]:
                    q_objects |= Q(reason__startswith=prefix)
                activities = activities.filter(q_objects)
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            
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
            from django.db.models import Q
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
        from django.db.models import Count, Sum
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
            from django.db.models import Q
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_list(request, user_id):
    """Get user's achievements list"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get user achievements
        user_achievements = UserAchievement.objects.filter(
            user=user,
            is_public=True
        ).select_related('achievement').order_by('-earned_at')
        
        limit = int(request.GET.get('limit', 50))
        user_achievements = user_achievements[:limit]
        
        data = []
        for ua in user_achievements:
            data.append({
                'id': ua.id,
                'achievement_id': ua.achievement.id,
                'achievement_name': ua.achievement.name,
                'achievement_description': ua.achievement.description,
                'achievement_icon': ua.achievement.icon,
                'achievement_rarity': ua.achievement.rarity,
                'achievement_category': ua.achievement.category,
                'achievement_points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        return Response({'results': data, 'count': len(data)})
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                from django.db.models import Q
                q_objects = Q()
                for prefix in category_mapping[category]:
                    q_objects |= Q(reason__startswith=prefix)
                activities = activities.filter(q_objects)
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            
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
            from django.db.models import Q
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
        from django.db.models import Count, Sum
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
            from django.db.models import Q
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def achievements_leaderboard(request):
    """Get achievements leaderboard"""
    try:
        # Get top users by points
        limit = int(request.GET.get('limit', 50))
        top_users = UserPoints.objects.select_related('user').order_by('-total_points')[:limit]
        
        leaderboard_data = []
        for rank, user_points in enumerate(top_users, 1):
            user = user_points.user
            achievements_count = UserAchievement.objects.filter(user=user).count()
            
            leaderboard_data.append({
                'rank': rank,
                'user_id': user.id,
                'username': user.username,
                'display_name': user.first_name + ' ' + user.last_name if user.first_name and user.last_name else user.username,
                'avatar_url': getattr(user, 'avatar_url', None),
                'total_points': user_points.total_points,
                'level': user_points.level,
                'level_progress': user_points.level_progress,
                'achievements_count': achievements_count,
                'points_this_month': user_points.points_this_month,
            })
        
        return Response({
            'results': leaderboard_data,
            'count': len(leaderboard_data)
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                from django.db.models import Q
                q_objects = Q()
                for prefix in category_mapping[category]:
                    q_objects |= Q(reason__startswith=prefix)
                activities = activities.filter(q_objects)
        
        # Apply time range filter
        if time_range != 'all':
            from django.utils import timezone
            from datetime import timedelta
            
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
            from django.db.models import Q
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
        from django.db.models import Count, Sum
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
            from django.db.models import Q
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements_summary(request, user_id):
    """Get comprehensive achievements summary with earned, available, and locked counts"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)
        total_achievements = all_achievements.count()
        
        # Get user's earned achievements
        earned_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        earned_count = len(earned_achievements)
        
        # Get earned achievements details
        earned_achievements_details = []
        user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
        
        for ua in user_achievements:
            earned_achievements_details.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'color': ua.achievement.color,
                'rarity': ua.achievement.rarity,
                'category': ua.achievement.category,
                'points': ua.achievement.points,
                'earned_at': ua.earned_at,
                'is_pinned': ua.is_pinned,
                'progress_data': ua.progress_data,
            })
        
        # Calculate available (can be unlocked) vs locked achievements
        available_achievements = []
        locked_achievements = []
        
        # Import here to avoid circular imports
        from .achievement_tracker import AchievementTracker
        
        for achievement in all_achievements.exclude(id__in=earned_achievements):
            # Check if user can unlock this achievement
            can_unlock = AchievementTracker._check_achievement_requirements(user, achievement)
            
            achievement_data = {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'rarity': achievement.rarity,
                'category': achievement.category,
                'points': achievement.points,
                'requirements': achievement.requirements,
                'is_secret': achievement.is_secret,
            }
            
            if can_unlock:
                available_achievements.append(achievement_data)
            else:
                locked_achievements.append(achievement_data)
        
        available_count = len(available_achievements)
        locked_count = len(locked_achievements)
        
        # Get achievement stats by category
        category_stats = {}
        for category in ['profile', 'content', 'social', 'startup', 'jobs', 'special']:
            category_achievements = all_achievements.filter(category=category)
            category_earned = UserAchievement.objects.filter(
                user=user,
                achievement__category=category
            ).count()
            
            category_stats[category] = {
                'total': category_achievements.count(),
                'earned': category_earned,
                'percentage': round((category_earned / category_achievements.count() * 100) if category_achievements.count() > 0 else 0, 1)
            }
        
        # Calculate overall completion percentage
        completion_percentage = round((earned_count / total_achievements * 100) if total_achievements > 0 else 0, 1)
        
        # Get recent achievements (last 6)
        recent_achievements = earned_achievements_details[:6]
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'summary': {
                'total_achievements': total_achievements,
                'earned': earned_count,
                'available': available_count,
                'locked': locked_count,
                'completion_percentage': completion_percentage,
            },
            'earned_achievements': earned_achievements_details,
            'available_achievements': available_achievements,
            'locked_achievements': locked_achievements,
            'recent_achievements': recent_achievements,
            'category_stats': category_stats,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in user_achievements_summary: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )