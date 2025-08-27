# PostgreSQL settings for StartupHub
from .base import *
import dj_database_url

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# PostgreSQL Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'startup_hub'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Celery Configuration - Use synchronous mode in development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Channel layer configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# Rate limiting settings
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Analytics settings (disabled in development)
ANALYTICS_SETTINGS = {
    'ENABLED': False,
    'TRACK_USER_ACTIVITY': False,
    'RETENTION_DAYS': 365,
}

# Security settings (relaxed for development)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Session settings
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = True

# Job posting settings
JOB_POSTING_SETTINGS = {
    'AUTO_APPROVE_VERIFIED_COMPANIES': True,
    'AUTO_APPROVE_STAFF': False,
    'AUTO_APPROVE_VERIFIED_STARTUPS': False,
}

# SendGrid Email Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')  # Set via environment variable
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@startlinker.com')
EMAIL_BACKEND = 'apps.users.sendgrid_backend.SendGridBackend'
EMAIL_HOST_USER = DEFAULT_FROM_EMAIL
SENDGRID_SANDBOX_MODE_IN_DEBUG = False

# Email verification settings
EMAIL_VERIFICATION_SETTINGS = {
    'VERIFICATION_TOKEN_EXPIRY_HOURS': 24,
    'FROM_EMAIL': DEFAULT_FROM_EMAIL,
    'SUBJECT_PREFIX': '[StartLinker] ',
    'RESEND_COOLDOWN_MINUTES': 5,
}