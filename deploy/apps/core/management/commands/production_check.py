# Management command to check production readiness

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connection
import os
import sys


class Command(BaseCommand):
    help = 'Check if the application is ready for production deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Production Readiness Check ==='))
        
        checks = [
            self.check_debug_mode,
            self.check_secret_key,
            self.check_allowed_hosts,
            self.check_database,
            self.check_static_files,
            self.check_media_files,
            self.check_cache,
            self.check_celery,
            self.check_logging,
            self.check_security_settings,
            self.check_required_env_vars,
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for check in checks:
            try:
                result = check()
                if result == 'pass':
                    passed += 1
                elif result == 'fail':
                    failed += 1
                elif result == 'warning':
                    warnings += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error running check {check.__name__}: {str(e)}')
                )
                failed += 1
        
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(f'✓ Passed: {passed}')
        if warnings > 0:
            self.stdout.write(f'⚠ Warnings: {warnings}')
        if failed > 0:
            self.stdout.write(f'✗ Failed: {failed}')
        
        if failed == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Application is ready for production!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n❌ Application is NOT ready for production!')
            )
            sys.exit(1)

    def check_debug_mode(self):
        """Check if DEBUG is disabled"""
        self.stdout.write('Checking DEBUG mode...', ending=' ')
        if settings.DEBUG:
            self.stdout.write(self.style.ERROR('✗ DEBUG is enabled'))
            return 'fail'
        else:
            self.stdout.write(self.style.SUCCESS('✓ DEBUG is disabled'))
            return 'pass'

    def check_secret_key(self):
        """Check if SECRET_KEY is properly set"""
        self.stdout.write('Checking SECRET_KEY...', ending=' ')
        if not settings.SECRET_KEY or settings.SECRET_KEY == 'django-insecure-dev-key-change-in-production':
            self.stdout.write(self.style.ERROR('✗ SECRET_KEY is not set or using default'))
            return 'fail'
        else:
            self.stdout.write(self.style.SUCCESS('✓ SECRET_KEY is properly set'))
            return 'pass'

    def check_allowed_hosts(self):
        """Check if ALLOWED_HOSTS is configured"""
        self.stdout.write('Checking ALLOWED_HOSTS...', ending=' ')
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            self.stdout.write(self.style.ERROR('✗ ALLOWED_HOSTS is not properly configured'))
            return 'fail'
        else:
            self.stdout.write(self.style.SUCCESS('✓ ALLOWED_HOSTS is configured'))
            return 'pass'

    def check_database(self):
        """Check database connection"""
        self.stdout.write('Checking database connection...', ending=' ')
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
            return 'pass'
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {str(e)}'))
            return 'fail'

    def check_static_files(self):
        """Check static files configuration"""
        self.stdout.write('Checking static files...', ending=' ')
        if not hasattr(settings, 'STATIC_ROOT') or not settings.STATIC_ROOT:
            self.stdout.write(self.style.ERROR('✗ STATIC_ROOT is not configured'))
            return 'fail'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Static files configured'))
            return 'pass'

    def check_media_files(self):
        """Check media files configuration"""
        self.stdout.write('Checking media files...', ending=' ')
        if not hasattr(settings, 'MEDIA_ROOT') and not hasattr(settings, 'DEFAULT_FILE_STORAGE'):
            self.stdout.write(self.style.ERROR('✗ Media files storage not configured'))
            return 'fail'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Media files configured'))
            return 'pass'

    def check_cache(self):
        """Check cache configuration"""
        self.stdout.write('Checking cache configuration...', ending=' ')
        if 'default' not in settings.CACHES:
            self.stdout.write(self.style.WARNING('⚠ Cache not configured'))
            return 'warning'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Cache configured'))
            return 'pass'

    def check_celery(self):
        """Check Celery configuration"""
        self.stdout.write('Checking Celery configuration...', ending=' ')
        if not hasattr(settings, 'CELERY_BROKER_URL'):
            self.stdout.write(self.style.WARNING('⚠ Celery not configured'))
            return 'warning'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Celery configured'))
            return 'pass'

    def check_logging(self):
        """Check logging configuration"""
        self.stdout.write('Checking logging configuration...', ending=' ')
        if not hasattr(settings, 'LOGGING'):
            self.stdout.write(self.style.WARNING('⚠ Logging not configured'))
            return 'warning'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Logging configured'))
            return 'pass'

    def check_security_settings(self):
        """Check security settings"""
        self.stdout.write('Checking security settings...', ending=' ')
        security_settings = [
            'SECURE_SSL_REDIRECT',
            'SESSION_COOKIE_SECURE',
            'CSRF_COOKIE_SECURE',
            'SECURE_BROWSER_XSS_FILTER',
            'SECURE_CONTENT_TYPE_NOSNIFF',
        ]
        
        missing = []
        for setting in security_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing.append(setting)
        
        if missing:
            self.stdout.write(self.style.WARNING(f'⚠ Missing security settings: {", ".join(missing)}'))
            return 'warning'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Security settings configured'))
            return 'pass'

    def check_required_env_vars(self):
        """Check required environment variables"""
        self.stdout.write('Checking required environment variables...', ending=' ')
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
        ]
        
        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                missing.append(var)
        
        if missing:
            self.stdout.write(self.style.ERROR(f'✗ Missing environment variables: {", ".join(missing)}'))
            return 'fail'
        else:
            self.stdout.write(self.style.SUCCESS('✓ Required environment variables set'))
            return 'pass'