"""
Database Optimization and Connection Pooling for StartupHub Production
Implements advanced database performance optimizations.
"""

import os
import logging
from django.conf import settings
from django.db import connections
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Max, Min
from django.db.models.query import QuerySet
from django.db import transaction
from contextlib import contextmanager
import time
from functools import wraps

logger = logging.getLogger('startup_hub.database')

class DatabaseConnectionPool:
    """
    Advanced database connection pooling configuration.
    """
    
    @staticmethod
    def get_production_database_config():
        """Get optimized database configuration for production."""
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'startup_hub'),
                'USER': os.environ.get('DB_USER', 'startup_hub'),
                'PASSWORD': os.environ.get('DB_PASSWORD'),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '5432'),
                'CONN_MAX_AGE': 600,  # 10 minutes
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {
                    'MAX_CONNS': 100,
                    'MIN_CONNS': 10,
                    'sslmode': 'require',
                    'application_name': 'startup_hub',
                    'options': '-c default_transaction_isolation=read_committed',
                    # Connection pool settings
                    'POOL_CLASS': 'psycopg2.pool.ThreadedConnectionPool',
                    'POOL_SIZE': 20,
                    'MAX_OVERFLOW': 30,
                    'POOL_TIMEOUT': 30,
                    'POOL_RECYCLE': 3600,  # 1 hour
                    'POOL_PRE_PING': True,
                },
                'TEST': {
                    'NAME': 'test_startup_hub',
                    'SERIALIZE': False,
                }
            },
            # Read replica for read-heavy operations
            'readonly': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_READONLY_NAME', os.environ.get('DB_NAME', 'startup_hub')),
                'USER': os.environ.get('DB_READONLY_USER', os.environ.get('DB_USER', 'startup_hub')),
                'PASSWORD': os.environ.get('DB_READONLY_PASSWORD', os.environ.get('DB_PASSWORD')),
                'HOST': os.environ.get('DB_READONLY_HOST', os.environ.get('DB_HOST', 'localhost')),
                'PORT': os.environ.get('DB_READONLY_PORT', os.environ.get('DB_PORT', '5432')),
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {
                    'sslmode': 'require',
                    'application_name': 'startup_hub_readonly',
                    'options': '-c default_transaction_isolation=read_committed -c transaction_read_only=on',
                }
            }
        }

class DatabaseRouter:
    """
    Database router for read/write splitting.
    """
    
    READ_MODELS = {
        'startups.startup',
        'posts.post',
        'users.user',
        'jobs.job',
    }
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.label_lower in self.READ_MODELS:
            return 'readonly'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default', 'readonly'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that only default database gets migrations."""
        return db == 'default'

class QueryOptimizer:
    """
    Query optimization utilities and decorators.
    """
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None, only_fields=None, defer_fields=None):
        """Apply common query optimizations."""
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        if only_fields:
            queryset = queryset.only(*only_fields)
        
        if defer_fields:
            queryset = queryset.defer(*defer_fields)
        
        return queryset
    
    @staticmethod
    def bulk_create_optimized(model_class, objects, batch_size=1000, ignore_conflicts=False):
        """Optimized bulk create with batching."""
        if not objects:
            return []
        
        created_objects = []
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            created_batch = model_class.objects.bulk_create(
                batch, 
                batch_size=batch_size,
                ignore_conflicts=ignore_conflicts
            )
            created_objects.extend(created_batch)
        
        logger.info(f"Bulk created {len(created_objects)} {model_class.__name__} objects")
        return created_objects
    
    @staticmethod
    def bulk_update_optimized(objects, fields, batch_size=1000):
        """Optimized bulk update with batching."""
        if not objects:
            return
        
        model_class = objects[0].__class__
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model_class.objects.bulk_update(batch, fields, batch_size=batch_size)
        
        logger.info(f"Bulk updated {len(objects)} {model_class.__name__} objects")

