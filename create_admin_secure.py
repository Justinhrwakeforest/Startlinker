#!/usr/bin/env python
"""
Create admin user using environment variables (more secure)
Set these environment variables in Render:
- ADMIN_USERNAME
- ADMIN_EMAIL  
- ADMIN_PASSWORD
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin():
    """Create admin user from environment variables"""
    
    # Get credentials from environment
    admin_username = os.environ.get('ADMIN_USERNAME')
    admin_email = os.environ.get('ADMIN_EMAIL') 
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if not all([admin_username, admin_email, admin_password]):
        print("❌ Missing environment variables!")
        print("Please set: ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD")
        sys.exit(1)
    
    print("🔧 Creating admin user from environment variables...")
    
    # Check if admin already exists
    if User.objects.filter(username=admin_username).exists():
        print(f"✅ Admin user '{admin_username}' already exists!")
        return
    
    # Create admin user
    try:
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"👤 Username: {admin_username}")
        print(f"📧 Email: {admin_email}")
        print(f"\n🌐 Admin URL: https://startlinker-backend.onrender.com/admin/")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin()