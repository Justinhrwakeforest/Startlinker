# Development settings for StartupHub
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

# Fallback to InMemoryChannelLayer if Redis is not available
try:
    import redis
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    r.ping()
except:
    print("Redis not available, falling back to InMemoryChannelLayer")
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Development logging
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
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'startup_hub': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Development settings
if DEBUG:
    # Enable Django Debug Toolbar if installed
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
            'SHOW_COLLAPSED': True,
        }
        
        INTERNAL_IPS = [
            '127.0.0.1',
            'localhost',
        ]
    except ImportError:
        pass

# Force disable SSL redirect for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Job posting settings - Require admin approval for all jobs
JOB_POSTING_SETTINGS = {
    'AUTO_APPROVE': False,  # Jobs require admin approval
    'REQUIRE_REVIEW': True,  # Force all jobs to go through review
    'AUTO_APPROVE_STAFF': False,  # Even staff jobs require approval
    'AUTO_APPROVE_VERIFIED_STARTUPS': False,  # Even verified startups require approval
}

# Ensure required directories exist
for directory in [MEDIA_ROOT, STATIC_ROOT, BASE_DIR / 'logs']:
    os.makedirs(directory, exist_ok=True)