# startup_hub/apps/connect/middleware.py
from django.utils import timezone
from django.core.cache import cache

class UpdateLastSeenMiddleware:
    """Middleware to update user's last seen timestamp"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Update last seen for authenticated users
        if request.user.is_authenticated:
            # Use cache to avoid too many DB updates
            cache_key = f'last_seen_{request.user.id}'
            last_update = cache.get(cache_key)
            
            # Update every 5 minutes
            if not last_update or (timezone.now() - last_update).seconds > 300:
                try:
                    profile = request.user.connect_profile
                    profile.update_last_seen()
                    cache.set(cache_key, timezone.now(), 300)
                except:
                    # Create profile if it doesn't exist
                    from .models import UserProfile
                    UserProfile.objects.get_or_create(user=request.user)
        
        response = self.get_response(request)
        return response