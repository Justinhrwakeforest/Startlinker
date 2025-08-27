# Production settings for StartupHub
from .base import *
import dj_database_url

# Add comprehensive production middleware
MIDDLEWARE = [
    'startup_hub.middleware.HealthCheckMiddleware',
    'startup_hub.middleware.SecurityHeadersMiddleware',
    'startup_hub.middleware.SecurityMonitoringMiddleware',
    'startup_hub.middleware.RateLimitMiddleware',
    'startup_hub.middleware.RequestLoggingMiddleware',
    'startup_hub.middleware.RequestTimingMiddleware',
    'startup_hub.middleware.IPWhitelistMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError("ALLOWED_HOSTS environment variable is required in production")

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Static files (CSS, JavaScript, Images)
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Additional security headers
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# SendGrid Email Configuration for Production
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')  # Set via environment variable
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@startlinker.com')
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'  # Use SendGrid backend for better performance
EMAIL_HOST_USER = DEFAULT_FROM_EMAIL
SENDGRID_SANDBOX_MODE_IN_DEBUG = False  # Always send emails in production

# Email verification settings
EMAIL_VERIFICATION_SETTINGS = {
    'VERIFICATION_TOKEN_EXPIRY_HOURS': 24,  # Token expires after 24 hours
    'FROM_EMAIL': DEFAULT_FROM_EMAIL,
    'SUBJECT_PREFIX': '[StartLinker] ',
    'RESEND_COOLDOWN_MINUTES': 5,  # Minimum time between verification emails
}

# Enforce email verification in production
REQUIRE_EMAIL_VERIFICATION = True

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://startlinker.com",
    "https://www.startlinker.com",
    "http://startlinker.com",
    "http://www.startlinker.com",
    "http://13.50.234.250",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow credentials for authentication
CORS_ALLOW_CREDENTIALS = True

# Allow all methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Allow headers
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'Authorization',
    'Content-Type',
    'X-Requested-With',
    'X-CSRFToken',
]

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://startlinker.com",
    "https://www.startlinker.com",
    "http://startlinker.com",
    "http://www.startlinker.com",
    "http://13.50.234.250",
]

# Disable CSRF for API endpoints using token authentication
CSRF_USE_SESSIONS = False

# Channel layer configuration with production Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

# Production logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/startup_hub/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/startup_hub/django_errors.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'startup_hub': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Performance optimizations
CONN_MAX_AGE = 60

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# If using AWS SES
if os.environ.get('USE_AWS_SES', 'False') == 'True':
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_REGION_NAME = AWS_S3_REGION_NAME
    AWS_SES_REGION_ENDPOINT = f'email.{AWS_S3_REGION_NAME}.amazonaws.com'

# Sentry configuration for error tracking
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment='production',
    )

# Job posting settings - Production should require admin approval
JOB_POSTING_SETTINGS = {
    'AUTO_APPROVE': False,  # Jobs require admin approval in production
    'REQUIRE_REVIEW': True,  # Force all jobs to go through review
    'AUTO_APPROVE_STAFF': True,  # Allow staff to auto-approve their jobs
    'AUTO_APPROVE_VERIFIED_STARTUPS': False,  # Even verified startups require approval
}