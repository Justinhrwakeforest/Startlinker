"""
Check deployment health and fix common issues
Run this script to diagnose deployment problems
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.conf import settings
from django.core.management import call_command

def check_deployment_status():
    """Check basic deployment health"""
    
    print("\n" + "="*60)
    print("DEPLOYMENT HEALTH CHECK")
    print("="*60)
    
    # Check critical settings
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)}")
    print(f"CORS_ALLOWED_ORIGINS: {getattr(settings, 'CORS_ALLOWED_ORIGINS', [])}")
    
    # Check environment variables
    critical_vars = ['SENDGRID_API_KEY', 'DATABASE_URL', 'SECRET_KEY', 'DEFAULT_FROM_EMAIL']
    print(f"\nEnvironment Variables:")
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            if var == 'SENDGRID_API_KEY':
                print(f"  {var}: {value[:15]}...")
            elif var == 'DATABASE_URL':
                print(f"  {var}: postgres://...")
            elif var == 'SECRET_KEY':
                print(f"  {var}: {'*' * 20}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ❌ NOT SET")
    
    # Test database connection
    print(f"\nDatabase Connection:")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("  ✅ Database connection successful")
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
    
    # Check if tables exist
    try:
        from apps.users.models import User
        user_count = User.objects.count()
        print(f"  ✅ User table accessible, {user_count} users")
    except Exception as e:
        print(f"  ❌ User table issue: {e}")

def fix_cors_temporarily():
    """Temporarily enable permissive CORS"""
    
    print("\n" + "="*60)
    print("CORS TEMPORARY FIX")
    print("="*60)
    
    cors_debug = os.environ.get('CORS_DEBUG', 'False').lower()
    if cors_debug == 'true':
        print("✅ CORS_DEBUG is already enabled")
        print("   All origins should be allowed")
    else:
        print("❌ CORS_DEBUG is not enabled")
        print("   Add CORS_DEBUG=true to Render environment variables")
        print("   This will temporarily fix CORS issues")

def reset_user_cooldowns():
    """Reset email cooldowns for testing"""
    
    print("\n" + "="*60)
    print("RESET EMAIL COOLDOWNS")
    print("="*60)
    
    try:
        from apps.users.models import User
        
        # Find users with active cooldowns
        users_with_cooldowns = User.objects.filter(
            email_verification_sent_at__isnull=False
        )
        
        count = users_with_cooldowns.count()
        if count > 0:
            users_with_cooldowns.update(email_verification_sent_at=None)
            print(f"✅ Reset cooldowns for {count} users")
        else:
            print("ℹ️  No users have active cooldowns")
            
    except Exception as e:
        print(f"❌ Error resetting cooldowns: {e}")

def test_email_configuration():
    """Test email configuration"""
    
    print("\n" + "="*60)
    print("EMAIL CONFIGURATION TEST")
    print("="*60)
    
    # Test SendGrid import
    try:
        import sendgrid
        api_key = os.environ.get('SENDGRID_API_KEY')
        if api_key:
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            print("✅ SendGrid client created successfully")
        else:
            print("❌ SENDGRID_API_KEY not found")
    except ImportError:
        print("❌ SendGrid package not installed")
    except Exception as e:
        print(f"❌ SendGrid error: {e}")
    
    # Check email backend
    email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
    print(f"Email backend: {email_backend}")
    
    if 'sendgrid' in email_backend.lower():
        print("✅ Using SendGrid backend")
    else:
        print("⚠️  Not using SendGrid backend")

def main():
    """Main health check"""
    
    print("StartLinker Deployment Health Check")
    print("Run this after each deployment to verify everything is working")
    
    check_deployment_status()
    fix_cors_temporarily() 
    reset_user_cooldowns()
    test_email_configuration()
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. If CORS_DEBUG is not enabled, add it to Render environment")
    print("2. Wait for Render to redeploy (2-3 minutes)")
    print("3. Test your frontend again")
    print("4. Check Render logs for any deployment errors")
    print("5. Use debug UI: /api/users/debug/email-ui/")
    print("="*60)

if __name__ == "__main__":
    main()