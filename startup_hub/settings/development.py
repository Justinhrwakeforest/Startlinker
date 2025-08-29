# Development settings for StartupHub
from .base import *
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - PostgreSQL Configuration
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
        # DISABLED - causing URL namespace issues
        # INSTALLED_APPS.append('debug_toolbar')
        # MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: False,  # Disable for now
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

# Email Configuration for Development
# SendGrid Configuration with improved backend
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'apps.users.working_sendgrid_backend.WorkingSendGridBackend'
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False  # Set to False to actually send emails
    DEFAULT_FROM_EMAIL = 'noreply@startlinker.com'
    EMAIL_HOST_USER = DEFAULT_FROM_EMAIL
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    
    # Frontend URL for email links
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
else:
    # Fallback to console backend if no SendGrid API key
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@startlinker.com'
    EMAIL_HOST_USER = DEFAULT_FROM_EMAIL
    print("WARNING: No SENDGRID_API_KEY found, using console email backend")

# Alternative: Use file backend to save emails to files (uncomment to use)
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = BASE_DIR / 'emails'

# Email verification settings
EMAIL_VERIFICATION_SETTINGS = {
    'VERIFICATION_TOKEN_EXPIRY_HOURS': 24,  # Token expires after 24 hours
    'FROM_EMAIL': DEFAULT_FROM_EMAIL,
    'SUBJECT_PREFIX': '[StartLinker] ',
    'RESEND_COOLDOWN_MINUTES': 5,  # Minimum time between verification emails
}

# Ensure required directories exist
for directory in [MEDIA_ROOT, STATIC_ROOT, BASE_DIR / 'logs']:
    os.makedirs(directory, exist_ok=True)