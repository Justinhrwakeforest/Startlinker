"""
Comprehensive Production Monitoring System for StartupHub
Implements real-time monitoring, alerting, and performance tracking.
"""

import os
import json
import time
import psutil
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import connections
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.core.management import call_command
from celery import current_app as celery_app
import redis

logger = logging.getLogger('startup_hub.monitoring')

class SystemMonitor:
    """
    System-level monitoring for CPU, memory, disk, and network.
    """
    
    @staticmethod
    def get_system_metrics():
        """Get comprehensive system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': load_avg
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free,
                    'swap_total': swap.total,
                    'swap_used': swap.used,
                    'swap_percent': swap.percent
                },
                'disk': {
                    'total': disk_usage.total,
                    'used': disk_usage.used,
                    'free': disk_usage.free,
                    'percent': (disk_usage.used / disk_usage.total) * 100,
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                },
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process_cpu,
                    'pid': process.pid,
                    'threads': process.num_threads()
                }
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return {'error': str(e)}

class DatabaseMonitor:
    """
    Database monitoring for connection health, query performance, and usage.
    """
    
    @staticmethod
    def check_database_health():
        """Check database connectivity and basic health."""
        try:
            # Test default database connection
            db_conn = connections['default']
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Get database size and connection info
            with db_conn.cursor() as cursor:
                # PostgreSQL specific queries
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections
                """)
                result = cursor.fetchone()
                
                return {
                    'status': 'healthy',
                    'database_size': result[0] if result else 'unknown',
                    'active_connections': result[1] if result else 0,
                    'max_connections': result[2] if result else 0,
                    'connection_pool_status': 'ok'
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def get_slow_queries():
        """Get slow running queries (PostgreSQL specific)."""
        try:
            db_conn = connections['default']
            with db_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pid,
                        now() - pg_stat_activity.query_start AS duration,
                        query,
                        state
                    FROM pg_stat_activity 
                    WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                    AND state = 'active'
                    ORDER BY duration DESC
                    LIMIT 10
                """)
                
                slow_queries = []
                for row in cursor.fetchall():
                    slow_queries.append({
                        'pid': row[0],
                        'duration': str(row[1]),
                        'query': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                        'state': row[3]
                    })
                
                return slow_queries
                
        except Exception as e:
            logger.error(f"Error getting slow queries: {str(e)}")
            return []

class CacheMonitor:
    """
    Redis cache monitoring for health, memory usage, and performance.
    """
    
    @staticmethod
    def check_cache_health():
        """Check Redis cache health and statistics."""
        try:
            # Test cache connectivity
            cache.set('health_check', 'ok', 30)
            result = cache.get('health_check')
            
            if result != 'ok':
                return {'status': 'unhealthy', 'error': 'Cache write/read failed'}
            
            # Get Redis info
            redis_client = cache._cache.get_client()
            info = redis_client.info()
            
            return {
                'status': 'healthy',
                'memory_used': info.get('used_memory_human', 'unknown'),
                'memory_peak': info.get('used_memory_peak_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

class ApplicationMonitor:
    """
    Application-level monitoring for Django-specific metrics.
    """
    
    @staticmethod
    def get_application_metrics():
        """Get Django application metrics."""
        try:
            # Get model counts
            from apps.users.models import User
            from apps.startups.models import Startup
            from apps.posts.models import Post
            from apps.jobs.models import Job
            from apps.messaging.models import Conversation
            
            model_counts = {
                'users': User.objects.count(),
                'startups': Startup.objects.count(),
                'posts': Post.objects.count(),
                'jobs': Job.objects.count(),
                'conversations': Conversation.objects.count()
            }
            
            # Get recent activity (last 24 hours)
            last_24h = timezone.now() - timedelta(hours=24)
            recent_activity = {
                'new_users': User.objects.filter(date_joined__gte=last_24h).count(),
                'new_startups': Startup.objects.filter(created_at__gte=last_24h).count(),
                'new_posts': Post.objects.filter(created_at__gte=last_24h).count(),
                'new_jobs': Job.objects.filter(created_at__gte=last_24h).count()
            }
            
            # Get performance metrics from cache
            avg_response_time = cache.get('perf:avg_response_time', 0)
            error_rate = cache.get('perf:error_rate', 0)
            
            return {
                'model_counts': model_counts,
                'recent_activity': recent_activity,
                'performance': {
                    'avg_response_time': avg_response_time,
                    'error_rate': error_rate
                },
                'cache_stats': CacheMonitor.check_cache_health()
            }
            
        except Exception as e:
            logger.error(f"Error getting application metrics: {str(e)}")
            return {'error': str(e)}

class CeleryMonitor:
    """
    Celery task monitoring for background job health.
    """
    
    @staticmethod
    def check_celery_health():
        """Check Celery worker and task health."""
        try:
            # Get Celery app inspect
            inspect = celery_app.control.inspect()
            
            # Get active workers
            active_workers = inspect.active() or {}
            
            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled() or {}
            
            # Get worker stats
            stats = inspect.stats() or {}
            
            # Calculate total tasks
            total_active_tasks = sum(len(tasks) for tasks in active_workers.values())
            total_scheduled_tasks = sum(len(tasks) for tasks in scheduled_tasks.values())
            
            return {
                'status': 'healthy' if active_workers else 'unhealthy',
                'active_workers': len(active_workers),
                'worker_names': list(active_workers.keys()),
                'active_tasks': total_active_tasks,
                'scheduled_tasks': total_scheduled_tasks,
                'worker_stats': stats
            }
            
        except Exception as e:
            logger.error(f"Celery health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

class AlertManager:
    """
    Alert management system for critical system events.
    """
    
    ALERT_THRESHOLDS = {
        'cpu_percent': 80,
        'memory_percent': 85,
        'disk_percent': 90,
        'response_time': 2.0,
        'error_rate': 5.0
    }
    
    @staticmethod
    def check_alerts():
        """Check system metrics against alert thresholds."""
        alerts = []
        
        try:
            # Get current system metrics
            system_metrics = SystemMonitor.get_system_metrics()
            
            if 'error' in system_metrics:
                alerts.append({
                    'level': 'critical',
                    'message': f"Failed to collect system metrics: {system_metrics['error']}",
                    'timestamp': timezone.now().isoformat()
                })
                return alerts
            
            # Check CPU usage
            cpu_percent = system_metrics['cpu']['percent']
            if cpu_percent > AlertManager.ALERT_THRESHOLDS['cpu_percent']:
                alerts.append({
                    'level': 'warning',
                    'message': f"High CPU usage: {cpu_percent}%",
                    'timestamp': timezone.now().isoformat(),
                    'metric': 'cpu_percent',
                    'value': cpu_percent,
                    'threshold': AlertManager.ALERT_THRESHOLDS['cpu_percent']
                })
            
            # Check memory usage
            memory_percent = system_metrics['memory']['percent']
            if memory_percent > AlertManager.ALERT_THRESHOLDS['memory_percent']:
                alerts.append({
                    'level': 'warning',
                    'message': f"High memory usage: {memory_percent}%",
                    'timestamp': timezone.now().isoformat(),
                    'metric': 'memory_percent',
                    'value': memory_percent,
                    'threshold': AlertManager.ALERT_THRESHOLDS['memory_percent']
                })
            
            # Check disk usage
            disk_percent = system_metrics['disk']['percent']
            if disk_percent > AlertManager.ALERT_THRESHOLDS['disk_percent']:
                alerts.append({
                    'level': 'critical',
                    'message': f"High disk usage: {disk_percent:.1f}%",
                    'timestamp': timezone.now().isoformat(),
                    'metric': 'disk_percent',
                    'value': disk_percent,
                    'threshold': AlertManager.ALERT_THRESHOLDS['disk_percent']
                })
            
            # Check database health
            db_health = DatabaseMonitor.check_database_health()
            if db_health['status'] != 'healthy':
                alerts.append({
                    'level': 'critical',
                    'message': f"Database unhealthy: {db_health.get('error', 'Unknown error')}",
                    'timestamp': timezone.now().isoformat(),
                    'metric': 'database_health'
                })
            
            # Check cache health
            cache_health = CacheMonitor.check_cache_health()
            if cache_health['status'] != 'healthy':
                alerts.append({
                    'level': 'critical',
                    'message': f"Cache unhealthy: {cache_health.get('error', 'Unknown error')}",
                    'timestamp': timezone.now().isoformat(),
                    'metric': 'cache_health'
                })
            
            # Store alerts in cache for dashboard
            if alerts:
                cache.set('system_alerts', alerts, 300)  # 5 minutes
                
                # Log critical alerts
                for alert in alerts:
                    if alert['level'] == 'critical':
                        logger.critical(f"ALERT: {alert['message']}")
                    else:
                        logger.warning(f"ALERT: {alert['message']}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            return [{
                'level': 'critical',
                'message': f"Alert system error: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }]

class HealthCheck:
    """
    Comprehensive health check system for load balancer integration.
    """
    
    @staticmethod
    def perform_health_check():
        """Perform comprehensive health check."""
        start_time = time.time()
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {},
            'response_time': 0
        }
        
        # Database check
        db_health = DatabaseMonitor.check_database_health()
        health_status['checks']['database'] = db_health
        if db_health['status'] != 'healthy':
            health_status['status'] = 'unhealthy'
        
        # Cache check
        cache_health = CacheMonitor.check_cache_health()
        health_status['checks']['cache'] = cache_health
        if cache_health['status'] != 'healthy':
            health_status['status'] = 'degraded'
        
        # Celery check
        celery_health = CeleryMonitor.check_celery_health()
        health_status['checks']['celery'] = celery_health
        if celery_health['status'] != 'healthy':
            health_status['status'] = 'degraded'
        
        # System resources check
        system_metrics = SystemMonitor.get_system_metrics()
        if 'error' not in system_metrics:
            # Check if system resources are critical
            if (system_metrics['memory']['percent'] > 95 or 
                system_metrics['disk']['percent'] > 95 or
                system_metrics['cpu']['percent'] > 95):
                health_status['status'] = 'degraded'
                health_status['checks']['system'] = {
                    'status': 'degraded',
                    'message': 'System resources critical'
                }
            else:
                health_status['checks']['system'] = {'status': 'healthy'}
        
        # Calculate total response time
        health_status['response_time'] = round(time.time() - start_time, 3)
        
        return health_status
    
    @staticmethod
    def get_monitoring_dashboard_data():
        """Get comprehensive monitoring data for dashboard."""
        try:
            return {
                'timestamp': timezone.now().isoformat(),
                'system_metrics': SystemMonitor.get_system_metrics(),
                'database_health': DatabaseMonitor.check_database_health(),
                'cache_health': CacheMonitor.check_cache_health(),
                'application_metrics': ApplicationMonitor.get_application_metrics(),
                'celery_health': CeleryMonitor.check_celery_health(),
                'alerts': AlertManager.check_alerts(),
                'slow_queries': DatabaseMonitor.get_slow_queries()
            }
        except Exception as e:
            logger.error(f"Error getting monitoring dashboard data: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }

# Global instances for backwards compatibility
metrics_collector = None
health_checker = HealthCheck()