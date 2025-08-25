"""
Advanced Caching and Performance Configuration for StartupHub Production
Implements multi-tier caching strategy with Redis backend.
"""

import os
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_headers, vary_on_cookie
from django.utils.cache import patch_response_headers
from functools import wraps
import hashlib
import json
import time
import logging

logger = logging.getLogger('startup_hub.cache')

# Cache Configuration
CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'startup_hub',
        'VERSION': 1,
        'TIMEOUT': 300,  # 5 minutes default
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'sessions',
        'TIMEOUT': 86400,  # 24 hours
    },
    'page_cache': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'pages',
        'TIMEOUT': 3600,  # 1 hour
    },
    'api_cache': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/4'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'api',
        'TIMEOUT': 600,  # 10 minutes
    }
}

class CacheManager:
    """
    Centralized cache management with advanced features.
    """
    
    # Cache timeout configurations (in seconds)
    CACHE_TIMEOUTS = {
        'startup_list': 300,      # 5 minutes
        'startup_detail': 600,    # 10 minutes
        'user_profile': 900,      # 15 minutes
        'job_list': 300,          # 5 minutes
        'post_feed': 180,         # 3 minutes
        'industry_list': 3600,    # 1 hour
        'static_content': 86400,  # 24 hours
        'search_results': 300,    # 5 minutes
        'analytics': 1800,        # 30 minutes
    }
    
    @staticmethod
    def get_cache_key(prefix, *args, **kwargs):
        """Generate consistent cache keys."""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        
        # Create hash for long keys
        key_string = ":".join(key_parts)
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_string
    
    @staticmethod
    def set_cache(key, value, timeout=None, version=None):
        """Set cache with logging and error handling."""
        try:
            cache.set(key, value, timeout=timeout, version=version)
            logger.debug(f"Cache SET: {key} (timeout: {timeout})")
        except Exception as e:
            logger.error(f"Cache SET failed for key {key}: {str(e)}")
    
    @staticmethod
    def get_cache(key, default=None, version=None):
        """Get cache with logging and error handling."""
        try:
            value = cache.get(key, default=default, version=version)
            if value is not None:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache GET failed for key {key}: {str(e)}")
            return default
    
    @staticmethod
    def delete_cache(key, version=None):
        """Delete cache with logging."""
        try:
            cache.delete(key, version=version)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache DELETE failed for key {key}: {str(e)}")
    
    @staticmethod
    def clear_pattern(pattern):
        """Clear cache keys matching pattern."""
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection('default')
            keys = conn.keys(f"*{pattern}*")
            if keys:
                conn.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {str(e)}")

def cache_function(timeout=300, key_prefix=None, vary_on=None):
    """
    Advanced function-level caching decorator.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = f"{func.__module__}.{func.__name__}"
            
            # Include vary_on parameters in cache key
            cache_key_parts = [prefix]
            if vary_on:
                for vary_param in vary_on:
                    if vary_param in kwargs:
                        cache_key_parts.append(f"{vary_param}:{kwargs[vary_param]}")
            
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            cache_key = CacheManager.get_cache_key(*cache_key_parts)
            
            # Try to get from cache
            cached_result = CacheManager.get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            CacheManager.set_cache(cache_key, result, timeout=timeout)
            
            logger.info(f"Function {func.__name__} executed in {execution_time:.3f}s and cached")
            return result
        
        return wrapper
    return decorator

def smart_cache_page(timeout=300, cache_name='page_cache', key_prefix=None):
    """
    Smart page caching that considers user authentication and query parameters.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key based on request
            key_parts = [
                key_prefix or view_func.__name__,
                request.path,
                request.GET.urlencode(),
                'auth' if request.user.is_authenticated else 'anon'
            ]
            
            if request.user.is_authenticated:
                key_parts.append(f"user:{request.user.id}")
            
            cache_key = CacheManager.get_cache_key(*key_parts)
            
            # Try to get from cache
            cached_response = cache.get(cache_key, cache=cache_name)
            if cached_response is not None:
                logger.debug(f"Page cache HIT: {cache_key}")
                return cached_response
            
            # Execute view and cache response
            start_time = time.time()
            response = view_func(request, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Only cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response, timeout=timeout, cache=cache_name)
                logger.info(f"Page cached: {cache_key} (execution: {execution_time:.3f}s)")
            
            return response
        
        return wrapper
    return decorator

class QuerysetCache:
    """
    Advanced queryset caching with invalidation.
    """
    
    @staticmethod
    def cache_queryset(queryset, cache_key, timeout=300, select_related=None, prefetch_related=None):
        """Cache a queryset with optional optimization."""
        # Optimize queryset if needed
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        # Convert to list and cache
        data = list(queryset.values())
        CacheManager.set_cache(cache_key, data, timeout=timeout)
        return data
    
    @staticmethod
    def get_cached_queryset(cache_key, model_class=None):
        """Get cached queryset data."""
        cached_data = CacheManager.get_cache(cache_key)
        if cached_data is not None and model_class:
            # Convert back to queryset if model provided
            ids = [item['id'] for item in cached_data]
            return model_class.objects.filter(id__in=ids)
        return cached_data
    
    @staticmethod
    def invalidate_model_cache(model_name, instance_id=None):
        """Invalidate cache for a specific model."""
        if instance_id:
            pattern = f"{model_name}:{instance_id}"
        else:
            pattern = f"{model_name}:"
        
        CacheManager.clear_pattern(pattern)

