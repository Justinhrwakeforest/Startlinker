import os
import django

def find_postgresql_credentials():
    """Try to find working PostgreSQL credentials"""
    
    # Common PostgreSQL credential combinations
    credential_combinations = [
        {'user': 'postgres', 'password': ''},
        {'user': 'postgres', 'password': 'postgres'},
        {'user': 'postgres', 'password': 'admin'},
        {'user': 'postgres', 'password': 'password'},
        {'user': 'postgres', 'password': 'root'},
        {'user': 'postgres', 'password': '123456'},
        {'user': 'startup_hub', 'password': 'password'},
        {'user': os.getenv('USERNAME', 'user'), 'password': ''},
        {'user': os.getenv('USERNAME', 'user'), 'password': 'password'},
    ]
    
    print("=== Testing PostgreSQL Credentials ===")
    print(f"Current Windows user: {os.getenv('USERNAME', 'unknown')}")
    
    for i, creds in enumerate(credential_combinations, 1):
        user = creds['user']
        password = creds['password']
        password_display = password if password else '(empty)'
        
        print(f"\n{i}. Testing: user='{user}', password='{password_display}'")
        
        try:
            # Update environment variables
            os.environ['DB_USER'] = user
            os.environ['DB_PASSWORD'] = password
            
            # Setup Django with new credentials
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
            
            # Force Django to reload settings
            if 'django.conf' in globals():
                from django.conf import settings
                settings._wrapped = None
            
            django.setup()
            
            from django.db import connection
            
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result:
                    print(f"✓ SUCCESS! Working credentials found:")
                    print(f"  DB_USER={user}")
                    print(f"  DB_PASSWORD={password}")
                    
                    # Test user query
                    try:
                        cursor.execute("SELECT COUNT(*) FROM auth_user")
                        user_count = cursor.fetchone()[0]
                        print(f"  Users in database: {user_count}")
                        
                        # Look for your user
                        cursor.execute("SELECT email, username, is_active FROM auth_user WHERE email LIKE %s", ['%hruthik%'])
                        users = cursor.fetchall()
                        if users:
                            print(f"  Found users matching 'hruthik':")
                            for email, username, is_active in users:
                                print(f"    - {email} (username: {username}, active: {is_active})")
                        
                        return {'user': user, 'password': password}
                        
                    except Exception as e:
                        print(f"  Connection works but error querying users: {e}")
                        return {'user': user, 'password': password}
                        
        except Exception as e:
            print(f"✗ Failed: {str(e)[:100]}")
            continue
    
    print(f"\n❌ Could not find working PostgreSQL credentials")
    print(f"Common solutions:")
    print(f"1. Check PostgreSQL service is running")
    print(f"2. Reset postgres user password:")
    print(f"   - Stop PostgreSQL service")
    print(f"   - Start with --auth-trust")  
    print(f"   - ALTER USER postgres PASSWORD 'newpassword';")
    print(f"3. Check pg_hba.conf authentication method")
    
    return None

def create_postgresql_env():
    """Create environment file with found credentials"""
    creds = find_postgresql_credentials()
    
    if creds:
        env_content = f"""# Working PostgreSQL Configuration
DB_NAME=startup_hub
DB_USER={creds['user']}
DB_PASSWORD={creds['password']}
DB_HOST=localhost
DB_PORT=5432

# Use these environment variables or update settings/development.py
"""
        try:
            with open('.env', 'w') as f:
                f.write(env_content)
            print(f"\n✓ Created .env file with working credentials")
            print(f"Your Django app should now connect to PostgreSQL!")
        except Exception as e:
            print(f"Could not create .env file: {e}")
    
    return creds

if __name__ == "__main__":
    creds = create_postgresql_env()
    
    if creds:
        print(f"\n🎉 Ready to test login!")
        print(f"Your user should exist in the PostgreSQL database.")
        print(f"Try logging in with hruthikrock536@gmail.com")
    else:
        print(f"\n❌ Need to fix PostgreSQL connection first")
        print(f"Check your PostgreSQL installation and credentials")