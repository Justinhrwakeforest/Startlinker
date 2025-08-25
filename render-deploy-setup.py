#!/usr/bin/env python3
"""
Render Deployment Setup
Prepares both frontend and backend for deployment on Render
"""

import os
import json
import time
import shutil
from pathlib import Path

def create_backend_render_config():
    """Create Render configuration for Django backend"""
    print("🔧 Creating Backend Render Configuration")
    print("=" * 50)
    
    # Create render.yaml for backend
    render_config = {
        "services": [
            {
                "type": "web",
                "name": "startup-hub-backend",
                "env": "python",
                "plan": "starter",
                "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic --noinput",
                "startCommand": "gunicorn startup_hub.wsgi:application",
                "envVars": [
                    {
                        "key": "PYTHON_VERSION",
                        "value": "3.11"
                    },
                    {
                        "key": "DJANGO_SETTINGS_MODULE",
                        "value": "startup_hub.settings.production"
                    },
                    {
                        "key": "SECRET_KEY",
                        "generateValue": True
                    },
                    {
                        "key": "DEBUG",
                        "value": "False"
                    },
                    {
                        "key": "ALLOWED_HOSTS",
                        "value": ".onrender.com"
                    },
                    {
                        "key": "DATABASE_URL",
                        "fromService": {
                            "type": "pserv",
                            "name": "startup-hub-db"
                        }
                    }
                ]
            },
            {
                "type": "pserv",
                "name": "startup-hub-db",
                "env": "postgresql",
                "plan": "starter"
            }
        ]
    }
    
    with open('render.yaml', 'w') as f:
        json.dump(render_config, f, indent=2)
    
    print("✅ Created render.yaml for backend")
    
    # Create requirements.txt for Render
    requirements = [
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.3.1",
        "psycopg2-binary==2.9.7",
        "gunicorn==21.2.0",
        "whitenoise==6.5.0",
        "python-decouple==3.8",
        "Pillow==10.0.1",
        "celery==5.3.4",
        "redis==5.0.1",
        "django-filter==23.3",
        "django-storages==1.14.2",
        "boto3==1.34.0"
    ]
    
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))
    
    print("✅ Created requirements.txt for Render")
    
    # Create build.sh for backend
    build_script = '''#!/usr/bin/env bash
# Build script for Render
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
'''
    
    with open('build.sh', 'w') as f:
        f.write(build_script)
    
    print("✅ Created build.sh for backend")