class PerformanceOptimizer:
    """
    Performance optimization utilities.
    """
    
    @staticmethod
    def optimize_database_queries():
        """Enable database query optimization."""
        # Enable query caching
        settings.DATABASES['default']['OPTIONS'].update({
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        })
    
    @staticmethod
    def setup_connection_pooling():
        """Setup database connection pooling."""
        settings.DATABASES['default'].update({
            'CONN_MAX_AGE': 600,  # 10 minutes
            'CONN_HEALTH_CHECKS': True,
        })
    
    @staticmethod
    def configure_static_files_caching():
        """Configure static files caching."""
        return {
            'STATICFILES_STORAGE': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            'WHITENOISE_MAX_AGE': 31536000,  # 1 year
            'WHITENOISE_USE_FINDERS': True,
            'WHITENOISE_AUTOREFRESH': False,
        }

# Template fragment caching utilities
def cache_template_fragment(fragment_name, *vary_on, timeout=300):
    """Cache template fragments with automatic invalidation."""
    def get_cache_key():
        return make_template_fragment_key(fragment_name, vary_on)
    
    def invalidate():
        cache_key = get_cache_key()
        cache.delete(cache_key)
    
    return {
        'cache_key': get_cache_key(),
        'timeout': timeout,
        'invalidate': invalidate
    }

# API response caching
def cache_api_response(timeout=600, vary_on_user=True, vary_on_params=None):
    """Cache API responses with intelligent key generation."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            key_parts = [f"api:{view_func.__name__}"]
            
            if vary_on_user and request.user.is_authenticated:
                key_parts.append(f"user:{request.user.id}")
            
            if vary_on_params:
                for param in vary_on_params:
                    value = request.GET.get(param) or request.POST.get(param)
                    if value:
                        key_parts.append(f"{param}:{value}")
            
            # Add query parameters
            if request.GET:
                key_parts.append(f"params:{request.GET.urlencode()}")
            
            cache_key = CacheManager.get_cache_key(*key_parts)
            
            # Try cache first
            cached_response = CacheManager.get_cache(cache_key)
            if cached_response is not None:
                logger.debug(f"API cache HIT: {cache_key}")
                return cached_response
            
            # Execute view
            response = view_func(request, *args, **kwargs)
            
            # Cache successful responses
            if hasattr(response, 'status_code') and response.status_code == 200:
                CacheManager.set_cache(cache_key, response, timeout=timeout)
                logger.debug(f"API response cached: {cache_key}")
            
            return response
        
        return wrapper
    return decorator

# Background cache warming
class CacheWarmer:
    """
    Background cache warming to improve user experience.
    """
    
    @staticmethod
    def warm_startup_cache():
        """Warm frequently accessed startup data."""
        try:
            from apps.startups.models import Startup
            
            # Cache top startups
            top_startups = Startup.objects.filter(status='active').order_by('-ranking_score')[:20]
            cache_key = CacheManager.get_cache_key('startups:top')
            CacheManager.set_cache(cache_key, list(top_startups.values()), timeout=3600)
            
            logger.info("Startup cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm startup cache: {str(e)}")
    
    @staticmethod
    def warm_user_cache():
        """Warm user-related cache data."""
        try:
            from apps.users.models import User
            
            # Cache active user count
            active_users = User.objects.filter(is_active=True).count()
            cache_key = CacheManager.get_cache_key('users:active_count')
            CacheManager.set_cache(cache_key, active_users, timeout=1800)
            
            logger.info("User cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm user cache: {str(e)}")
    
    @staticmethod
    def warm_all_caches():
        """Warm all application caches."""
        CacheWarmer.warm_startup_cache()
        CacheWarmer.warm_user_cache()
        logger.info("All caches warmed successfully")

# Cache invalidation signals
def setup_cache_invalidation():
    """Setup automatic cache invalidation on model changes."""
    from django.db.models.signals import post_save, post_delete
    from django.dispatch import receiver
    
    @receiver(post_save)
    def invalidate_cache_on_save(sender, instance, **kwargs):
        model_name = sender._meta.label_lower
        QuerysetCache.invalidate_model_cache(model_name, instance.pk)
    
    @receiver(post_delete)
    def invalidate_cache_on_delete(sender, instance, **kwargs):
        model_name = sender._meta.label_lower
        QuerysetCache.invalidate_model_cache(model_name, instance.pk)

# Global cache configuration
def get_production_cache_config():
    """Get production cache configuration."""
    return CACHE_SETTINGS