"""
Advanced API Protection and Rate Limiting System for StartupHub Production
Implements sophisticated rate limiting, DDoS protection, and API security measures.
"""

import time
import hashlib
import json
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from functools import wraps
from ipaddress import ip_address, ip_network
import re
from collections import defaultdict

logger = logging.getLogger('startup_hub.api_protection')

class RateLimiter:
    """
    Advanced rate limiting with multiple strategies and user tiers.
    """
    
    # Rate limit configurations by user type and endpoint
    RATE_LIMITS = {
        'anonymous': {
            'default': {'requests': 100, 'window': 3600},      # 100/hour
            'auth': {'requests': 5, 'window': 300},            # 5/5min for auth endpoints
            'api_heavy': {'requests': 10, 'window': 3600},     # 10/hour for heavy endpoints
            'search': {'requests': 50, 'window': 3600},        # 50/hour for search
        },
        'authenticated': {
            'default': {'requests': 1000, 'window': 3600},     # 1000/hour
            'api_heavy': {'requests': 100, 'window': 3600},    # 100/hour for heavy endpoints
            'upload': {'requests': 20, 'window': 3600},        # 20/hour for uploads
            'search': {'requests': 200, 'window': 3600},       # 200/hour for search
        },
        'premium': {
            'default': {'requests': 5000, 'window': 3600},     # 5000/hour
            'api_heavy': {'requests': 500, 'window': 3600},    # 500/hour for heavy endpoints
            'upload': {'requests': 100, 'window': 3600},       # 100/hour for uploads
            'search': {'requests': 1000, 'window': 3600},      # 1000/hour for search
        },
        'admin': {
            'default': {'requests': 10000, 'window': 3600},    # 10000/hour
            'api_heavy': {'requests': 1000, 'window': 3600},   # 1000/hour
            'upload': {'requests': 500, 'window': 3600},       # 500/hour
            'search': {'requests': 5000, 'window': 3600},      # 5000/hour
        }
    }
    
    # Endpoint categorization
    ENDPOINT_CATEGORIES = {
        'auth': ['/api/auth/', '/api/users/login/', '/api/users/register/'],
        'api_heavy': ['/api/analysis/', '/api/export/', '/api/reports/'],
        'upload': ['/api/upload/', '/api/media/', '/api/files/'],
        'search': ['/api/search/', '/api/filter/'],
    }
    
    def __init__(self):
        self.cache_prefix = 'rate_limit:'
        self.violation_cache_prefix = 'rate_violations:'
    
    def get_client_identifier(self, request):
        """Get unique client identifier for rate limiting."""
        # Try to get real IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # For authenticated users, include user ID
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}:{ip}"
        
        return f"ip:{ip}"
    
    def get_user_tier(self, request):
        """Determine user tier for rate limiting."""
        if not hasattr(request, 'user'):
            return 'anonymous'
        
        user = request.user
        
        if isinstance(user, AnonymousUser):
            return 'anonymous'
        elif user.is_staff or user.is_superuser:
            return 'admin'
        elif hasattr(user, 'subscription_status') and user.subscription_status == 'active':
            return 'premium'
        elif user.is_authenticated:
            return 'authenticated'
        else:
            return 'anonymous'
    
    def get_endpoint_category(self, path):
        """Categorize endpoint for appropriate rate limiting."""
        for category, patterns in self.ENDPOINT_CATEGORIES.items():
            for pattern in patterns:
                if path.startswith(pattern):
                    return category
        return 'default'
    
    def is_rate_limited(self, request):
        """Check if request should be rate limited."""
        client_id = self.get_client_identifier(request)
        user_tier = self.get_user_tier(request)
        endpoint_category = self.get_endpoint_category(request.path)
        
        # Get rate limit configuration
        rate_config = self.RATE_LIMITS.get(user_tier, self.RATE_LIMITS['anonymous'])
        limit_config = rate_config.get(endpoint_category, rate_config['default'])
        
        # Create cache key
        cache_key = f"{self.cache_prefix}{user_tier}:{endpoint_category}:{client_id}"
        
        # Get current request count
        current_requests = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if current_requests >= limit_config['requests']:
            # Log rate limit violation
            self.log_rate_limit_violation(request, client_id, user_tier, current_requests, limit_config)
            return True, limit_config
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, limit_config['window'])
        
        return False, limit_config
    
    def log_rate_limit_violation(self, request, client_id, user_tier, current_requests, limit_config):
        """Log rate limit violations for monitoring."""
        violation_data = {
            'timestamp': timezone.now().isoformat(),
            'client_id': client_id,
            'user_tier': user_tier,
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
            'current_requests': current_requests,
            'limit': limit_config['requests'],
            'window': limit_config['window']
        }
        
        # Store violation for analysis
        violation_key = f"{self.violation_cache_prefix}{client_id}:{int(time.time() // 300)}"  # 5-minute buckets
        violations = cache.get(violation_key, [])
        violations.append(violation_data)
        cache.set(violation_key, violations, 3600)  # Store for 1 hour
        
        logger.warning(
            f"Rate limit violation: {client_id} ({user_tier}) "
            f"exceeded {limit_config['requests']} requests in {limit_config['window']}s "
            f"for {request.path}"
        )
    
    def get_rate_limit_headers(self, request, limit_config, current_requests=0):
        """Generate rate limit headers for response."""
        remaining = max(0, limit_config['requests'] - current_requests)
        reset_time = int(time.time()) + limit_config['window']
        
        return {
            'X-RateLimit-Limit': str(limit_config['requests']),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time),
            'X-RateLimit-Window': str(limit_config['window'])
        }

