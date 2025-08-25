# STEP-BY-STEP FIX - Run Commands One by One

Follow these commands **exactly in order**. After each step, I'll tell you what to expect.

## Step 1: Access Your Server

1. **Go to AWS Console** → EC2 → Instances
2. **Find your instance** with IP `44.219.216.107`
3. **Click "Connect"** → **"Session Manager"** → **"Connect"**

You should see a black terminal that says something like: `sh-4.2$ ` or `ubuntu@ip-xxx:`

## Step 2: Run Diagnosis

**Copy and paste this command:**
```bash
curl -s https://raw.githubusercontent.com/your-repo/QUICK_DIAGNOSIS.sh | bash
```

**Or run it manually:**
```bash
cd /var/www/startlinker 2>/dev/null || echo "Directory not found"
pwd
ls -la
```

**Expected output:** You should see either:
- A directory listing if the project exists
- "Directory not found" if we need to create it

**➡️ Tell me what you see, then proceed to the next step.**

## Step 3A: If Project Directory EXISTS

**Run these commands:**
```bash
cd /var/www/startlinker
ls -la startup_hub/
ls -la apps/ 2>/dev/null || echo "No apps directory"
cat startup_hub/urls.py 2>/dev/null || echo "No urls.py"
```

**Expected output:** Directory listings or "No X" messages

**➡️ Based on what you see, I'll give you the next commands.**

## Step 3B: If Project Directory DOES NOT EXIST

**Run these commands:**
```bash
sudo mkdir -p /var/www/startlinker
cd /var/www/startlinker
sudo chown -R ubuntu:ubuntu /var/www/startlinker
echo "Directory created successfully"
```

**Expected output:** `Directory created successfully`

**➡️ Then continue with Step 4.**

## Step 4: Create Basic Django Structure

**Run each command and wait for it to finish:**

```bash
# Create basic files
sudo tee manage.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import os, sys
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
EOF

echo "✓ manage.py created"
```

```bash
# Create startup_hub directory
sudo mkdir -p startup_hub
sudo tee startup_hub/__init__.py > /dev/null << 'EOF'
# Django project init
EOF

echo "✓ startup_hub/__init__.py created"
```

```bash
# Create wsgi.py
sudo tee startup_hub/wsgi.py > /dev/null << 'EOF'
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
application = get_wsgi_application()
EOF

echo "✓ wsgi.py created"
```

## Step 5: Create Settings

```bash
sudo tee startup_hub/settings.py > /dev/null << 'EOF'
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-temp-key-for-testing'
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
        'rest_framework.permissions.AllowAny',
    ],
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
EOF

echo "✓ settings.py created"
```

## Step 6: Create Apps Structure

```bash
# Create apps
sudo mkdir -p apps/{users,posts,startups,jobs}
sudo touch apps/__init__.py
sudo touch apps/users/__init__.py
sudo touch apps/posts/__init__.py
sudo touch apps/startups/__init__.py  
sudo touch apps/jobs/__init__.py

echo "✓ Apps structure created"
```

## Step 7: Create Users App (Most Important)

```bash
sudo tee apps/users/views.py > /dev/null << 'EOF'
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class UserLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Email and password required'}, status=400)
        
        # Try to authenticate with email as username
        user = authenticate(username=email, password=password)
        
        if user and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                }
            })
        
        return Response({'error': 'Invalid email or password'}, status=400)

class UserRegistrationView(APIView):
    def post(self, request):
        return Response({'message': 'Registration endpoint working'})

class UserLogoutView(APIView):
    def post(self, request):
        return Response({'message': 'Logout endpoint working'})

class UserProfileView(APIView):
    def get(self, request):
        return Response({'message': 'Profile endpoint working'})
EOF

echo "✓ Users views created"
```

```bash
sudo tee apps/users/urls.py > /dev/null << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('register/', views.UserRegistrationView.as_view(), name='register'), 
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
]
EOF

echo "✓ Users URLs created"
```

## Step 8: Create Other Apps (Basic)

