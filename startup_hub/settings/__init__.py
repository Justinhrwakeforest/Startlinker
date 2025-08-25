# Settings module selector
import os

# Default to development settings
DJANGO_SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')

if DJANGO_SETTINGS_MODULE == 'startup_hub.settings.production':
    from .production import *
elif DJANGO_SETTINGS_MODULE == 'startup_hub.settings.development':
    from .development import *
else:
    from .development import *