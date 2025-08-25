# Custom error handlers for production

import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from startup_hub.monitoring import metrics_collector

logger = logging.getLogger(__name__)


def handler400(request, exception):
    """Handle 400 Bad Request errors"""
    metrics_collector.increment_counter('http_errors', tags={'status_code': '400'})
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server.',
            'status_code': 400
        }, status=400)
    
    return render(request, 'errors/400.html', {'error': exception}, status=400)


def handler403(request, exception):
    """Handle 403 Forbidden errors"""
    metrics_collector.increment_counter('http_errors', tags={'status_code': '403'})
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource.',
            'status_code': 403
        }, status=403)
    
    return render(request, 'errors/403.html', {'error': exception}, status=403)


def handler404(request, exception):
    """Handle 404 Not Found errors"""
    metrics_collector.increment_counter('http_errors', tags={'status_code': '404'})
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Not Found',
            'message': 'The requested resource was not found.',
            'status_code': 404
        }, status=404)
    
    return render(request, 'errors/404.html', {'error': exception}, status=404)


def handler500(request):
    """Handle 500 Internal Server Error"""
    metrics_collector.increment_counter('http_errors', tags={'status_code': '500'})
    
    # Log the error
    logger.error(f'Internal Server Error: {request.path}', exc_info=True)
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Please try again later.',
            'status_code': 500
        }, status=500)
    
    return render(request, 'errors/500.html', status=500)


@csrf_exempt
def handler_csrf_failure(request, reason=""):
    """Handle CSRF token failures"""
    metrics_collector.increment_counter('csrf_failures')
    
    logger.warning(f'CSRF failure: {reason} for {request.path}')
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'CSRF Verification Failed',
            'message': 'CSRF token missing or incorrect.',
            'status_code': 403
        }, status=403)
    
    return render(request, 'errors/csrf_failure.html', {'reason': reason}, status=403)


class ErrorHandlingMiddleware:
    """Middleware to handle uncaught exceptions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f'Uncaught exception in {request.path}: {str(e)}', exc_info=True)
            metrics_collector.increment_counter('uncaught_exceptions')
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Internal Server Error',
                    'message': 'An unexpected error occurred.',
                    'status_code': 500
                }, status=500)
            
            return render(request, 'errors/500.html', status=500)
    
    def process_exception(self, request, exception):
        """Process exceptions that occur during request processing"""
        logger.error(f'Exception in {request.path}: {str(exception)}', exc_info=True)
        metrics_collector.increment_counter('middleware_exceptions')
        
        if settings.DEBUG:
            # Let Django handle it in debug mode
            return None
        
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.',
                'status_code': 500
            }, status=500)
        
        return render(request, 'errors/500.html', status=500)