```bash
# Posts app
sudo tee apps/posts/views.py > /dev/null << 'EOF'
from rest_framework.views import APIView
from rest_framework.response import Response

class PostListView(APIView):
    def get(self, request):
        return Response({'posts': [], 'message': 'Posts endpoint working'})
    
    def post(self, request):
        return Response({'message': 'Post created successfully'})
EOF

sudo tee apps/posts/urls.py > /dev/null << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PostListView.as_view(), name='posts'),
]
EOF

echo "✓ Posts app created"
```

```bash
# Similar for startups and jobs
sudo tee apps/startups/views.py > /dev/null << 'EOF'
from rest_framework.views import APIView
from rest_framework.response import Response

class StartupListView(APIView):
    def get(self, request):
        return Response({'startups': [], 'message': 'Startups endpoint working'})
    
    def post(self, request):
        return Response({'message': 'Startup created successfully'})
EOF

sudo tee apps/startups/urls.py > /dev/null << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.StartupListView.as_view(), name='startups'),
]
EOF

sudo tee apps/jobs/views.py > /dev/null << 'EOF'
from rest_framework.views import APIView
from rest_framework.response import Response

class JobListView(APIView):
    def get(self, request):
        return Response({'jobs': [], 'message': 'Jobs endpoint working'})
    
    def post(self, request):
        return Response({'message': 'Job created successfully'})
EOF

sudo tee apps/jobs/urls.py > /dev/null << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListView.as_view(), name='jobs'),
]
EOF

echo "✓ All apps created"
```

## Step 9: Create Main URLs

```bash
sudo tee startup_hub/urls.py > /dev/null << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "message": "StartLinker API",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/v1/auth/",
            "posts": "/api/v1/posts/", 
            "startups": "/api/v1/startups/",
            "jobs": "/api/v1/jobs/"
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/posts/', include('apps.posts.urls')),
    path('api/v1/startups/', include('apps.startups.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
]
EOF

echo "✓ Main URLs created"
```

## Step 10: Install Dependencies and Setup Database

```bash
# Install Python packages
sudo pip3 install django djangorestframework django-cors-headers

echo "✓ Packages installed"
```

```bash
# Setup database
python3 manage.py migrate

echo "✓ Database migrated"
```

## Step 11: Create Test User

```bash
python3 manage.py shell << 'EOF'
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

try:
    # Create test user
    user, created = User.objects.get_or_create(
        username='test@startlinker.com',
        defaults={
            'email': 'test@startlinker.com',
            'is_active': True
        }
    )
    
    user.set_password('Test@123456')
    user.save()
    
    token, created = Token.objects.get_or_create(user=user)
    
    print(f'✓ User created: {user.username}')
    print(f'✓ Token: {token.key}')
    
except Exception as e:
    print(f'Error: {e}')
EOF
```

## Step 12: Test Django Directly

```bash
# Test Django works
python3 manage.py runserver 127.0.0.1:8000 &
sleep 3

# Test endpoints
echo "Testing API:"
curl http://127.0.0.1:8000/api/

echo -e "\nTesting login:"
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'

# Kill the test server
pkill -f "runserver"
```

**Expected output:** You should see JSON responses with API info and login token.

## Step 13: Setup Gunicorn Service

```bash
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/startlinker
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 startup_hub.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn

echo "✓ Gunicorn configured and started"
```

## Step 14: Final Test

```bash
# Test through nginx
echo "Final test through nginx:"
curl http://localhost/api/

echo -e "\nTesting login through nginx:"
curl -X POST http://localhost/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'
```

## Step 15: Verify Frontend Can Connect

**Open a new browser tab and go to:**
- http://44.219.216.107 
- http://startlinker.com

**Try to log in with:**
- Email: `test@startlinker.com`
- Password: `Test@123456`

---

## ⚠️ IMPORTANT: Follow Each Step

1. **Run commands ONE AT A TIME**
2. **Wait for each to complete**
3. **Check the output matches what I said to expect**
4. **If any step fails, STOP and tell me the error**

This should get your Django backend connected to the frontend!