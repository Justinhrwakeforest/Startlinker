import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.conf import settings

User = get_user_model()

def debug_authentication_backend():
    """Debug the authentication backend issue"""
    try:
        print("=== Debugging Authentication Backend ===")
        
        user = User.objects.get(email="hruthikrock536@gmail.com")
        print(f"User: {user.email}")
        print(f"User ID: {user.id}")
        print(f"Username field: {user.username}")
        print(f"Is active: {user.is_active}")
        
        # Check password hash
        print(f"\nPassword hash starts with: {user.password[:20]}...")
        
        # Test password directly
        password_check = check_password("newpass123", user.password)
        print(f"Direct password check: {password_check}")
        
        # Test different authentication methods
        print(f"\nTesting different authentication methods:")
        
        # Method 1: Authenticate with email (should work based on USERNAME_FIELD)
        auth1 = authenticate(username=user.email, password="newpass123")
        print(f"authenticate(username=email): {auth1 is not None}")
        
        # Method 2: Authenticate with username
        auth2 = authenticate(username=user.username, password="newpass123")
        print(f"authenticate(username=username): {auth2 is not None}")
        
        # Method 3: Check authentication backends
        print(f"\nAuthentication backends: {settings.AUTHENTICATION_BACKENDS}")
        
        # Method 4: Test the serializer authenticate call specifically
        print(f"\nTesting serializer authenticate call:")
        
        # Look at how the serializer calls authenticate
        from apps.users.serializers import UserLoginSerializer
        import inspect
        
        serializer_source = inspect.getsource(UserLoginSerializer)
        print("UserLoginSerializer.validate method:")
        lines = serializer_source.split('\n')
        in_validate = False
        for line in lines:
            if 'def validate(' in line:
                in_validate = True
            if in_validate:
                print(line)
                if line.strip().startswith('return data'):
                    break
        
        # Test the exact way serializer authenticates
        print(f"\nTesting serializer's authenticate call:")
        email = "hruthikrock536@gmail.com"
        password = "newpass123"
        
        # This is how the serializer calls authenticate
        serializer_auth = authenticate(username=email, password=password)
        print(f"Serializer method result: {serializer_auth is not None}")
        
        if not serializer_auth:
            print("This is the problem - serializer's authenticate call fails")
            
            # Check if there's an issue with the authentication backend
            from django.contrib.auth.backends import ModelBackend
            backend = ModelBackend()
            
            # Test the backend directly
            backend_result = backend.authenticate(None, username=email, password=password)
            print(f"ModelBackend direct call: {backend_result is not None}")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def reset_user_password():
    """Reset user password to ensure it's correct"""
    try:
        print(f"\n=== Resetting User Password ===")
        
        user = User.objects.get(email="hruthikrock536@gmail.com")
        
        # Set password again
        user.set_password("newpass123")
        user.save()
        
        print("Password reset completed")
        
        # Test again
        auth_test = authenticate(username="hruthikrock536@gmail.com", password="newpass123")
        print(f"Authentication after reset: {auth_test is not None}")
        
        return True
        
    except Exception as e:
        print(f"ERROR resetting password: {e}")
        return False

if __name__ == "__main__":
    debug_authentication_backend()
    reset_user_password()