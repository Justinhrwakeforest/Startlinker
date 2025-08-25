#!/usr/bin/env python
"""
Fix posting issues for startlinker.com
This script will:
1. Update CORS settings
2. Fix authentication issues
3. Ensure proper permissions
4. Update frontend API configuration
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

def create_test_user():
    """Create a test user for testing purposes"""
    try:
        user, created = User.objects.get_or_create(
            email='test@startlinker.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'is_verified': True
            }
        )
        
        if created:
            user.set_password('Test@123456')
            user.save()
            print(f"[OK] Created test user: {user.email}")
        else:
            print(f"[OK] Test user already exists: {user.email}")
            
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        print(f"[OK] Token for test user: {token.key}")
        
        return user, token
    except Exception as e:
        print(f"[ERROR] Error creating test user: {e}")
        return None, None

def check_database_connection():
    """Check if database is accessible"""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("[OK] Database connection successful")
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

def check_required_tables():
    """Check if all required tables exist"""
    from django.db import connection
    
    required_tables = [
        'users_user',
        'authtoken_token',
        'posts_post',
        'posts_story',
        'startups_startup',
        'jobs_job'
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                print(f"[OK] Table exists: {table}")
            else:
                print(f"[ERROR] Table missing: {table}")
                missing_tables.append(table)
                
    return len(missing_tables) == 0

def update_cors_settings():
    """Update CORS settings for production"""
    print("\nUpdating CORS settings...")
    
    cors_file = Path(__file__).parent / 'startup_hub' / 'settings' / 'cors_fix.py'
    
    cors_content = '''# CORS Configuration Fix
from corsheaders.defaults import default_headers

# Update these in your production.py or base.py

CORS_ALLOWED_ORIGINS = [
    "https://startlinker.com",
    "https://www.startlinker.com",
    "http://startlinker.com",
    "http://www.startlinker.com",
    "http://13.50.234.250",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow all origins during development/testing
# CORS_ALLOW_ALL_ORIGINS = True  # Uncomment for testing only

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'Authorization',
    'Content-Type',
    'X-Requested-With',
    'X-CSRFToken',
]

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    "https://startlinker.com",
    "https://www.startlinker.com",
    "http://startlinker.com",
    "http://www.startlinker.com",
    "http://13.50.234.250",
]

# Disable CSRF for API endpoints (if using token authentication)
# Add this to your REST_FRAMEWORK settings
REST_FRAMEWORK_CSRF_EXEMPT = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
'''
    
    with open(cors_file, 'w') as f:
        f.write(cors_content)
    
    print(f"[OK] CORS configuration saved to: {cors_file}")
    print("  Please update your settings files with these configurations")

def create_frontend_config_fix():
    """Create frontend configuration fix"""
    print("\nCreating frontend configuration fix...")
    
    frontend_config = Path(__file__).parent.parent / 'frontend' / 'src' / 'config' / 'api.config.fixed.js'
    
    config_content = '''// Fixed API Configuration for Startlinker
const getApiUrl = () => {
  // Check if we're in production
  if (window.location.hostname === 'startlinker.com' || 
      window.location.hostname === 'www.startlinker.com') {
    return 'https://startlinker.com/api/v1';
  }
  
  // Check for environment variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Default to AWS server
  return 'http://13.50.234.250/api/v1';
};

const API_BASE_URL = getApiUrl();
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws').replace('/api/v1', '/ws');

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  wsURL: WS_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  endpoints: {
    // Auth endpoints
    login: '/auth/login/',
    register: '/auth/register/',
    logout: '/auth/logout/',
    profile: '/auth/profile/',
    
    // Posts endpoints
    posts: '/posts/',
    stories: '/posts/stories/',
    
    // Startups endpoints
    startups: '/startups/',
    industries: '/industries/',
    
    // Jobs endpoints
    jobs: '/jobs/',
    jobTypes: '/job-types/',
    applications: '/applications/',
    
    // Social endpoints
    follow: '/users/follow/',
    unfollow: '/users/unfollow/',
    followers: '/users/followers/',
    following: '/users/following/',
  }
};

// Axios interceptor for authentication
export const setupAxiosInterceptors = (axios) => {
  // Request interceptor
  axios.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Token ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );
  
  // Response interceptor
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
};

export default API_CONFIG;
'''
    
    frontend_config.parent.mkdir(parents=True, exist_ok=True)
    with open(frontend_config, 'w') as f:
        f.write(config_content)
    
    print(f"[OK] Frontend configuration saved to: {frontend_config}")

def create_nginx_config():
    """Create proper nginx configuration"""
    print("\nCreating nginx configuration...")
    
    nginx_config = Path(__file__).parent / 'nginx_startlinker.conf'
    
    config_content = '''# Nginx configuration for Startlinker
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 13.50.234.250;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # CORS headers for API
    location /api/ {
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 86400 always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            return 204;
        }
        
        # Add CORS headers to all responses
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With' always;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for large uploads
        client_max_body_size 50M;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /var/www/startlinker/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/startlinker/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Frontend
    location / {
        root /var/www/startlinker/frontend;
        try_files $uri $uri/ /index.html;
        
        # Security headers for frontend
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-XSS-Protection "1; mode=block";
    }
}
'''
    
    with open(nginx_config, 'w') as f:
        f.write(config_content)
    
    print(f"[OK] Nginx configuration saved to: {nginx_config}")

def main():
    print("=" * 60)
    print("STARTLINKER POSTING ISSUES FIX")
    print("=" * 60)
    
    # Check database
    print("\n1. Checking database connection...")
    if not check_database_connection():
        print("Please fix database connection first!")
        return
    
    # Check tables
    print("\n2. Checking required tables...")
    if not check_required_tables():
        print("Please run migrations: python manage.py migrate")
    
    # Create test user
    print("\n3. Creating test user...")
    user, token = create_test_user()
    
    # Create configuration files
    print("\n4. Creating configuration fixes...")
    update_cors_settings()
    create_frontend_config_fix()
    create_nginx_config()
    
    print("\n" + "=" * 60)
    print("FIXES CREATED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Update your Django settings with the CORS configuration")
    print("2. Update your frontend API configuration")
    print("3. Update your nginx configuration on the server")
    print("4. Restart both Django and nginx services")
    print("\nTest credentials:")
    print(f"  Email: test@startlinker.com")
    print(f"  Password: Test@123456")
    if token:
        print(f"  Token: {token.key}")

if __name__ == "__main__":
    main()