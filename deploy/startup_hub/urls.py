# startup_hub/startup_hub/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from apps.core.health import health_check, detailed_health_check, readiness_check, liveness_check
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

def api_stats(request):
    from apps.startups.models import Startup
    from apps.jobs.models import Job
    from apps.startups.models import Industry
    from apps.users.models import User
    from apps.posts.models import Post
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    # Calculate active jobs (not expired)
    # Use application_deadline instead of deadline
    active_jobs = Job.objects.filter(
        Q(application_deadline__gt=datetime.now()) | Q(application_deadline__isnull=True),
        status='active'
    ).count()
    
    # Calculate approved startups
    approved_startups = Startup.objects.filter(
        Q(status='approved') | Q(status='active')
    ).count()
    
    # Calculate recent activity (posts in last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_posts = Post.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Total users (could be used for member count)
    total_users = User.objects.count()
    
    return JsonResponse({
        'total_startups': approved_startups,
        'total_jobs': active_jobs,
        'total_industries': Industry.objects.count(),
        'total_users': total_users,
        'recent_posts': recent_posts,
        'all_startups': Startup.objects.count(),
        'all_jobs': Job.objects.count(),
        'countries_served': 50,  # Static for now, could be calculated from user profiles
        'success_stories': approved_startups // 4,  # Approximate based on approved startups
        'message': 'StartupHub API is running!'
    })

def api_root(request):
    return JsonResponse({'message': 'StartupHub API is running!'})

@csrf_exempt
def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('health/detailed/', detailed_health_check, name='detailed_health_check'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    
    # API endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/startups/', include('apps.startups.urls')),
    path('api/jobs/', include('apps.jobs.urls')),
    path('api/posts/', include('apps.posts.urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/social/', include('apps.users.social_urls')),
    path('api/reports/', include('apps.reports.urls')),
    # path('api/subscriptions/', include('apps.subscriptions.urls')),  # Removed - Stripe functionality
    # path('api/analysis/', include('apps.analysis.urls')),  # Removed - Pitch deck analysis
    path('api/', include('apps.notifications.urls')),
    path('api/stats/', api_stats, name='api_stats'),
    path('api/', api_root, name='api_root'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)