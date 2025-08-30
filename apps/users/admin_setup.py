"""
Admin setup utilities for production environments without shell access
"""
import os
from django.contrib.auth import get_user_model
from django.conf import settings
import secrets
import string

User = get_user_model()

def create_admin_user():
    """
    Create admin user with credentials from environment variables
    Returns dict with status and details
    """
    # Get credentials from environment or use defaults
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@startlinker.com')
    
    # Generate secure password if not provided
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        # Generate a secure random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        admin_password = ''.join(secrets.choice(alphabet) for i in range(16))
    
    # Check if admin already exists
    if User.objects.filter(username=admin_username).exists():
        admin_user = User.objects.get(username=admin_username)
        return {
            'status': 'exists',
            'message': f'Admin user "{admin_username}" already exists',
            'username': admin_username,
            'email': admin_user.email,
            'is_superuser': admin_user.is_superuser,
            'is_staff': admin_user.is_staff
        }
    
    try:
        # Create admin user
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        
        return {
            'status': 'created',
            'message': 'Admin user created successfully',
            'username': admin_username,
            'email': admin_email,
            'password': admin_password,
            'admin_url': f"{settings.BACKEND_URL or 'https://startlinker-backend.onrender.com'}/admin/"
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error creating admin user: {str(e)}'
        }