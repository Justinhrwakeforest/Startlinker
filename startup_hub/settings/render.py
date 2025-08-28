"""
Production settings for Render deployment
"""

import os
import dj_database_url
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Get secret key from environment
SECRET_KEY = os.environ.get('SECRET_KEY')

# Allow Render hostnames and custom domain
ALLOWED_HOSTS = [
    'startlinker.com',
    'www.startlinker.com',
    '.onrender.com',
    'startlinker-backend.onrender.com', 
    'startlinker.onrender.com',
    'localhost', 
    '127.0.0.1'
]

# Add additional hosts from environment
additional_hosts = os.environ.get('ALLOWED_HOSTS', '')
if additional_hosts:
    ALLOWED_HOSTS.extend(additional_hosts.split(','))

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# Static files configuration for Render
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Use WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise to middleware if not already present
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS settings - updated for our deployment
CORS_ALLOWED_ORIGINS = [
    "https://startlinker.com",
    "https://www.startlinker.com", 
    "https://startlinker.onrender.com",
    "https://startlinker-frontend.onrender.com",
    "http://localhost:3000",
]

# Always allow all origins in debug mode or with CORS_DEBUG
if os.environ.get('CORS_DEBUG', 'False').lower() == 'true' or DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    print("⚠️  WARNING: CORS_DEBUG enabled - allowing all origins!")
else:
    CORS_ALLOW_ALL_ORIGINS = False

# Add additional CORS origins from environment
additional_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if additional_origins:
    CORS_ALLOWED_ORIGINS.extend(additional_origins.split(','))

# More permissive CORS settings for debugging
CORS_ALLOW_CREDENTIALS = True

# Allow all common methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS', 
    'PATCH',
    'POST',
    'PUT',
]

# Allow all common headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Add preflight max age
CORS_PREFLIGHT_MAX_AGE = 86400

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://startlinker.com",
    "https://www.startlinker.com",
    "https://startlinker.onrender.com",
    "https://startlinker-frontend.onrender.com", 
    "https://startlinker-backend.onrender.com",
]

# Add additional CSRF trusted origins from environment
additional_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if additional_csrf_origins:
    CSRF_TRUSTED_ORIGINS.extend(additional_csrf_origins.split(','))

# Security settings - can be overridden by environment variables
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').lower() == 'true'

# Additional CSRF settings for debugging
CSRF_COOKIE_SAMESITE = 'Lax'  # Changed from 'Strict' to allow cross-site requests
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read the cookie
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# SendGrid Email Configuration for Render
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'apps.users.sendgrid_backend.SendGridBackend'
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@startlinker.com')
    EMAIL_HOST_USER = DEFAULT_FROM_EMAIL
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False
else:
    # Fallback email configuration
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Email verification settings
EMAIL_VERIFICATION_SETTINGS = {
    'VERIFICATION_TOKEN_EXPIRY_HOURS': 24,
    'FROM_EMAIL': DEFAULT_FROM_EMAIL,
    'SUBJECT_PREFIX': '[StartLinker] ',
    'RESEND_COOLDOWN_MINUTES': 5,
}

# Enforce email verification in production
REQUIRE_EMAIL_VERIFICATION = True

# Frontend URL for email verification links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://startlinker-frontend.onrender.com')
