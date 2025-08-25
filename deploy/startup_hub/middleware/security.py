"""
Comprehensive Security Middleware for StartupHub Production
Implements enterprise-level security measures for production deployment.
"""

import json
import time
import hashlib
import logging
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import re

logger = logging.getLogger('startup_hub.security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Enhanced security headers middleware with comprehensive protection.
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://*.amazonaws.com https://avatars.githubusercontent.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' wss: ws: https://api.stripe.com https://checkout.stripe.com; "
            "media-src 'self' blob: https://*.amazonaws.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests;"
        )
        
        # Security headers
        security_headers = {
            'Content-Security-Policy': csp_policy,
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': (
                'camera=(), microphone=(), geolocation=(), '
                'payment=(), usb=(), magnetometer=(), accelerometer=(), '
                'gyroscope=(), notifications=()'
            ),
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'X-Permitted-Cross-Domain-Policies': 'none',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin'
        }
        
        # Apply headers
        for header, value in security_headers.items():
            response[header] = value
            
        # Server header removal
        if 'Server' in response:
            del response['Server']
            
        # Add custom security header
        response['X-Security-Level'] = 'production'
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """
    Advanced rate limiting middleware with multiple strategies.
    """
    
    # Rate limit configurations
    RATE_LIMITS = {
        'api': {'requests': 1000, 'window': 3600},  # 1000 requests per hour for API
        'auth': {'requests': 5, 'window': 300},     # 5 auth attempts per 5 minutes
        'upload': {'requests': 10, 'window': 600},   # 10 uploads per 10 minutes
        'default': {'requests': 100, 'window': 300}, # 100 requests per 5 minutes
    }
    
    def get_client_ip(self, request):
        """Get real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_rate_limit_type(self, request):
        """Determine rate limit type based on request."""
        path = request.path_info
        
        if path.startswith('/api/'):
            if 'auth' in path or 'login' in path or 'register' in path:
                return 'auth'
            elif 'upload' in path or request.method == 'POST':
                return 'upload'
            return 'api'
        return 'default'
    
    def process_request(self, request):
        # Skip rate limiting for health checks and static files
        if request.path_info in ['/health/', '/ping/', '/status/']:
            return None
            
        if request.path_info.startswith('/static/') or request.path_info.startswith('/media/'):
            return None
        
        client_ip = self.get_client_ip(request)
        rate_limit_type = self.get_rate_limit_type(request)
        
        # Get rate limit config
        config = self.RATE_LIMITS.get(rate_limit_type, self.RATE_LIMITS['default'])
        
        # Create cache key
        cache_key = f"rate_limit:{rate_limit_type}:{client_ip}"
        
        # Get current request count
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= config['requests']:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}, type {rate_limit_type}, "
                f"requests: {current_requests}"
            )
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': config['window'],
                'limit': config['requests'],
                'window': config['window']
            }, status=429)
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, config['window'])
        
        return None

class SecurityMonitoringMiddleware(MiddlewareMixin):
    """
    Security monitoring and threat detection middleware.
    """
    
    # Suspicious patterns
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS attempts
        r'union\s+select',            # SQL injection
        r'drop\s+table',              # SQL injection
        r'exec\s*\(',                 # Code execution
        r'eval\s*\(',                 # Code execution
        r'\.\./',                     # Directory traversal
        r'%2e%2e%2f',                 # Encoded directory traversal
        r'javascript:',               # JavaScript injection
        r'vbscript:',                 # VBScript injection
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS]
    
    def detect_suspicious_activity(self, request):
        """Detect suspicious patterns in request data."""
        suspicious_found = []
        
        # Check URL path
        for pattern in self.compiled_patterns:
            if pattern.search(request.path):
                suspicious_found.append(f"URL: {pattern.pattern}")
        
        # Check GET parameters
        for key, value in request.GET.items():
            for pattern in self.compiled_patterns:
                if pattern.search(str(value)):
                    suspicious_found.append(f"GET {key}: {pattern.pattern}")
        
        # Check POST data
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                for pattern in self.compiled_patterns:
                    if pattern.search(str(value)):
                        suspicious_found.append(f"POST {key}: {pattern.pattern}")
        
        # Check headers
        suspicious_headers = ['X-Forwarded-For', 'User-Agent', 'Referer']
        for header in suspicious_headers:
            value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}', '')
            for pattern in self.compiled_patterns:
                if pattern.search(str(value)):
                    suspicious_found.append(f"Header {header}: {pattern.pattern}")
        
        return suspicious_found
    
    def process_request(self, request):
        # Detect suspicious activity
        suspicious_activity = self.detect_suspicious_activity(request)
        
        if suspicious_activity:
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
            
            logger.critical(
                f"Suspicious activity detected from IP {client_ip}: "
                f"{suspicious_activity}, User-Agent: {user_agent}, "
                f"Path: {request.path}, Method: {request.method}"
            )
            
            # Block the request
            return JsonResponse({
                'error': 'Suspicious activity detected',
                'code': 'SECURITY_VIOLATION'
            }, status=403)
        
        return None

class RequestTimingMiddleware(MiddlewareMixin):
    """
    Request timing and performance monitoring middleware.
    """
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Add timing header
            response['X-Response-Time'] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.3f}s, User: {getattr(request, 'user', 'Anonymous')}"
                )
            
            # Store performance metrics
            cache_key = f"perf:avg_response_time"
            current_avg = cache.get(cache_key, 0)
            new_avg = (current_avg + duration) / 2
            cache.set(cache_key, new_avg, 3600)  # Store for 1 hour
        
        return response

class HealthCheckMiddleware(MiddlewareMixin):
    """
    Health check middleware for load balancers and monitoring.
    """
    
    def process_request(self, request):
        if request.path_info == '/health/':
            return self.health_check_response(request)
        elif request.path_info == '/ping/':
            return HttpResponse('pong', content_type='text/plain')
        elif request.path_info == '/status/':
            return self.detailed_status_response(request)
        return None
    
    def health_check_response(self, request):
        """Basic health check response."""
        try:
            # Check database connectivity
            from django.db import connections
            db_conn = connections['default']
            db_conn.cursor()
            
            # Check Redis connectivity
            cache.set('health_check', 'ok', 30)
            cache.get('health_check')
            
            return JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'database': 'ok',
                'cache': 'ok'
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return JsonResponse({
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }, status=503)
    
    def detailed_status_response(self, request):
        """Detailed system status response."""
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application metrics
            avg_response_time = cache.get('perf:avg_response_time', 0)
            
            return JsonResponse({
                'status': 'ok',
                'timestamp': timezone.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': (disk.used / disk.total) * 100,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'application': {
                    'avg_response_time': avg_response_time
                },
                'services': {
                    'database': 'ok',
                    'cache': 'ok'
                }
            })
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }, status=500)

class IPWhitelistMiddleware(MiddlewareMixin):
    """
    IP whitelist middleware for admin and sensitive endpoints.
    """
    
    # Admin IP whitelist - add your IPs here
    ADMIN_WHITELIST = getattr(settings, 'ADMIN_IP_WHITELIST', [])
    
    # Paths that require IP whitelisting
    PROTECTED_PATHS = ['/admin/', '/api/admin/']
    
    def process_request(self, request):
        if not self.ADMIN_WHITELIST:
            return None  # Skip if no whitelist configured
            
        # Check if request path is protected
        for protected_path in self.PROTECTED_PATHS:
            if request.path_info.startswith(protected_path):
                client_ip = self.get_client_ip(request)
                
                if client_ip not in self.ADMIN_WHITELIST:
                    logger.warning(
                        f"Blocked admin access from non-whitelisted IP: {client_ip}, "
                        f"Path: {request.path_info}"
                    )
                    return JsonResponse({
                        'error': 'Access denied',
                        'code': 'IP_NOT_WHITELISTED'
                    }, status=403)
        
        return None
    
    def get_client_ip(self, request):
        """Get real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Comprehensive request logging middleware for security and debugging.
    """
    
    def process_request(self, request):
        # Log all requests with relevant information
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        user = getattr(request, 'user', None)
        user_id = user.id if user and not isinstance(user, AnonymousUser) else 'anonymous'
        
        # Create request signature for tracking
        request_data = f"{request.method}:{request.path}:{client_ip}"
        request.signature = hashlib.md5(request_data.encode()).hexdigest()[:8]
        
        logger.info(
            f"Request [{request.signature}]: {request.method} {request.path} "
            f"from IP {client_ip}, User: {user_id}, UA: {user_agent[:100]}"
        )
    
    def process_response(self, request, response):
        if hasattr(request, 'signature'):
            duration = getattr(request, 'start_time', 0)
            if duration:
                duration = time.time() - duration
            
            logger.info(
                f"Response [{request.signature}]: Status {response.status_code}, "
                f"Duration: {duration:.3f}s, Size: {len(response.content)} bytes"
            )
        
        return response