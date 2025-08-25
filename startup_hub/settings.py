# startup_hub/startup_hub/settings.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"Loading .env from: {BASE_DIR / '.env'}")
load_dotenv(BASE_DIR / '.env', verbose=True)

# Determine which settings module to use
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .settings.production import *
elif ENVIRONMENT == 'staging':
    from .settings.production import *
    DEBUG = True  # Enable debug for staging
else:
    from .settings.development import *