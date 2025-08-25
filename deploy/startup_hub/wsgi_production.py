# WSGI config for StartupHub production environment

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
os.environ.setdefault('DJANGO_ENVIRONMENT', 'production')

# Get the WSGI application
application = get_wsgi_application()

# Add whitenoise for static files serving
from whitenoise import WhiteNoise
application = WhiteNoise(application)

# For development, you might want to serve static files
if os.environ.get('SERVE_STATIC_FILES') == 'True':
    application.add_files('/var/www/static', prefix='/static/')
    application.add_files('/var/www/media', prefix='/media/')