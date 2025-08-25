"""
Simple production settings for StartLinker
"""
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['13.50.234.250', 'localhost', '127.0.0.1']

# Simple database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'startlinker_db',
        'USER': 'startlinker',
        'PASSWORD': '7_v0fwth0EwUuzmt0qIvHmJdD8QhWS_jQ0X33HE46cI',
        'HOST': 'startlinker-db-production-free.cc34a8mii33o.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/opt/startlinker/staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/opt/startlinker/media'

# Security
SECRET_KEY = 'qR9fK2mN8pL5xW7vB3hJ6tY4aZ1sD0eC9uF8gH3kM2nX5wQ7vP'

# Remove problematic apps for now
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'taggit',
    'apps.core',
    'apps.users',
    'apps.startups',
    'apps.jobs',
    'apps.posts',
    'apps.notifications',
    'apps.subscriptions',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://13.50.234.250",
    "http://localhost:3000",
]

ROOT_URLCONF = 'startup_hub.urls'
WSGI_APPLICATION = 'startup_hub.wsgi.application'