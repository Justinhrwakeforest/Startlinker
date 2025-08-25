from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from startup_hub.monitoring import health_checker, metrics_collector
import json


def health_check(request):
    """Simple health check endpoint"""
    # Record metric for health check requests
    metrics_collector.increment_counter('health_check_requests')
    
    return JsonResponse({
        'status': 'healthy',
        'message': 'StartupHub is running',
        'timestamp': timezone.now().isoformat()
    })


@csrf_exempt  
@require_http_methods(["GET"])
def detailed_health_check(request):
    """Detailed health check with system status"""
    try:
        # Use the comprehensive health checker
        health_results = health_checker.run_all_checks()
        
        # Record metrics
        metrics_collector.increment_counter('detailed_health_check_requests')
        metrics_collector.record_metric('health_check_status', 1 if health_results['overall_status'] == 'healthy' else 0)
        
        status_code = 200
        if health_results['overall_status'] == 'unhealthy':
            status_code = 503
        elif health_results['overall_status'] == 'warning':
            status_code = 200  # Still OK but with warnings
        
        return JsonResponse({
            'status': health_results['overall_status'],
            'checks': health_results['checks'],
            'timestamp': timezone.now().isoformat()
        }, status=status_code)
        
    except Exception as e:
        metrics_collector.increment_counter('health_check_errors')
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def metrics_endpoint(request):
    """Expose metrics for monitoring systems"""
    try:
        # This would typically integrate with Prometheus or similar
        # For now, return basic application metrics
        from django.core.cache import cache
        
        # Get some basic metrics from cache
        metrics = {
            'health_check_requests': cache.get('counter:health_check_requests', 0),
            'detailed_health_check_requests': cache.get('counter:detailed_health_check_requests', 0),
            'health_check_errors': cache.get('counter:health_check_errors', 0),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(metrics)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)