"""
Comprehensive Error Tracking and Logging System for StartupHub Production
Implements advanced error handling, logging, and monitoring with Sentry integration.
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import mail_admins
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from functools import wraps
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger('startup_hub.errors')

class ErrorTracker:
    """
    Advanced error tracking and reporting system.
    """
    
    def __init__(self):
        self.error_cache_prefix = 'error_tracking:'
        self.error_threshold = 5  # Number of errors before alerting
        self.time_window = 300    # 5 minutes window
    
    def setup_sentry(self):
        """Configure Sentry for error tracking."""
        sentry_dsn = os.environ.get('SENTRY_DSN')
        
        if sentry_dsn:
            sentry_logging = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    DjangoIntegration(auto_enabling=True),
                    CeleryIntegration(auto_enabling=True),
                    RedisIntegration(),
                    sentry_logging,
                ],
                traces_sample_rate=0.1,  # 10% of transactions
                send_default_pii=False,  # Don't send personally identifiable information
                environment=os.environ.get('DJANGO_ENVIRONMENT', 'production'),
                release=os.environ.get('APP_VERSION', 'unknown'),
                before_send=self.filter_sensitive_data,
                before_send_transaction=self.filter_sensitive_transactions,
            )
            
            logger.info("Sentry error tracking initialized")
        else:
            logger.warning("Sentry DSN not provided, error tracking disabled")
    
    def filter_sensitive_data(self, event, hint):
        """Filter sensitive data from Sentry events."""
        # Remove sensitive keys
        sensitive_keys = ['password', 'token', 'secret', 'key', 'auth']
        
        def clean_dict(data):
            if isinstance(data, dict):
                return {
                    k: '[REDACTED]' if any(sensitive in k.lower() for sensitive in sensitive_keys) 
                    or (isinstance(v, str) and len(v) > 100)  # Redact long strings
                    else clean_dict(v) if isinstance(v, (dict, list)) else v
                    for k, v in data.items()
                }
            elif isinstance(data, list):
                return [clean_dict(item) for item in data]
            return data
        
        # Clean request data
        if 'request' in event:
            event['request'] = clean_dict(event['request'])
        
        # Clean extra data
        if 'extra' in event:
            event['extra'] = clean_dict(event['extra'])
        
        return event
    
    def filter_sensitive_transactions(self, event, hint):
        """Filter sensitive transactions from Sentry."""
        # Don't track health check transactions
        if event.get('transaction') in ['/health/', '/ping/', '/status/']:
            return None
        
        return event
    
    def track_error(self, error, context=None, user=None, extra_data=None):
        """Track an error with context information."""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': timezone.now().isoformat(),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'user_id': getattr(user, 'id', None) if user else None,
            'extra_data': extra_data or {}
        }
        
        # Store in cache for immediate access
        cache_key = f"{self.error_cache_prefix}{error_data['error_type']}:{timezone.now().strftime('%Y%m%d%H%M')}"
        error_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, error_count, self.time_window)
        
        # Log the error
        logger.error(
            f"Error tracked: {error_data['error_type']} - {error_data['error_message']}",
            extra={
                'error_data': error_data,
                'error_count': error_count
            }
        )
        
        # Alert if error threshold exceeded
        if error_count >= self.error_threshold:
            self.send_error_alert(error_data, error_count)
        
        # Send to Sentry if configured
        with sentry_sdk.push_scope() as scope:
            if user:
                scope.user = {
                    'id': getattr(user, 'id', None),
                    'username': getattr(user, 'username', None),
                    'email': getattr(user, 'email', None)
                }
            
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            if extra_data:
                for key, value in extra_data.items():
                    scope.set_extra(key, value)
            
            sentry_sdk.capture_exception(error)
        
        return error_data
    
    def send_error_alert(self, error_data, error_count):
        """Send alert when error threshold is exceeded."""
        subject = f"High Error Rate Alert - {error_data['error_type']}"
        message = f"""
        High error rate detected for {error_data['error_type']}
        
        Error Count: {error_count} in {self.time_window // 60} minutes
        Error Message: {error_data['error_message']}
        Timestamp: {error_data['timestamp']}
        
        Context: {json.dumps(error_data['context'], indent=2)}
        
        Please investigate immediately.
        """
        
        try:
            mail_admins(subject, message, fail_silently=False)
            logger.critical(f"Error alert sent for {error_data['error_type']}")
        except Exception as e:
            logger.error(f"Failed to send error alert: {str(e)}")
    
    def get_error_statistics(self, hours=24):
        """Get error statistics for the specified time period."""
        try:
            from django.db import connections
            
            # This would require a custom error log table
            # For now, return cache-based statistics
            stats = {
                'total_errors': 0,
                'error_types': {},
                'hourly_breakdown': {},
                'top_errors': []
            }
            
            # Get errors from cache (limited view)
            cache_pattern = f"{self.error_cache_prefix}*"
            
            # Note: This is a simplified version
            # In production, you'd want to store errors in a database
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get error statistics: {str(e)}")
            return {}

def error_handler(error_type=None, notify_admins=True, track_in_sentry=True):
    """
    Decorator for handling and tracking errors in views and functions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Determine if this is a Django view
                request = None
                if args and hasattr(args[0], 'META'):
                    request = args[0]
                
                context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
                
                if request:
                    context.update({
                        'path': request.path,
                        'method': request.method,
                        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                        'ip_address': request.META.get('REMOTE_ADDR', 'unknown')
                    })
                
                # Track the error
                error_tracker = ErrorTracker()
                user = getattr(request, 'user', None) if request else None
                error_data = error_tracker.track_error(
                    e, 
                    context=context, 
                    user=user,
                    extra_data={'function_name': func.__name__}
                )
                
                # Return appropriate response based on context
                if request and request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Internal server error',
                        'error_id': error_data.get('timestamp'),
                        'message': 'An error occurred while processing your request'
                    }, status=500)
                elif request:
                    # For web requests, let Django handle it normally
                    raise
                else:
                    # For non-web functions, re-raise
                    raise
                    
        return wrapper
    return decorator

