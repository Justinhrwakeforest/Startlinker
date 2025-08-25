# Additional API views for achievements
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User
from .social_models import UserAchievement, UserPoints

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