import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

def create_your_user():
    """Create the user account you're trying to login with"""
    try:
        email = "hruthikrock536@gmail.com"
        username = "hruthikrock536"
        password = "newpass123"
        
        print(f"Creating user: {email}")
        
        # Delete if exists
        User.objects.filter(email=email).delete()
        User.objects.filter(username=username).delete()
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Hruthik",
            last_name="HR"
        )
        
        print(f"SUCCESS: User created!")
        print(f"Email: {email}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        
        # Test authentication
        auth_result = authenticate(username=email, password=password)
        if auth_result:
            print("SUCCESS: Authentication test passed!")
        else:
            print("ERROR: Authentication test failed!")
            
        # Test with your exact login data
        from apps.users.serializers import UserLoginSerializer
        
        login_data = {
            "email": email,
            "password": password,
            "remember_me": False
        }
        
        serializer = UserLoginSerializer(data=login_data)
        if serializer.is_valid():
            print("SUCCESS: Login serializer validation passed!")
            print("You should now be able to login on the frontend")
        else:
            print(f"ERROR: Login serializer failed: {serializer.errors}")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_postgresql_if_needed():
    """Check if we should be using PostgreSQL instead"""
    print("Current database configuration:")
    from django.conf import settings
    
    db_config = settings.DATABASES['default']
    print(f"Engine: {db_config['ENGINE']}")
    print(f"Name: {db_config['NAME']}")
    
    if 'sqlite' in db_config['ENGINE']:
        print("\nCurrently using SQLite. If you prefer PostgreSQL:")
        print("1. Install PostgreSQL locally")
        print("2. Create a database named 'startup_hub'")
        print("3. Update settings/development.py to use PostgreSQL")
        print("4. Run migrations")
        print("\nFor now, continuing with SQLite...")

if __name__ == "__main__":
    setup_postgresql_if_needed()
    create_your_user()