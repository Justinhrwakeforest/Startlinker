# startup_hub/startup_hub/views.py - Updated with error handlers
from django.http import JsonResponse
from django.shortcuts import render

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def api_stats(request):
    """API statistics endpoint"""
    from apps.startups.models import Startup, Industry
    from apps.jobs.models import Job
    from apps.posts.models import Post
    from apps.users.models import User
    from apps.connect.models import Space, Event
    
    return JsonResponse({
        'status': 'ok',
        'stats': {
            'total_users': User.objects.count(),
            'total_startups': Startup.objects.count(),
            'total_jobs': Job.objects.count(),
            'total_industries': Industry.objects.count(),
            'total_posts': Post.objects.count(),
            'total_spaces': Space.objects.count(),
            'total_events': Event.objects.count(),
        },
        'message': 'StartupHub API is running!',
        'version': 'v1.0'
    })

def custom_404(request, exception=None):
    """Custom 404 error handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Not found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }, status=404)
    
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 error handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }, status=500)
    
    return render(request, '500.html', status=500)