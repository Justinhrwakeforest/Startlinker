#!/usr/bin/env python3
"""
Script to create admin user in production environment
Run this on your production server with proper environment variables set
"""

import os
import django

def setup_production_django():
    """Setup Django with production settings"""
    # Set production environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.production')
    
    # Required environment variables for production
    required_env_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'ALLOWED_HOSTS',
        'SENDGRID_API_KEY'
    ]
    
    print("=== Production Environment Check ===")
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
            print(f"❌ Missing: {var}")
        else:
            # Show partial values for security
            value = os.environ.get(var)
            if len(value) > 20:
                display_value = value[:10] + "..." + value[-5:]
            else:
                display_value = value[:5] + "..."
            print(f"✅ Found: {var} = {display_value}")
    
    if missing_vars:
        print(f"\n⚠️  WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print("Production setup may fail without these variables")
        
        # For demo purposes, we'll continue but warn user
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            print("Aborting...")
            return False
    
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def create_admin_user():
    """Create admin user in production"""
    from django.contrib.auth import get_user_model
    from django.core.exceptions import ValidationError
    
    User = get_user_model()
    
    print(f"\n=== Creating Admin User ===")
    
    # Get admin details
    admin_email = input("Admin email: ").strip()
    if not admin_email:
        print("❌ Email is required")
        return False
    
    admin_username = input("Admin username (optional, will use email): ").strip()
    if not admin_username:
        admin_username = admin_email
    
    admin_first_name = input("First name: ").strip()
    admin_last_name = input("Last name: ").strip()
    
    # Check if user already exists
    try:
        existing_user = User.objects.get(email=admin_email)
        print(f"⚠️  User {admin_email} already exists")
        
        if existing_user.is_staff and existing_user.is_superuser:
            print(f"✅ User is already an admin")
            return True
        else:
            print(f"📝 Promoting existing user to admin...")
            existing_user.is_staff = True
            existing_user.is_superuser = True
            existing_user.save()
            print(f"✅ User promoted to admin successfully!")
            return True
            
    except User.DoesNotExist:
        pass
    
    # Get password
    import getpass
    while True:
        password = getpass.getpass("Admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match. Try again.")
            continue
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters. Try again.")
            continue
            
        break
    
    # Create admin user
    try:
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            email_verified=True  # Admin should be verified
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Staff: {admin_user.is_staff}")
        print(f"   Superuser: {admin_user.is_superuser}")
        
        return True
        
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def test_admin_access():
    """Test admin login and permissions"""
    from django.contrib.auth import authenticate
    
    print(f"\n=== Testing Admin Access ===")
    
    email = input("Test admin email: ").strip()
    
    import getpass
    password = getpass.getpass("Test admin password: ")
    
    # Test authentication
    user = authenticate(username=email, password=password)
    
    if user:
        print(f"✅ Authentication successful!")
        print(f"   User: {user.email}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Active: {user.is_active}")
        
        if user.is_staff and user.is_superuser:
            print(f"✅ Admin permissions confirmed!")
            return True
        else:
            print(f"❌ User lacks admin permissions")
            return False
    else:
        print(f"❌ Authentication failed")
        return False

def main():
    """Main function"""
    print("🚀 StartLinker Production Admin Setup")
    print("=" * 40)
    
    # Setup Django
    if not setup_production_django():
        return
    
    # Show menu
    while True:
        print(f"\nOptions:")
        print(f"1. Create new admin user")
        print(f"2. Test admin login")
        print(f"3. List existing admin users")
        print(f"4. Exit")
        
        choice = input("Choose option (1-4): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            test_admin_access()
        elif choice == "3":
            list_admin_users()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

def list_admin_users():
    """List existing admin users"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    print(f"\n=== Existing Admin Users ===")
    
    admin_users = User.objects.filter(is_staff=True, is_superuser=True)
    
    if admin_users.exists():
        print(f"Found {admin_users.count()} admin users:")
        for user in admin_users:
            status = "✅ Active" if user.is_active else "❌ Inactive"
            verified = "✅ Verified" if getattr(user, 'email_verified', True) else "❌ Unverified"
            print(f"  - {user.email} ({user.username}) - {status} - {verified}")
    else:
        print("❌ No admin users found!")
        print("You should create at least one admin user.")

if __name__ == "__main__":
    main()