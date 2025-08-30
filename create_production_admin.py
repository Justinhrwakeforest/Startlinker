#!/usr/bin/env python
"""
Create admin user for production
Run this on Render or production environment
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
    """Create admin user if it doesn't exist"""
    
    # Admin credentials - change these!
    admin_username = 'admin'
    admin_email = 'your-email@example.com'  # CHANGE THIS
    admin_password = 'YourSecurePassword123!'  # CHANGE THIS
    
    print("🔧 Creating admin user for production...")
    
    # Check if admin already exists
    if User.objects.filter(username=admin_username).exists():
        print(f"❌ Admin user '{admin_username}' already exists!")
        admin_user = User.objects.get(username=admin_username)
        print(f"📧 Email: {admin_user.email}")
        print(f"🔐 Is superuser: {admin_user.is_superuser}")
        print(f"✅ Is staff: {admin_user.is_staff}")
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
        print(f"🔐 Password: {admin_password}")
        print(f"\n🌐 Admin URL: https://startlinker-backend.onrender.com/admin/")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin()