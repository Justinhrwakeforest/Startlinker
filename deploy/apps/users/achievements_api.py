# apps/users/achievements_api.py - Dedicated achievements API endpoints
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User
from .social_models import UserPoints, PointsHistory, UserAchievement, Achievement
from .points_service import PointsService

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
                'animation_config': {
                    'type': 'earned',
                    'rarity_level': _get_rarity_level(ua.achievement.rarity),
                    'special_effects': _get_special_effects(ua.achievement.rarity, ua.achievement.category),
                    'unlock_celebration': _get_unlock_celebration_config(ua.achievement.rarity)
                }
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
                'animation_config': {
                    'type': 'available' if can_unlock else 'locked',
                    'rarity_level': _get_rarity_level(achievement.rarity),
                    'special_effects': _get_special_effects(achievement.rarity, achievement.category),
                    'unlock_celebration': _get_unlock_celebration_config(achievement.rarity)
                }
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
    
def _get_rarity_level(rarity):
    """Get numeric rarity level for animation intensity"""
    rarity_levels = {
        'common': 1,
        'uncommon': 2,
        'rare': 3,
        'epic': 4,
        'legendary': 5
    }
    return rarity_levels.get(rarity.lower() if rarity else None, 1)
    
def _get_special_effects(rarity, category):
    """Get special effects configuration based on rarity and category"""
    effects = []
    
    # Rarity-based effects
    if rarity == 'legendary':
        effects.extend(['rainbow_border', 'rotating_aura', 'floating_particles', 'sparkle_trail'])
    elif rarity == 'epic':
        effects.extend(['pulsing_aura', 'floating_particles', 'glow_enhancement'])
    elif rarity == 'rare':
        effects.extend(['shimmer_effect', 'rotation_glow'])
    elif rarity == 'uncommon':
        effects.extend(['gentle_sparkle', 'hover_float'])
    else:  # common
        effects.extend(['simple_glow'])
    
    # Category-based effects
    category_effects = {
        'profile': ['personal_glow'],
        'social': ['network_pulse', 'connection_ripple'],
        'content': ['creative_sparkle', 'inspiration_burst'],
        'startup': ['innovation_energy', 'rocket_trail'],
        'jobs': ['professional_steady', 'career_glow'],
        'special': ['magical_swirl', 'unique_signature']
    }
    
    if category and category.lower() in category_effects:
        effects.extend(category_effects[category.lower()])
    
    return effects
    
def _get_unlock_celebration_config(rarity):
    """Get unlock celebration configuration based on rarity"""
    celebrations = {
        'common': {
            'duration': 1000,
            'particles': ['⭐'],
            'particle_count': 3,
            'sound': 'unlock_common',
            'screen_shake': False,
            'fireworks': False
        },
        'uncommon': {
            'duration': 1200,
            'particles': ['⭐', '✨'],
            'particle_count': 5,
            'sound': 'unlock_uncommon',
            'screen_shake': False,
            'fireworks': False
        },
        'rare': {
            'duration': 1500,
            'particles': ['⭐', '✨', '💫'],
            'particle_count': 8,
            'sound': 'unlock_rare',
            'screen_shake': True,
            'fireworks': False
        },
        'epic': {
            'duration': 2000,
            'particles': ['⭐', '✨', '💫', '🌟'],
            'particle_count': 12,
            'sound': 'unlock_epic',
            'screen_shake': True,
            'fireworks': True
        },
        'legendary': {
            'duration': 2500,
            'particles': ['⭐', '✨', '💫', '🌟', '🎊', '🎉'],
            'particle_count': 20,
            'sound': 'unlock_legendary',
            'screen_shake': True,
            'fireworks': True,
            'rainbow_flash': True,
            'confetti': True
        }
    }
    
    return celebrations.get(rarity.lower() if rarity else None, celebrations['common'])