class DDoSProtection:
    """
    DDoS protection with pattern detection and automatic blocking.
    """
    
    def __init__(self):
        self.suspicious_threshold = 50  # Requests per minute
        self.block_duration = 3600      # 1 hour
        self.pattern_cache_prefix = 'ddos_pattern:'
        self.blocked_ips_cache_prefix = 'blocked_ip:'
    
    def is_suspicious_pattern(self, request):
        """Detect suspicious request patterns."""
        client_ip = self.get_client_ip(request)
        
        # Check if IP is already blocked
        if self.is_ip_blocked(client_ip):
            return True, "IP blocked due to previous violations"
        
        # Track request patterns
        minute_key = f"{self.pattern_cache_prefix}{client_ip}:{int(time.time() // 60)}"
        requests_this_minute = cache.get(minute_key, 0) + 1
        cache.set(minute_key, requests_this_minute, 120)  # Store for 2 minutes
        
        # Check for suspicious patterns
        if requests_this_minute > self.suspicious_threshold:
            self.block_ip(client_ip, "Excessive requests per minute")
            return True, "DDoS pattern detected"
        
        # Check for other suspicious patterns
        if self.check_bot_patterns(request):
            return True, "Bot-like behavior detected"
        
        if self.check_attack_patterns(request):
            self.block_ip(client_ip, "Attack pattern detected")
            return True, "Attack pattern detected"
        
        return False, None
    
    def check_bot_patterns(self, request):
        """Check for bot-like behavior patterns."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Known bot patterns
        bot_patterns = [
            r'bot', r'crawler', r'spider', r'scraper',
            r'curl', r'wget', r'python-requests',
            r'automation', r'test', r'monitor'
        ]
        
        for pattern in bot_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                # Allow some legitimate bots
                if not any(good_bot in user_agent.lower() for good_bot in 
                          ['googlebot', 'bingbot', 'slurp', 'duckduckbot']):
                    return True
        
        return False
    
    def check_attack_patterns(self, request):
        """Check for common attack patterns."""
        # Check URL for attack patterns
        attack_patterns = [
            r'\.\./', r'etc/passwd', r'cmd\.exe', r'<script',
            r'union\s+select', r'drop\s+table', r'exec\s*\(',
            r'javascript:', r'vbscript:', r'onload=', r'onerror='
        ]
        
        url_path = request.get_full_path()
        for pattern in attack_patterns:
            if re.search(pattern, url_path, re.IGNORECASE):
                return True
        
        # Check for SQL injection in parameters
        for value in request.GET.values():
            for pattern in attack_patterns:
                if re.search(pattern, str(value), re.IGNORECASE):
                    return True
        
        return False
    
    def block_ip(self, ip_address, reason):
        """Block an IP address."""
        block_key = f"{self.blocked_ips_cache_prefix}{ip_address}"
        block_data = {
            'blocked_at': timezone.now().isoformat(),
            'reason': reason,
            'expires_at': (timezone.now() + timedelta(seconds=self.block_duration)).isoformat()
        }
        
        cache.set(block_key, block_data, self.block_duration)
        
        logger.critical(f"IP blocked: {ip_address} - {reason}")
    
    def is_ip_blocked(self, ip_address):
        """Check if an IP address is blocked."""
        block_key = f"{self.blocked_ips_cache_prefix}{ip_address}"
        return cache.get(block_key) is not None
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip

class APISecurityValidator:
    """
    Comprehensive API security validation.
    """
    
    def __init__(self):
        self.max_payload_size = 10 * 1024 * 1024  # 10MB
        self.allowed_content_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain'
        ]
    
    def validate_request(self, request):
        """Validate request for security issues."""
        errors = []
        
        # Validate content length
        if hasattr(request, 'content_length') and request.content_length:
            if request.content_length > self.max_payload_size:
                errors.append(f"Payload too large: {request.content_length} bytes")
        
        # Validate content type
        content_type = request.content_type
        if content_type and not any(ct in content_type for ct in self.allowed_content_types):
            errors.append(f"Invalid content type: {content_type}")
        
        # Validate headers
        header_errors = self.validate_headers(request)
        errors.extend(header_errors)
        
        # Validate authentication
        auth_errors = self.validate_authentication(request)
        errors.extend(auth_errors)
        
        return errors
    
    def validate_headers(self, request):
        """Validate request headers."""
        errors = []
        
        # Check for required headers on certain endpoints
        if request.path.startswith('/api/'):
            # Check for proper API versioning
            if not request.META.get('HTTP_ACCEPT') and request.method in ['POST', 'PUT', 'PATCH']:
                errors.append("Missing Accept header for API request")
        
        # Check for suspicious headers
        suspicious_headers = ['X-Cluster-Client-Ip', 'X-Real-Ip']
        for header in suspicious_headers:
            if request.META.get(f'HTTP_{header.upper().replace("-", "_")}'):
                logger.warning(f"Suspicious header detected: {header}")
        
        return errors
    
    def validate_authentication(self, request):
        """Validate authentication requirements."""
        errors = []
        
        # Check for protected endpoints
        protected_paths = ['/api/admin/', '/api/users/profile/']
        
        for path in protected_paths:
            if request.path.startswith(path):
                if not hasattr(request, 'user') or not request.user.is_authenticated:
                    errors.append("Authentication required for this endpoint")
        
        return errors

def rate_limit(category='default', per_user=True):
    """
    Decorator for applying rate limiting to views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rate_limiter = RateLimiter()
            
            # Override endpoint category if specified
            original_path = request.path
            if category != 'default':
                # Temporarily modify path for categorization
                request.path = f"/api/{category}/"
            
            is_limited, limit_config = rate_limiter.is_rate_limited(request)
            
            # Restore original path
            request.path = original_path
            
            if is_limited:
                response = JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f"Too many requests. Limit: {limit_config['requests']} per {limit_config['window']} seconds",
                    'retry_after': limit_config['window']
                }, status=429)
                
                # Add rate limit headers
                headers = rate_limiter.get_rate_limit_headers(request, limit_config, limit_config['requests'])
                for header, value in headers.items():
                    response[header] = value
                
                return response
            
            # Execute view
            response = view_func(request, *args, **kwargs)
            
            # Add rate limit headers to successful responses
            if hasattr(response, 'status_code') and response.status_code < 400:
                headers = rate_limiter.get_rate_limit_headers(request, limit_config)
                for header, value in headers.items():
                    response[header] = value
            
            return response
        
        return wrapper
    return decorator

