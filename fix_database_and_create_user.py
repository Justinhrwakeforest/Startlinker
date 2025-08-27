import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.db import connection

User = get_user_model()

def fix_database_constraints():
    """Fix database constraints by adding default values"""
    try:
        print("Fixing database constraints...")
        
        with connection.cursor() as cursor:
            # Add default values for NOT NULL columns
            cursor.execute("UPDATE users_user SET bio = '' WHERE bio IS NULL")
            cursor.execute("UPDATE users_user SET location = '' WHERE location IS NULL")
            cursor.execute("UPDATE users_user SET subscription_status = 'free' WHERE subscription_status IS NULL OR subscription_status = ''")
            
        print("Database constraints fixed!")
        return True
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

def create_user_via_django():
    """Create user using Django ORM after fixing constraints"""
    try:
        test_email = "justinhrwakeforest536@gmail.com"
        test_username = "Justinhr"
        test_password = "password123"
        
        print(f"Creating user via Django: {test_email}")
        
        # Delete existing user if any
        User.objects.filter(email=test_email).delete()
        User.objects.filter(username=test_username).delete()
        
        # Create user with all required fields
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password,
            first_name="Justin",
            last_name="HR"
        )
        
        print(f"SUCCESS: User created successfully!")
        print(f"Email: {test_email}")
        print(f"Username: {test_username}")
        print(f"Password: {test_password}")
        
        # Test authentication
        auth_result = authenticate(username=test_email, password=test_password)
        if auth_result:
            print("SUCCESS: Authentication test passed!")
        else:
            print("WARNING: Authentication test failed")
            
        # Test the login serializer
        from apps.users.serializers import UserLoginSerializer
        
        print("\nTesting login serializer:")
        login_data = {
            'email': test_email,
            'password': test_password
        }
        
        serializer = UserLoginSerializer(data=login_data)
        if serializer.is_valid():
            print("SUCCESS: Login serializer validation passed")
            validated_user = serializer.validated_data.get('user')
            if validated_user:
                print(f"User can login: {validated_user.username}")
        else:
            print("FAILED: Login serializer validation failed")
            print(f"Errors: {serializer.errors}")
            
        return user
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_login_requirements():
    """Check if there are any special login requirements"""
    try:
        print("\n=== Checking Login Requirements ===")
        
        # Check if email verification is enforced
        from apps.users.views import UserLoginView
        from apps.users.serializers import UserLoginSerializer
        
        print("Login system components:")
        print(f"- Login view: {UserLoginView}")
        print(f"- Login serializer: {UserLoginSerializer}")
        
        # Look for any email verification checks
        import inspect
        login_view_source = inspect.getsource(UserLoginView)
        if 'email_verified' in login_view_source:
            print("WARNING: Login view may check email verification")
        else:
            print("INFO: No email verification check found in login view")
            
        # Check the frontend login endpoint
        print("\nFrontend should call: /api/auth/login/")
        print("Required data: {'email': 'user@email.com', 'password': 'password'}")
        
        return True
        
    except Exception as e:
        print(f"Error checking login requirements: {e}")
        return False

if __name__ == "__main__":
    # Fix database constraints first
    if fix_database_constraints():
        # Create user
        user = create_user_via_django()
        
        if user:
            # Check login requirements
            check_login_requirements()
            
            print("\n" + "="*50)
            print("READY TO TEST LOGIN!")
            print("="*50)
            print(f"Email: justinhrwakeforest536@gmail.com")
            print(f"Password: password123")
            print("Also available:")
            print(f"Admin Email: admin@startlinker.com")
            print(f"Admin Password: admin123")
            print("="*50)