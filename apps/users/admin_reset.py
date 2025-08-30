"""
Admin password reset utilities for production
"""
import os
from django.contrib.auth import get_user_model
import secrets
import string

User = get_user_model()

def reset_admin_password():
    """
    Reset admin user password
    Returns dict with status and new password
    """
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    
    try:
        admin_user = User.objects.get(username=admin_username, is_superuser=True)
        
        # Generate new secure password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(secrets.choice(alphabet) for i in range(16))
        
        # Reset password
        admin_user.set_password(new_password)
        admin_user.save()
        
        return {
            'status': 'reset',
            'message': f'Password reset successfully for admin user "{admin_username}"',
            'username': admin_username,
            'email': admin_user.email,
            'new_password': new_password,
            'admin_url': 'https://startlinker-backend.onrender.com/admin/'
        }
        
    except User.DoesNotExist:
        return {
            'status': 'not_found',
            'message': f'Admin user "{admin_username}" not found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error resetting password: {str(e)}'
        }