class CustomErrorHandler:
    """
    Custom error handling for different types of errors.
    """
    
    def __init__(self):
        self.error_tracker = ErrorTracker()
    
    def handle_404(self, request, exception):
        """Handle 404 errors."""
        logger.warning(f"404 error: {request.path} from IP {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        # Track 404s to identify broken links
        cache_key = f"404_tracking:{request.path}"
        count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, count, 3600)  # 1 hour
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'error': 'Not found',
                'message': 'The requested resource was not found'
            }, status=404)
        
        # Let Django handle HTML responses
        return None
    
    def handle_500(self, request):
        """Handle 500 errors."""
        logger.error(f"500 error on {request.path} from IP {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'error': 'Internal server error',
                'message': 'An internal server error occurred'
            }, status=500)
        
        return None
    
    def handle_403(self, request, exception):
        """Handle 403 errors."""
        logger.warning(f"403 error: {request.path} from IP {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource'
            }, status=403)
        
        return None

class LoggingConfiguration:
    """
    Advanced logging configuration for production.
    """
    
    @staticmethod
    def get_production_logging_config():
        """Get comprehensive logging configuration for production."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                    'style': '{',
                },
                'json': {
                    'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
                },
                'simple': {
                    'format': '{levelname} {message}',
                    'style': '{',
                },
            },
            'filters': {
                'require_debug_false': {
                    '()': 'django.utils.log.RequireDebugFalse',
                },
                'require_debug_true': {
                    '()': 'django.utils.log.RequireDebugTrue',
                },
            },
            'handlers': {
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
                'file': {
                    'level': 'INFO',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': '/var/log/startup_hub/app.log',
                    'maxBytes': 1024*1024*10,  # 10MB
                    'backupCount': 5,
                    'formatter': 'verbose',
                },
                'error_file': {
                    'level': 'ERROR',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': '/var/log/startup_hub/errors.log',
                    'maxBytes': 1024*1024*10,  # 10MB
                    'backupCount': 10,
                    'formatter': 'json',
                },
                'security_file': {
                    'level': 'WARNING',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': '/var/log/startup_hub/security.log',
                    'maxBytes': 1024*1024*5,  # 5MB
                    'backupCount': 10,
                    'formatter': 'json',
                },
                'mail_admins': {
                    'level': 'ERROR',
                    'filters': ['require_debug_false'],
                    'class': 'django.utils.log.AdminEmailHandler',
                    'formatter': 'verbose',
                },
                'sentry': {
                    'level': 'ERROR',
                    'class': 'sentry_sdk.integrations.logging.SentryHandler',
                },
            },
            'loggers': {
                'startup_hub': {
                    'handlers': ['console', 'file', 'error_file', 'sentry'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'startup_hub.security': {
                    'handlers': ['security_file', 'mail_admins'],
                    'level': 'WARNING',
                    'propagate': False,
                },
                'startup_hub.errors': {
                    'handlers': ['error_file', 'mail_admins', 'sentry'],
                    'level': 'ERROR',
                    'propagate': False,
                },
                'django': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': True,
                },
                'django.request': {
                    'handlers': ['error_file', 'mail_admins'],
                    'level': 'ERROR',
                    'propagate': False,
                },
                'django.security': {
                    'handlers': ['security_file', 'mail_admins'],
                    'level': 'WARNING',
                    'propagate': False,
                },
                'celery': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': True,
                },
                'celery.task': {
                    'handlers': ['file', 'error_file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'root': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        }

class StructuredLogger:
    """
    Structured logging utilities for better log analysis.
    """
    
    def __init__(self, logger_name):
        self.logger = logging.getLogger(logger_name)
    
    def log_structured(self, level, message, **kwargs):
        """Log structured data."""
        extra_data = {
            'timestamp': timezone.now().isoformat(),
            'structured_data': kwargs
        }
        
        self.logger.log(level, message, extra=extra_data)
    
    def log_user_action(self, user, action, resource=None, **kwargs):
        """Log user actions for audit trail."""
        self.log_structured(
            logging.INFO,
            f"User action: {action}",
            user_id=getattr(user, 'id', None),
            username=getattr(user, 'username', None),
            action=action,
            resource=resource,
            **kwargs
        )
    
    def log_api_request(self, request, response_time, status_code):
        """Log API requests for monitoring."""
        self.log_structured(
            logging.INFO,
            f"API request: {request.method} {request.path}",
            method=request.method,
            path=request.path,
            status_code=status_code,
            response_time=response_time,
            user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'unknown')
        )
    
    def log_security_event(self, event_type, severity, details):
        """Log security events."""
        self.log_structured(
            logging.WARNING if severity == 'medium' else logging.ERROR,
            f"Security event: {event_type}",
            event_type=event_type,
            severity=severity,
            details=details
        )

# Global error tracker instance
error_tracker = ErrorTracker()

# Custom error handler instance
custom_error_handler = CustomErrorHandler()

# Initialize structured loggers
app_logger = StructuredLogger('startup_hub')
security_logger = StructuredLogger('startup_hub.security')
error_logger = StructuredLogger('startup_hub.errors')

def setup_error_tracking():
    """Setup error tracking and logging."""
    try:
        # Initialize Sentry
        error_tracker.setup_sentry()
        
        # Create log directories
        log_dir = '/var/log/startup_hub'
        os.makedirs(log_dir, exist_ok=True)
        
        logger.info("Error tracking and logging setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup error tracking: {str(e)}")

# Error reporting endpoint for frontend
@csrf_exempt
def report_frontend_error(request):
    """Endpoint for frontend error reporting."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        error_data = {
            'message': data.get('message', 'Unknown error'),
            'stack': data.get('stack', ''),
            'url': data.get('url', ''),
            'line': data.get('line', 0),
            'column': data.get('column', 0),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
            'timestamp': timezone.now().isoformat()
        }
        
        # Log frontend error
        app_logger.log_structured(
            logging.ERROR,
            f"Frontend error: {error_data['message']}",
            **error_data
        )
        
        # Send to Sentry
        with sentry_sdk.push_scope() as scope:
            scope.set_context('frontend_error', error_data)
            sentry_sdk.capture_message(
                f"Frontend Error: {error_data['message']}", 
                level='error'
            )
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Failed to process frontend error report: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)