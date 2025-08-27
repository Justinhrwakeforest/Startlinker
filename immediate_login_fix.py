import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def immediate_login_fix():
    """Provide immediate login solution"""
    print("=== Immediate Login Fix ===\n")
    
    # Option 1: Use the existing admin account
    print("OPTION 1 - Use Admin Account (RECOMMENDED):")
    print("Email: admin@startlinker.com")
    print("Password: admin123")
    print("This should work immediately for login testing.\n")
    
    # Option 2: Try to create user with raw SQL
    print("OPTION 2 - Create your user with direct SQL:")
    try:
        email = "hruthikrock536@gmail.com"
        
        # Delete if exists
        User.objects.filter(email=email).delete()
        
        with connection.cursor() as cursor:
            # Insert with all required fields
            cursor.execute("""
                INSERT INTO users_user (
                    username, email, password, first_name, last_name,
                    is_active, is_staff, is_superuser, date_joined,
                    bio, location, subscription_status,
                    email_verified, email_verification_token, email_verification_sent_at,
                    follower_count, following_count, is_premium
                ) VALUES (
                    'hruthikrock536', %s, 'pbkdf2_sha256$600000$temp$temp',
                    'Hruthik', 'HR', 1, 0, 0, datetime('now'),
                    '', '', 'free', 0, '', NULL, 0, 0, 0
                )
            """, [email])
            
        # Get the user and set proper password
        user = User.objects.get(email=email)
        user.set_password('newpass123')
        user.save(update_fields=['password'])
        
        print(f"SUCCESS: Created {email} with password 'newpass123'")
        
        # Test login
        from django.contrib.auth import authenticate
        auth_test = authenticate(username=email, password='newpass123')
        if auth_test:
            print("SUCCESS: User can now login!\n")
        else:
            print("WARNING: Login test failed\n")
            
    except Exception as e:
        print(f"FAILED: Could not create user - {e}")
        print("Use admin account instead.\n")
    
    # Option 3: Setup PostgreSQL
    print("OPTION 3 - Switch to PostgreSQL (LONG TERM):")
    print("1. Install PostgreSQL if not already installed")
    print("2. Create database: createdb startup_hub")
    print("3. Run with PostgreSQL settings:")
    print("   set DJANGO_SETTINGS_MODULE=startup_hub.settings.postgresql")
    print("   python manage.py migrate")
    print("   python manage.py createsuperuser")

def test_current_login():
    """Test current login options"""
    print("\n=== Testing Current Login Options ===\n")
    
    from django.contrib.auth import authenticate
    from apps.users.serializers import UserLoginSerializer
    
    # Test admin login
    print("Testing admin login:")
    admin_auth = authenticate(username='admin@startlinker.com', password='admin123')
    if admin_auth:
        print("✓ Admin login works")
        
        # Test with serializer
        login_data = {
            'email': 'admin@startlinker.com',
            'password': 'admin123'
        }
        serializer = UserLoginSerializer(data=login_data)
        if serializer.is_valid():
            print("✓ Admin login via API should work")
        else:
            print(f"✗ Admin API login failed: {serializer.errors}")
    else:
        print("✗ Admin login failed")
    
    # Test if hruthik user exists now
    if User.objects.filter(email='hruthikrock536@gmail.com').exists():
        print("\nTesting hruthik user login:")
        hruthik_auth = authenticate(username='hruthikrock536@gmail.com', password='newpass123')
        if hruthik_auth:
            print("✓ Hruthik login works")
            
            login_data = {
                'email': 'hruthikrock536@gmail.com',
                'password': 'newpass123'
            }
            serializer = UserLoginSerializer(data=login_data)
            if serializer.is_valid():
                print("✓ Hruthik login via API should work")
            else:
                print(f"✗ Hruthik API login failed: {serializer.errors}")
        else:
            print("✗ Hruthik login failed")

if __name__ == "__main__":
    immediate_login_fix()
    test_current_login()