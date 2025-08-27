import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.db import connection

User = get_user_model()

def create_user_properly():
    """Create user using direct SQL to avoid constraints"""
    try:
        test_email = "justinhrwakeforest536@gmail.com"
        test_username = "Justinhr"
        test_password = "password123"
        
        print(f"Creating user: {test_email}")
        
        # Delete existing user if any
        User.objects.filter(email=test_email).delete()
        User.objects.filter(username=test_username).delete()
        
        # Create using direct SQL
        with connection.cursor() as cursor:
            # First, let's see what columns exist
            cursor.execute("PRAGMA table_info(users_user)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Available columns: {columns}")
            
            # Insert minimal required data
            cursor.execute("""
                INSERT INTO users_user (
                    username, email, first_name, last_name, 
                    is_active, is_staff, is_superuser, date_joined,
                    email_verified, email_verification_token, email_verification_sent_at,
                    password
                ) VALUES (
                    ?, ?, ?, ?,
                    1, 0, 0, datetime('now'),
                    0, '', NULL,
                    'pbkdf2_sha256$600000$temp$temp'
                )
            """, [test_username, test_email, "Justin", "HR"])
        
        # Get the created user and set proper password
        user = User.objects.get(email=test_email)
        user.set_password(test_password)
        user.save()
        
        print(f"SUCCESS: User created successfully!")
        print(f"Email: {test_email}")
        print(f"Password: {test_password}")
        
        # Test authentication
        auth_result = authenticate(username=test_email, password=test_password)
        if auth_result:
            print("SUCCESS: Authentication test passed!")
        else:
            print("WARNING: Authentication test failed")
            
        # Check if login view requires email verification
        print(f"\nUser details:")
        print(f"- Active: {user.is_active}")
        print(f"- Email verified: {user.email_verified}")
        print(f"- Staff: {user.is_staff}")
        
        return user
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_login_with_verification_check():
    """Test if email verification affects login"""
    try:
        user = User.objects.get(email="justinhrwakeforest536@gmail.com")
        
        print("\n=== Testing Login Requirements ===")
        
        # Check login serializer behavior
        from apps.users.serializers import UserLoginSerializer
        
        login_data = {
            'email': user.email,
            'password': 'password123'
        }
        
        serializer = UserLoginSerializer(data=login_data)
        
        if serializer.is_valid():
            print("SUCCESS: Login serializer validation passed")
            validated_user = serializer.validated_data.get('user')
            print(f"Validated user: {validated_user.username if validated_user else 'None'}")
            
            # Check if email verification is required somewhere
            if hasattr(validated_user, 'email_verified'):
                print(f"Email verified status: {validated_user.email_verified}")
                
        else:
            print("FAILED: Login serializer validation failed")
            print(f"Errors: {serializer.errors}")
            
    except User.DoesNotExist:
        print("User not found, creating first...")
        return create_user_properly()
    except Exception as e:
        print(f"ERROR in login test: {e}")

if __name__ == "__main__":
    # First create the user
    user = create_user_properly()
    
    if user:
        # Then test login
        test_login_with_verification_check()