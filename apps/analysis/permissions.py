from rest_framework import permissions


class IsProSubscriber(permissions.BasePermission):
    """
    Allow access to all authenticated users (subscription requirement removed).
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow access to all authenticated users
        return True