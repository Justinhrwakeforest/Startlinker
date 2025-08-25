# Database optimization settings

import os

# Database configuration with optimizations
DATABASE_CONFIG = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'startup_hub'),
        'USER': os.environ.get('DB_USER', 'startup_hub'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'OPTIONS': {
                'sslmode': 'require',
            }
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Database connection pooling
DATABASE_POOL_CONFIG = {
    'default': {
        'ENGINE': 'django_postgres_pool',
        'NAME': os.environ.get('DB_NAME', 'startup_hub'),
        'USER': os.environ.get('DB_USER', 'startup_hub'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
            'OPTIONS': {
                'sslmode': 'require',
            }
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}