def query_timer(func):
    """Decorator to time database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log slow queries (> 1 second)
            logger.warning(f"Slow query in {func.__name__}: {execution_time:.3f}s")
        else:
            logger.debug(f"Query {func.__name__} executed in {execution_time:.3f}s")
        
        return result
    return wrapper

@contextmanager
def database_transaction_atomic():
    """Context manager for atomic database transactions with logging."""
    start_time = time.time()
    try:
        with transaction.atomic():
            yield
        execution_time = time.time() - start_time
        logger.debug(f"Transaction completed in {execution_time:.3f}s")
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Transaction failed after {execution_time:.3f}s: {str(e)}")
        raise

class DatabaseAnalyzer:
    """
    Database performance analysis tools.
    """
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze slow queries in PostgreSQL."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    WHERE mean_time > 1000  -- Queries taking more than 1 second on average
                    ORDER BY mean_time DESC
                    LIMIT 20;
                """)
                
                slow_queries = []
                for row in cursor.fetchall():
                    slow_queries.append({
                        'query': row[0][:200] + '...' if len(row[0]) > 200 else row[0],
                        'calls': row[1],
                        'total_time': row[2],
                        'mean_time': row[3],
                        'rows': row[4]
                    })
                
                return slow_queries
        except Exception as e:
            logger.error(f"Error analyzing slow queries: {str(e)}")
            return []
    
    @staticmethod
    def get_database_stats():
        """Get database statistics and health metrics."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Database size
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cursor.fetchone()[0]
                
                # Connection stats
                cursor.execute("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database();
                """)
                conn_stats = cursor.fetchone()
                
                # Table sizes
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10;
                """)
                table_sizes = [
                    {
                        'schema': row[0],
                        'table': row[1],
                        'size': row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
                return {
                    'database_size': db_size,
                    'total_connections': conn_stats[0],
                    'active_connections': conn_stats[1],
                    'idle_connections': conn_stats[2],
                    'largest_tables': table_sizes
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}
    
    @staticmethod
    def check_missing_indexes():
        """Check for missing indexes on frequently queried columns."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    AND n_distinct > 100  -- Columns with high cardinality
                    AND correlation < 0.5  -- Not well correlated
                    ORDER BY n_distinct DESC;
                """)
                
                potential_indexes = []
                for row in cursor.fetchall():
                    potential_indexes.append({
                        'schema': row[0],
                        'table': row[1],
                        'column': row[2],
                        'distinct_values': row[3],
                        'correlation': row[4]
                    })
                
                return potential_indexes
                
        except Exception as e:
            logger.error(f"Error checking missing indexes: {str(e)}")
            return []

class DatabaseOptimizationCommand:
    """
    Database optimization maintenance commands.
    """
    
    @staticmethod
    def vacuum_analyze_all():
        """Run VACUUM ANALYZE on all tables."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("VACUUM ANALYZE;")
            logger.info("VACUUM ANALYZE completed successfully")
        except Exception as e:
            logger.error(f"VACUUM ANALYZE failed: {str(e)}")
    
    @staticmethod
    def update_table_statistics():
        """Update table statistics for query planner."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("ANALYZE;")
            logger.info("Table statistics updated successfully")
        except Exception as e:
            logger.error(f"Statistics update failed: {str(e)}")
    
    @staticmethod
    def optimize_database():
        """Run comprehensive database optimization."""
        logger.info("Starting database optimization...")
        
        # Update statistics
        DatabaseOptimizationCommand.update_table_statistics()
        
        # Vacuum and analyze
        DatabaseOptimizationCommand.vacuum_analyze_all()
        
        # Log database stats
        stats = DatabaseAnalyzer.get_database_stats()
        logger.info(f"Database optimization completed. Stats: {stats}")

# Connection health check
def check_database_connections():
    """Check health of all database connections."""
    healthy_connections = []
    unhealthy_connections = []
    
    for alias in connections:
        try:
            conn = connections[alias]
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            healthy_connections.append(alias)
        except Exception as e:
            unhealthy_connections.append({
                'alias': alias,
                'error': str(e)
            })
            logger.error(f"Database connection {alias} is unhealthy: {str(e)}")
    
    return {
        'healthy': healthy_connections,
        'unhealthy': unhealthy_connections,
        'total_connections': len(connections)
    }

# Index recommendations
class IndexRecommendations:
    """
    Generate index recommendations based on query patterns.
    """
    
    COMMON_QUERY_PATTERNS = {
        'startups_startup': [
            'status',
            'created_at',
            'ranking_score',
            'industry_id',
            'founder_id'
        ],
        'posts_post': [
            'created_at',
            'author_id',
            'status'
        ],
        'jobs_job': [
            'status',
            'created_at',
            'company_id',
            'location'
        ],
        'users_user': [
            'email',
            'username',
            'is_active',
            'date_joined'
        ]
    }
    
    @staticmethod
    def generate_index_sql():
        """Generate SQL for recommended indexes."""
        index_sql = []
        
        for table, columns in IndexRecommendations.COMMON_QUERY_PATTERNS.items():
            for column in columns:
                index_name = f"idx_{table}_{column}"
                sql = f"CREATE INDEX CONCURRENTLY {index_name} ON {table} ({column});"
                index_sql.append(sql)
        
        return index_sql
    
    @staticmethod
    def create_recommended_indexes():
        """Create recommended indexes."""
        try:
            from django.db import connection
            index_sql_list = IndexRecommendations.generate_index_sql()
            
            with connection.cursor() as cursor:
                for sql in index_sql_list:
                    try:
                        cursor.execute(sql)
                        logger.info(f"Created index: {sql}")
                    except Exception as e:
                        if 'already exists' not in str(e):
                            logger.error(f"Failed to create index: {sql}, Error: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error creating recommended indexes: {str(e)}")

# Global configuration function
def apply_database_optimizations():
    """Apply all database optimizations."""
    try:
        # Update database configuration
        optimized_config = DatabaseConnectionPool.get_production_database_config()
        settings.DATABASES.update(optimized_config)
        
        # Add database router
        if 'startup_hub.database_optimization.DatabaseRouter' not in settings.DATABASE_ROUTERS:
            settings.DATABASE_ROUTERS.append('startup_hub.database_optimization.DatabaseRouter')
        
        logger.info("Database optimizations applied successfully")
        
    except Exception as e:
        logger.error(f"Failed to apply database optimizations: {str(e)}")

# Performance monitoring
class DatabasePerformanceMonitor:
    """
    Monitor database performance metrics.
    """
    
    @staticmethod
    def get_performance_metrics():
        """Get comprehensive database performance metrics."""
        return {
            'connection_health': check_database_connections(),
            'database_stats': DatabaseAnalyzer.get_database_stats(),
            'slow_queries': DatabaseAnalyzer.analyze_slow_queries(),
            'missing_indexes': DatabaseAnalyzer.check_missing_indexes()
        }