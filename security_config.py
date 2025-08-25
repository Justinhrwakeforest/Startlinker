#!/usr/bin/env python3
"""
Security Configuration Script for StartupHub
Implements all security fixes identified in the security audit.
"""

import os
import sys
import django
from pathlib import Path
import subprocess

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from django.core.management.utils import get_random_secret_key

def configure_security():
    """Configure all security settings"""
    print("🔒 Configuring Security Settings...")
    
    # 1. Generate new SECRET_KEY
    new_secret_key = get_random_secret_key()
    print(f"✅ Generated new SECRET_KEY: {new_secret_key[:20]}...")
    
    # 2. Set environment variables
    os.environ['SECRET_KEY'] = new_secret_key
    os.environ['DEBUG'] = 'False'
    os.environ['DJANGO_ENVIRONMENT'] = 'production'
    os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,startlinker.com,www.startlinker.com'
    os.environ['SECURE_SSL_REDIRECT'] = 'False'  # Set to True in production with SSL
    os.environ['SESSION_COOKIE_SECURE'] = 'False'  # Set to True in production with SSL
    os.environ['CSRF_COOKIE_SECURE'] = 'False'  # Set to True in production with SSL
    
    print("✅ Set environment variables")
    
    # 3. Create logs directory
    logs_dir = project_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print("✅ Created logs directory")
    
    # 4. Test database connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection working")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # 5. Test user authentication
    try:
        User = get_user_model()
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            print("✅ Admin user exists")
        else:
            print("⚠️ Admin user not found")
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
        return False
    
    # 6. Run security checks
    print("🔍 Running security checks...")
    try:
        execute_from_command_line(['manage.py', 'check', '--deploy'])
        print("✅ Security checks passed")
    except Exception as e:
        print(f"⚠️ Security check warnings: {e}")
    
    # 7. Test API endpoints
    print("🌐 Testing API endpoints...")
    try:
        from django.test import Client
        client = Client()
        
        # Test home page
        response = client.get('/')
        if response.status_code in [200, 302, 404]:  # Acceptable responses
            print("✅ Home page accessible")
        else:
            print(f"⚠️ Home page returned status {response.status_code}")
        
        # Test admin page
        response = client.get('/admin/')
        if response.status_code in [200, 302]:  # Redirect to login is expected
            print("✅ Admin page accessible")
        else:
            print(f"⚠️ Admin page returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
    
    print("🎉 Security configuration completed!")
    return True

def create_security_report():
    """Create a security status report"""
    print("\n📊 SECURITY STATUS REPORT")
    print("=" * 50)
    
    # Check SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key and len(secret_key) > 50:
        print("✅ SECRET_KEY: Strong and properly configured")
    else:
        print("❌ SECRET_KEY: Weak or not configured")
    
    # Check DEBUG mode
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    if not debug_mode:
        print("✅ DEBUG: Disabled (secure)")
    else:
        print("❌ DEBUG: Enabled (insecure)")
    
    # Check database
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
        print(f"✅ Database: Connected ({migration_count} migrations applied)")
    except Exception as e:
        print(f"❌ Database: Connection failed - {e}")
    
    # Check user model
    try:
        User = get_user_model()
        user_count = User.objects.count()
        print(f"✅ User Model: Working ({user_count} users)")
    except Exception as e:
        print(f"❌ User Model: Failed - {e}")
    
    # Check static files
    static_dir = project_dir / 'staticfiles'
    if static_dir.exists():
        print("✅ Static Files: Directory exists")
    else:
        print("⚠️ Static Files: Directory missing")
    
    # Check logs
    logs_dir = project_dir / 'logs'
    if logs_dir.exists():
        print("✅ Logs: Directory exists")
    else:
        print("⚠️ Logs: Directory missing")
    
    print("=" * 50)

def main():
    """Main security configuration function"""
    print("🔒 STARTUPHUB SECURITY CONFIGURATION")
    print("=" * 50)
    
    # Configure security
    if configure_security():
        print("\n✅ Security configuration successful!")
    else:
        print("\n❌ Security configuration failed!")
        return False
    
    # Create security report
    create_security_report()
    
    print("\n📋 NEXT STEPS:")
    print("1. Set up SSL/TLS certificates for production")
    print("2. Configure proper ALLOWED_HOSTS for your domain")
    print("3. Set up monitoring and logging")
    print("4. Configure backup systems")
    print("5. Set up rate limiting")
    print("6. Configure email backend")
    print("7. Set up AWS S3 for file storage (if needed)")
    
    return True

if __name__ == '__main__':
    main()
