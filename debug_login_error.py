import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from apps.users.serializers import UserLoginSerializer
from rest_framework.test import APIClient
from django.test import Client
import json

User = get_user_model()

def debug_login_error():
    """Debug the 400 Bad Request login error"""
    try:
        print("=== Debugging Login Error ===\n")
        
        # Check database connection and users
        print("1. Database Check:")
        print(f"Database: {django.conf.settings.DATABASES}")
        
        users = User.objects.all()
        print(f"Total users: {users.count()}")
        for user in users[:3]:
            print(f"  - {user.username} ({user.email}) - Active: {user.is_active}")
            
        # Test the exact login data from the frontend
        login_data = {
            "email": "hruthikrock536@gmail.com",
            "password": "newpass123",
            "remember_me": False
        }
        
        print(f"\n2. Testing login data: {login_data}")
        
        # Test if user exists
        try:
            user = User.objects.get(email=login_data["email"])
            print(f"User found: {user.username} ({user.email})")
            print(f"  - Active: {user.is_active}")
            print(f"  - Staff: {user.is_staff}")
            print(f"  - Email verified: {user.email_verified}")
        except User.DoesNotExist:
            print(f"ERROR: User with email {login_data['email']} does not exist!")
            print("Available users:")
            for user in User.objects.all():
                print(f"  - {user.email}")
            return False
            
        # Test Django authentication
        print("\n3. Testing Django authentication:")
        auth_result = authenticate(
            username=login_data["email"], 
            password=login_data["password"]
        )
        if auth_result:
            print("SUCCESS: Django authentication passed")
        else:
            print("FAILED: Django authentication failed - password incorrect")
            
        # Test the serializer directly
        print("\n4. Testing UserLoginSerializer:")
        serializer = UserLoginSerializer(data=login_data)
        if serializer.is_valid():
            print("SUCCESS: Serializer validation passed")
            validated_user = serializer.validated_data.get('user')
            if validated_user:
                print(f"Validated user: {validated_user.username}")
        else:
            print("FAILED: Serializer validation failed")
            print(f"Errors: {serializer.errors}")
            
        # Test the API endpoint directly
        print("\n5. Testing API endpoint directly:")
        client = APIClient()
        response = client.post(
            '/api/auth/login/',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Data: {response.data if hasattr(response, 'data') else response.content}")
        
        if response.status_code == 400:
            print("400 Bad Request Error Details:")
            if hasattr(response, 'data') and isinstance(response.data, dict):
                for field, errors in response.data.items():
                    print(f"  - {field}: {errors}")
                    
        return response.status_code == 200
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_user_if_missing():
    """Create the test user if it doesn't exist"""
    try:
        email = "hruthikrock536@gmail.com"
        
        if User.objects.filter(email=email).exists():
            print(f"User {email} already exists")
            return True
            
        print(f"Creating user: {email}")
        
        # Try to create using the registration serializer
        from apps.users.serializers import UserRegistrationSerializer
        
        user_data = {
            'username': 'hruthikrock536',
            'email': email,
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'Hruthik',
            'last_name': 'HR'
        }
        
        serializer = UserRegistrationSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            print(f"SUCCESS: User created via serializer: {user.email}")
            return True
        else:
            print(f"FAILED: User creation failed: {serializer.errors}")
            
            # Try direct creation
            user = User.objects.create_user(
                username='hruthikrock536',
                email=email,
                password='newpass123',
                first_name='Hruthik',
                last_name='HR'
            )
            print(f"SUCCESS: User created directly: {user.email}")
            return True
            
    except Exception as e:
        print(f"ERROR creating user: {e}")
        return False

if __name__ == "__main__":
    # First try to create the user if missing
    create_test_user_if_missing()
    
    # Then debug the login
    debug_login_error()