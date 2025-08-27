import os
import django
import requests

# Setup Django environment - same as server should use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

def check_server_database():
    """Check if server is using the same database as our scripts"""
    try:
        print("=== Checking Server Database Configuration ===")
        
        # Show what database our scripts are using
        db_config = settings.DATABASES['default']
        print(f"Script Database Configuration:")
        print(f"  Engine: {db_config['ENGINE']}")
        print(f"  Name: {db_config['NAME']}")
        print(f"  Path: {os.path.abspath(str(db_config['NAME']))}")
        
        # Check users in our database
        users = User.objects.all()
        print(f"\nUsers in our database ({users.count()} total):")
        for user in users:
            print(f"  - {user.email} (username: {user.username})")
            print(f"    Active: {user.is_active}, Staff: {user.is_staff}")
        
        # Try to make a request to get server info
        print(f"\n=== Server Information ===")
        try:
            # Try to get server stats that might show database info
            response = requests.get("http://localhost:8000/api/stats/", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"Server shows {stats.get('total_users', 'unknown')} total users")
            else:
                print(f"Could not get server stats: {response.status_code}")
        except Exception as e:
            print(f"Could not connect to server stats: {e}")
        
        # Check if there's a different settings file being used
        print(f"\n=== Environment Check ===")
        django_settings = os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')
        print(f"DJANGO_SETTINGS_MODULE: {django_settings}")
        
        # Check if there are other database files
        print(f"\n=== Database File Check ===")
        possible_db_files = [
            'db.sqlite3',
            'database.db',
            'startup_hub.db',
            'development.db'
        ]
        
        for db_file in possible_db_files:
            if os.path.exists(db_file):
                size = os.path.getsize(db_file)
                print(f"  {db_file}: exists ({size} bytes)")
            else:
                print(f"  {db_file}: not found")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_debug_endpoint_test():
    """Create a test to verify server is using our database"""
    try:
        print(f"\n=== Creating Server Database Test ===")
        
        # Let's make a simple GET request to check users endpoint
        # if it exists, or create a user and see if server sees it
        
        # Create a unique test user
        test_email = f"servertest_{os.getpid()}@test.com"
        
        # Delete if exists
        User.objects.filter(email=test_email).delete()
        
        # Create test user
        test_user = User.objects.create_user(
            username=f"servertest{os.getpid()}",
            email=test_email,
            password="testpass123"
        )
        print(f"Created test user: {test_email}")
        
        # Try to login with this user immediately
        login_data = {
            "email": test_email,
            "password": "testpass123"
        }
        
        print(f"Testing login with fresh user...")
        response = requests.post(
            "http://localhost:8000/api/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("SUCCESS: Server can see our database changes!")
            data = response.json()
            print(f"Got token for test user")
        else:
            print(f"FAILED: Server cannot see our database changes")
            print(f"Response: {response.text}")
            print("This means server is using a different database!")
        
        # Clean up
        test_user.delete()
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"ERROR in server test: {e}")
        return False

if __name__ == "__main__":
    check_server_database()
    create_debug_endpoint_test()