def create_frontend_render_config():
    """Create Render configuration for React frontend"""
    print("\n🌐 Creating Frontend Render Configuration")
    print("=" * 50)
    
    # Create package.json for frontend if it doesn't exist
    frontend_dir = Path("../frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return
    
    # Create render.yaml for frontend
    frontend_render_config = {
        "services": [
            {
                "type": "web",
                "name": "startup-hub-frontend",
                "env": "static",
                "plan": "starter",
                "buildCommand": "npm install && npm run build",
                "staticPublishPath": "./build",
                "envVars": [
                    {
                        "key": "REACT_APP_API_URL",
                        "value": "https://startup-hub-backend.onrender.com"
                    },
                    {
                        "key": "REACT_APP_BACKEND_URL",
                        "value": "https://startup-hub-backend.onrender.com"
                    }
                ]
            }
        ]
    }
    
    with open('../frontend/render.yaml', 'w') as f:
        json.dump(frontend_render_config, f, indent=2)
    
    print("✅ Created render.yaml for frontend")
    
    # Update frontend package.json for Render
    package_json_path = frontend_dir / "package.json"
    if package_json_path.exists():
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        # Add homepage for Render
        package_data["homepage"] = "https://startup-hub-frontend.onrender.com"
        
        with open(package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        print("✅ Updated package.json for Render")

def create_production_settings():
    """Create production settings for Django"""
    print("\n⚙️ Creating Production Settings")
    print("=" * 50)
    
    production_settings = '''"""
Production settings for Render deployment
"""

import os
import dj_database_url
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Get secret key from environment
SECRET_KEY = os.environ.get('SECRET_KEY')

# Allow Render hostnames
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://startup-hub-frontend.onrender.com",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

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

# Email configuration (if needed)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
'''
    
    settings_dir = Path("startup_hub/settings")
    if not settings_dir.exists():
        settings_dir.mkdir(parents=True)
    
    with open(settings_dir / "render.py", 'w') as f:
        f.write(production_settings)
    
    print("✅ Created render.py production settings")

def create_deployment_guide():
    """Create deployment guide"""
    print("\n📋 Creating Deployment Guide")
    print("=" * 50)
    
    guide = '''# 🚀 Render Deployment Guide

## 📋 Prerequisites
- Render account (free tier available)
- GitHub repository with your code

## 🔧 Backend Deployment (Django)

### Step 1: Connect Repository
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Select the repository containing your Django backend

### Step 2: Configure Backend Service
- **Name**: startup-hub-backend
- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Start Command**: `gunicorn startup_hub.wsgi:application`
- **Plan**: Starter (Free)

### Step 3: Environment Variables
Add these environment variables:
- `DJANGO_SETTINGS_MODULE`: startup_hub.settings.render
- `SECRET_KEY`: (auto-generated)
- `DEBUG`: False
- `ALLOWED_HOSTS`: .onrender.com

### Step 4: Database
1. Create a new PostgreSQL service
2. Name it: startup-hub-db
3. Copy the DATABASE_URL to your backend service

## 🌐 Frontend Deployment (React)

### Step 1: Connect Repository
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Static Site"
3. Connect your GitHub repository
4. Select the frontend directory

### Step 2: Configure Frontend Service
- **Name**: startup-hub-frontend
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: build
- **Plan**: Starter (Free)

### Step 3: Environment Variables
Add these environment variables:
- `REACT_APP_API_URL`: https://startup-hub-backend.onrender.com
- `REACT_APP_BACKEND_URL`: https://startup-hub-backend.onrender.com

## 🔗 Connect Services

### Update Frontend API Configuration
In your frontend code, update the API base URL to point to your Render backend:
```javascript
// In src/config/api.config.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://startup-hub-backend.onrender.com';
```

### Update CORS Settings
In your Django backend, ensure CORS allows your frontend domain:
```python
CORS_ALLOWED_ORIGINS = [
    "https://startup-hub-frontend.onrender.com",
]
```

## 🎉 Deployment Complete!

Your services will be available at:
- **Backend**: https://startup-hub-backend.onrender.com
- **Frontend**: https://startup-hub-frontend.onrender.com

## 🔧 Troubleshooting

### Backend Issues
- Check build logs in Render dashboard
- Verify environment variables are set correctly
- Ensure DATABASE_URL is properly configured

### Frontend Issues
- Check if API_URL is pointing to correct backend
- Verify build command completes successfully
- Check browser console for CORS errors

## 📞 Support
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com/
'''
    
    with open('RENDER_DEPLOYMENT_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("✅ Created RENDER_DEPLOYMENT_GUIDE.md")

def main():
    print("🚀 Render Deployment Setup")
    print("=" * 50)
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create backend configuration
    create_backend_render_config()
    
    # Create frontend configuration
    create_frontend_render_config()
    
    # Create production settings
    create_production_settings()
    
    # Create deployment guide
    create_deployment_guide()
    
    print("\n🎉 Render Deployment Setup Complete!")
    print("=" * 50)
    print("📁 Files created:")
    print("  🔧 render.yaml (backend)")
    print("  📦 requirements.txt (updated)")
    print("  🔨 build.sh (backend)")
    print("  🌐 ../frontend/render.yaml (frontend)")
    print("  ⚙️ startup_hub/settings/render.py")
    print("  📋 RENDER_DEPLOYMENT_GUIDE.md")
    print()
    print("🚀 Next Steps:")
    print("1. Push your code to GitHub")
    print("2. Follow the deployment guide")
    print("3. Deploy backend first, then frontend")
    print("4. Update frontend API URLs to point to backend")

if __name__ == "__main__":
    main()
