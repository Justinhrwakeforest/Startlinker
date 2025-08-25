# Upload Django Code via GitHub (No SSH Required)

If you can't find your Django project on the server, here's how to get it there without SSH keys:

## Option 1: GitHub Upload (Recommended)

### Step 1: Push Code to GitHub (on your local machine)
```cmd
REM Initialize git if not already done
git init
git add .
git commit -m "Django backend with fixes"

REM Push to GitHub (create a new repo or use existing)
git remote add origin https://github.com/yourusername/startlinker-backend.git
git push -u origin main
```

### Step 2: Download on Server (in AWS Session Manager)
```bash
# Install git if not available
sudo apt update
sudo apt install -y git

# Clone your repository
cd /var/www
sudo git clone https://github.com/yourusername/startlinker-backend.git startlinker

# Set permissions
sudo chown -R ubuntu:www-data /var/www/startlinker
cd /var/www/startlinker
```

## Option 2: Copy-Paste Method

### Step 1: Create Minimal Django Setup on Server
```bash
cd /var/www/startlinker

# Create Django project structure
sudo mkdir -p apps/{users,posts,startups,jobs}
sudo mkdir -p startup_hub/settings
sudo touch manage.py
```

### Step 2: Copy Key Files (copy-paste content)

**Create manage.py:**
```bash
sudo tee manage.py > /dev/null << 'EOF'
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)
EOF
```

**Create startup_hub/wsgi.py:**
```bash
sudo tee startup_hub/wsgi.py > /dev/null << 'EOF'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
application = get_wsgi_application()
EOF
```

**Create startup_hub/__init__.py:**
```bash
sudo touch startup_hub/__init__.py
```

**Create startup_hub/urls.py:**
```bash
sudo tee startup_hub/urls.py > /dev/null << 'EOF'
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/posts/', include('apps.posts.urls')),
    path('api/v1/startups/', include('apps.startups.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
]
EOF
```

### Step 3: Create Settings (copy from your local files)

You'll need to copy your settings files. I'll create a simple one:

```bash
sudo tee startup_hub/settings.py > /dev/null << 'EOF'
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-change-this'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'apps.users',
    'apps.posts',
    'apps.startups',
    'apps.jobs',
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

ROOT_URLCONF = 'startup_hub.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

AUTH_USER_MODEL = 'users.User'
EOF
```

## Option 3: Use AWS CodeCommit

If GitHub isn't preferred:
1. Create AWS CodeCommit repository
2. Push code there
3. Clone on server using IAM roles

## After Uploading Code

Once your Django code is on the server, continue with the main connection commands from `CONNECT_DJANGO_COMMANDS.md`.

## Quick Test

To verify your Django setup is working:
```bash
cd /var/www/startlinker
python3 manage.py migrate
python3 manage.py runserver 127.0.0.1:8000
```

Then test: `curl http://127.0.0.1:8000/`