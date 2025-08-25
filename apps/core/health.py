# Health check views for production monitoring

from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
from django.conf import settings
import redis
import time
import sys
import os


def health_check(request):
    """Basic health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'environment': getattr(settings, 'ENVIRONMENT', 'unknown')
    })


def detailed_health_check(request):
    """Detailed health check with service status"""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'redis': check_redis(),
        'celery': check_celery(),
        'storage': check_storage(),
    }
    
    # Determine overall health
    overall_status = 'healthy' if all(check['status'] == 'healthy' for check in checks.values()) else 'unhealthy'
    
    return JsonResponse({
        'status': overall_status,
        'timestamp': time.time(),
        'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
        'checks': checks,
        'version': get_version_info()
    })


def check_database():
    """Check database connectivity"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return {'status': 'healthy', 'message': 'Database connection successful'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}


def check_cache():
    """Check cache connectivity"""
    try:
        cache.set('health_check', 'test', 30)
        result = cache.get('health_check')
        if result == 'test':
            return {'status': 'healthy', 'message': 'Cache working properly'}
        else:
            return {'status': 'unhealthy', 'message': 'Cache not working properly'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Cache error: {str(e)}'}


def check_redis():
    """Check Redis connectivity"""
    try:
        if hasattr(settings, 'CHANNEL_LAYERS'):
            redis_url = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
            if isinstance(redis_url, str):
                r = redis.from_url(redis_url)
            else:
                r = redis.Redis(host=redis_url[0], port=redis_url[1])
            
            r.ping()
            return {'status': 'healthy', 'message': 'Redis connection successful'}
        else:
            return {'status': 'skipped', 'message': 'Redis not configured'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Redis error: {str(e)}'}


def check_celery():
    """Check Celery worker status"""
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            active_workers = len(stats)
            return {'status': 'healthy', 'message': f'{active_workers} active workers'}
        else:
            return {'status': 'unhealthy', 'message': 'No active Celery workers'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Celery error: {str(e)}'}


def check_storage():
    """Check file storage connectivity"""
    try:
        from django.core.files.storage import default_storage
        
        # Test file operations
        test_file = 'health_check_test.txt'
        content = b'health check test'
        
        # Save test file
        default_storage.save(test_file, content)
        
        # Check if file exists
        if default_storage.exists(test_file):
            # Clean up
            default_storage.delete(test_file)
            return {'status': 'healthy', 'message': 'Storage working properly'}
        else:
            return {'status': 'unhealthy', 'message': 'Storage file operations failed'}
            
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Storage error: {str(e)}'}


def get_version_info():
    """Get version and system information"""
    return {
        'python_version': sys.version,
        'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'unknown',
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
    }


def readiness_check(request):
    """Readiness check for deployment"""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
    }
    
    # Check if all critical services are ready
    ready = all(check['status'] == 'healthy' for check in checks.values())
    
    status_code = 200 if ready else 503
    
    return JsonResponse({
        'status': 'ready' if ready else 'not_ready',
        'timestamp': time.time(),
        'checks': checks
    }, status=status_code)


def liveness_check(request):
    """Liveness check for deployment"""
    # Basic liveness check - just return 200 if the application is running
    return JsonResponse({
        'status': 'alive',
        'timestamp': time.time()
    })