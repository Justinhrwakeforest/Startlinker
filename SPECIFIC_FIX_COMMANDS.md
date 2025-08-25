# SPECIFIC FIX COMMANDS - Django URL Routing

Based on server analysis, Django is running but URL routing is broken. Here are the EXACT commands to fix it:

## Step 1: Access Server (AWS Console)
1. Go to **AWS EC2 Console** → Your instance → **Connect** → **Session Manager**
2. Click **Connect** (opens browser terminal)

## Step 2: Diagnose Current State

Run these commands to see what's actually there:

```bash
# Navigate to Django project
cd /var/www/startlinker
pwd

# Check directory structure  
ls -la

# Check if our apps exist
ls -la apps/ 2>/dev/null || echo "Apps directory not found"

# Check current URL configuration
cat startup_hub/urls.py 2>/dev/null || echo "urls.py not found"

# Check what's in settings
cat startup_hub/settings.py | grep INSTALLED_APPS -A 10 2>/dev/null || echo "settings.py not found"

# Check what Django thinks is installed
python3 manage.py diffsettings | grep INSTALLED_APPS || echo "Django not properly configured"
```

## Step 3: Fix Based on What You Find

### Scenario A: If apps/ directory EXISTS

```bash
# Check what apps are there
ls -la apps/

# Create missing URL files for each app
# Users app URLs
sudo mkdir -p apps/users
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

# Posts app URLs  
sudo mkdir -p apps/posts
sudo tee apps/posts/urls.py > /dev/null << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PostViewSet.as_view({'get': 'list', 'post': 'create'}), name='posts'),
]
EOF

# Startups app URLs
sudo mkdir -p apps/startups  
sudo tee apps/startups/urls.py > /dev/null << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.StartupViewSet.as_view({'get': 'list', 'post': 'create'}), name='startups'),
]
EOF

# Jobs app URLs
sudo mkdir -p apps/jobs
sudo tee apps/jobs/urls.py > /dev/null << 'EOF' 
from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobViewSet.as_view({'get': 'list', 'post': 'create'}), name='jobs'),
]
EOF

# Fix main URLs
sudo tee startup_hub/urls.py > /dev/null << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({"message": "StartLinker API", "version": "1.0", "status": "running"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/posts/', include('apps.posts.urls')),
    path('api/v1/startups/', include('apps.startups.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
]
EOF
```

### Scenario B: If apps/ directory DOES NOT EXIST

```bash
# Create the full app structure
sudo mkdir -p apps/{users,posts,startups,jobs}

# Create __init__.py files
sudo touch apps/__init__.py
sudo touch apps/users/__init__.py
sudo touch apps/posts/__init__.py  
sudo touch apps/startups/__init__.py
sudo touch apps/jobs/__init__.py

# Create basic views for users app
sudo tee apps/users/views.py > /dev/null << 'EOF'
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class UserLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(username=email, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {'id': user.id, 'email': user.email, 'username': user.username}
            })
        return Response({'error': 'Invalid credentials'}, status=400)

class UserRegistrationView(APIView):
    def post(self, request):
        return Response({'message': 'Registration endpoint'})

class UserLogoutView(APIView): 
    def post(self, request):
        return Response({'message': 'Logged out'})

class UserProfileView(APIView):
    def get(self, request):
        return Response({'message': 'Profile endpoint'})
EOF

# Create basic views for other apps
sudo tee apps/posts/views.py > /dev/null << 'EOF'
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

class PostViewSet(ViewSet):
    def list(self, request):
        return Response({'posts': []})
    
    def create(self, request):
        return Response({'message': 'Post created'})
EOF

sudo tee apps/startups/views.py > /dev/null << 'EOF'
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

class StartupViewSet(ViewSet):
    def list(self, request):
        return Response({'startups': []})
    
    def create(self, request):
        return Response({'message': 'Startup created'})
EOF

sudo tee apps/jobs/views.py > /dev/null << 'EOF'
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

class JobViewSet(ViewSet):
    def list(self, request):
        return Response({'jobs': []})
    
    def create(self, request):
        return Response({'message': 'Job created'})
EOF

# Create URL files (same as Scenario A above)
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

# (Repeat for other apps as in Scenario A)
```

## Step 4: Create Test User

```bash
# Create superuser and test user
python3 manage.py shell << 'EOF'
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create test user
try:
    user = User.objects.filter(username='test@startlinker.com').first()
    if not user:
        user = User.objects.create_user(
            username='test@startlinker.com',
            email='test@startlinker.com',
            password='Test@123456'
        )
    else:
        user.set_password('Test@123456') 
        user.save()
    
    token, created = Token.objects.get_or_create(user=user)
    print(f'User: {user.username}')
    print(f'Token: {token.key}')
except Exception as e:
    print(f'Error: {e}')
EOF
```

## Step 5: Restart and Test

```bash
# Restart Django
sudo systemctl restart gunicorn

# Wait a moment
sleep 2

# Test endpoints
echo "Testing API root:"
curl http://localhost/api/

echo -e "\nTesting login:"
curl -X POST http://localhost/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'

echo -e "\nTesting posts:"
curl http://localhost/api/v1/posts/
```

## Step 6: Check Logs If Still Not Working

```bash
# Check Django/Gunicorn logs
sudo journalctl -u gunicorn -n 20

# Check nginx logs  
sudo tail -10 /var/log/nginx/error.log

# Test Django directly (bypass nginx)
curl http://127.0.0.1:8000/api/v1/auth/login/
```

## Expected Results After Fix

You should see:
- `curl http://localhost/api/` → `{"message": "StartLinker API", "version": "1.0", "status": "running"}`
- Login should return user data and token
- Frontend at http://44.219.216.107 should be able to login

## If You Get Errors

Common issues and fixes:

1. **"No module named 'apps'"**
   ```bash
   sudo touch apps/__init__.py
   sudo systemctl restart gunicorn
   ```

2. **"URLconf doesn't define any patterns"**
   - Check that all URLs files were created properly
   - Verify syntax in urls.py files

3. **"ModuleNotFoundError: No module named 'rest_framework'"**
   ```bash
   sudo pip3 install djangorestframework
   sudo systemctl restart gunicorn
   ```

Run these commands step by step and let me know what you find at each stage!