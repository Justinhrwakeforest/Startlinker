import os
import django

# Set PostgreSQL credentials
os.environ['DB_PASSWORD'] = 'Hruthikh123&'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_NAME'] = 'startup_hub'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

def reset_user_password():
    """Reset the user password to a known value"""
    try:
        print("=== Resetting User Password ===")
        
        # Get your user
        user = User.objects.get(email="hruthikrock536@gmail.com")
        print(f"Found user: {user.email}")
        
        # Set new password
        new_password = "newpass123"
        user.set_password(new_password)
        user.save()
        
        print(f"Password reset successfully!")
        print(f"New credentials:")
        print(f"  Email: hruthikrock536@gmail.com")
        print(f"  Password: {new_password}")
        
        # Test authentication
        auth_result = authenticate(username="hruthikrock536@gmail.com", password=new_password)
        if auth_result:
            print(f"SUCCESS: Authentication test passed!")
            print(f"You can now login with these credentials!")
            return True
        else:
            print(f"ERROR: Authentication test failed")
            return False
            
    except User.DoesNotExist:
        print(f"User not found!")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = reset_user_password()
    
    if success:
        print(f"\n=== READY TO LOGIN! ===")
        print(f"1. Make sure your Django server is running with PostgreSQL")
        print(f"2. Use these credentials to login:")
        print(f"   Email: hruthikrock536@gmail.com")
        print(f"   Password: newpass123")
        print(f"3. Login should work on the frontend now!")
    else:
        print(f"Need to fix the password reset issue")