"""
Minimal Django Backend Fix for EC2
Add this to the existing 'working_api' backend on EC2 to fix the /api/auth/user/ endpoint
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_http_methods(["GET"])
def get_current_user(request):
    """
    GET /api/auth/user/
    Return current authenticated user data
    """
    # Check for authentication token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Token '):
        return JsonResponse(
            {'detail': 'Authentication credentials were not provided.'}, 
            status=401
        )
    
    # For now, return a basic user response
    # In production, you'd validate the token and return actual user data
    token = auth_header.replace('Token ', '')
    
    # Basic user data structure
    user_data = {
        'id': 1,
        'username': 'demo_user',
        'email': 'demo@startlinker.com',
        'first_name': 'Demo',
        'last_name': 'User',
        'is_premium': False,
        'profile_picture': None
    }
    
    return JsonResponse(user_data)

# Add this URL pattern to your existing URLconf:
# path('api/auth/user/', get_current_user, name='current-user'),