def ddos_protection(view_func):
    """
    Decorator for DDoS protection.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        ddos_protector = DDoSProtection()
        
        is_suspicious, reason = ddos_protector.is_suspicious_pattern(request)
        
        if is_suspicious:
            logger.warning(f"DDoS protection triggered: {reason} for {request.path}")
            return JsonResponse({
                'error': 'Request blocked',
                'message': 'Your request has been blocked due to suspicious activity',
                'code': 'DDOS_PROTECTION'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def api_security_validation(view_func):
    """
    Decorator for API security validation.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        validator = APISecurityValidator()
        
        validation_errors = validator.validate_request(request)
        
        if validation_errors:
            logger.warning(f"API security validation failed: {validation_errors}")
            return JsonResponse({
                'error': 'Invalid request',
                'message': 'Request failed security validation',
                'details': validation_errors
            }, status=400)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

class APIProtectionMiddleware:
    """
    Comprehensive API protection middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter()
        self.ddos_protector = DDoSProtection()
        self.security_validator = APISecurityValidator()
    
    def __call__(self, request):
        # Skip protection for health checks
        if request.path in ['/health/', '/ping/', '/status/']:
            return self.get_response(request)
        
        # Apply DDoS protection
        is_suspicious, reason = self.ddos_protector.is_suspicious_pattern(request)
        if is_suspicious:
            return JsonResponse({
                'error': 'Request blocked',
                'message': 'Suspicious activity detected',
                'code': 'DDOS_PROTECTION'
            }, status=403)
        
        # Apply rate limiting to API endpoints
        if request.path.startswith('/api/'):
            is_limited, limit_config = self.rate_limiter.is_rate_limited(request)
            if is_limited:
                response = JsonResponse({
                    'error': 'Rate limit exceeded',
                    'retry_after': limit_config['window']
                }, status=429)
                
                # Add rate limit headers
                headers = self.rate_limiter.get_rate_limit_headers(request, limit_config, limit_config['requests'])
                for header, value in headers.items():
                    response[header] = value
                
                return response
            
            # Apply security validation
            validation_errors = self.security_validator.validate_request(request)
            if validation_errors:
                return JsonResponse({
                    'error': 'Security validation failed',
                    'details': validation_errors
                }, status=400)
        
        response = self.get_response(request)
        
        # Add security headers to API responses
        if request.path.startswith('/api/'):
            response['X-API-Version'] = '1.0'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
        
        return response

# Global instances
rate_limiter = RateLimiter()
ddos_protector = DDoSProtection()
api_security_validator = APISecurityValidator()

def get_api_protection_stats():
    """Get API protection statistics."""
    # This would typically pull from a database or cache
    # For now, return basic structure
    return {
        'timestamp': timezone.now().isoformat(),
        'rate_limit_violations': 0,  # Would be populated from cache/db
        'blocked_ips': 0,            # Would be populated from cache/db
        'ddos_attempts': 0,          # Would be populated from cache/db
        'security_violations': 0     # Would be populated from cache/db
    }