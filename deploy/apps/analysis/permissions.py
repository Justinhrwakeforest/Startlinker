from rest_framework import permissions


class IsProSubscriber(permissions.BasePermission):
    """
    Allows access only to users with active Pro subscription.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has an active Pro subscription
        return hasattr(request.user, 'subscription') and request.user.subscription.is_active_pro