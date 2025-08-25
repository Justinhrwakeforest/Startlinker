# Base settings for StartupHub
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'channels',
    
    # Local apps
    'apps.core',
    'apps.users',
    'apps.startups',
    'apps.notifications',
    'apps.jobs',
    'apps.posts',
    'apps.connect',
    'apps.messaging',
    'apps.reports',
    # 'apps.subscriptions',  # Removed - contains Stripe functionality
    # 'apps.analysis',       # Removed - contains pitch deck analysis
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'startup_hub.urls'

# Enable APPEND_SLASH for proper URL handling
APPEND_SLASH = True

# Channels ASGI application
ASGI_APPLICATION = 'startup_hub.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
# This will be overridden in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# User model
AUTH_USER_MODEL = 'users.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'delete-old-pitch-decks': {
        'task': 'apps.analysis.tasks.delete_old_pitch_decks',
        'schedule': 60 * 60 * 24,  # Run daily
    },
}

# Analysis Settings
ANALYSIS_SETTINGS = {
    'MAX_FILE_SIZE_MB': 25,
    'ALLOWED_FILE_TYPES': ['pdf'],
    'FILE_RETENTION_DAYS': 7,
    'AI_PROVIDER': os.environ.get('AI_PROVIDER', 'openai'),
    'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
    'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', ''),
}

# Job Settings
JOB_SETTINGS = {
    'REQUIRE_REVIEW': os.environ.get('REQUIRE_JOB_REVIEW', 'False') == 'True',
    'MAX_JOBS_PER_USER_PER_DAY': int(os.environ.get('MAX_JOBS_PER_USER_PER_DAY', '3')),
}

# Subscription Settings
SUBSCRIPTION_SETTINGS = {
    'TRIAL_PERIOD_DAYS': 14,
    'ALLOW_PLAN_CHANGES': True,
    'PRORATE_CHANGES': True,
    'SEND_INVOICE_EMAILS': True,
    'SEND_RECEIPT_EMAILS': True,
    'GRACE_PERIOD_DAYS': 3,
    'MAX_RETRY_ATTEMPTS': 3,
    'WEBHOOK_TOLERANCE': 300,
}

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.EmailBackend',  # Custom email authentication
    'django.contrib.auth.backends.ModelBackend',  # Fallback to default
]

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@startlinker.com')

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Configure Stripe
if STRIPE_SECRET_KEY:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

# Import WebRTC configuration
from .webrtc import WEBRTC_CONFIG, WEBRTC_MEDIA_CONSTRAINTS