"""
EMERGENCY FIX SCRIPT
Run this immediately on Render to fix authentication issues
"""

import os
import sys

print("=" * 60)
print("EMERGENCY AUTHENTICATION FIX")
print("=" * 60)

print("\n1. CRITICAL ENVIRONMENT VARIABLES TO ADD:")
print("-" * 40)
print("Add these to Render Dashboard → Environment:")
print()
print("CORS_DEBUG=true")
print("CSRF_COOKIE_SECURE=False")
print("SESSION_COOKIE_SECURE=False")
print("SECURE_SSL_REDIRECT=False")
print()
print("These will temporarily disable security features to fix the 403 errors")

print("\n2. CHECK CURRENT SETTINGS:")
print("-" * 40)

# Try to load Django
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
    import django
    django.setup()
    from django.conf import settings
    
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)}")
    print(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', True)}")
    print(f"SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', True)}")
    print(f"SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', True)}")
    
    # Check middleware
    print(f"\nMiddleware count: {len(settings.MIDDLEWARE)}")
    cors_middleware = 'corsheaders.middleware.CorsMiddleware' in settings.MIDDLEWARE
    print(f"CORS middleware present: {cors_middleware}")
    
except Exception as e:
    print(f"Error loading Django: {e}")

print("\n3. TEST EMAIL DIRECTLY:")
print("-" * 40)

if len(sys.argv) > 1:
    test_email = sys.argv[1]
    print(f"Testing email to: {test_email}")
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        result = send_mail(
            subject='Emergency Test from StartLinker',
            message='This is an emergency test email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        
        if result:
            print(f"✅ Email sent to {test_email}")
        else:
            print("❌ Email failed to send")
            
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("Run with email to test: python emergency_fix.py your@email.com")

print("\n4. IMMEDIATE ACTIONS:")
print("-" * 40)
print("1. Add the environment variables above to Render")
print("2. Wait for redeploy (2-3 minutes)")
print("3. Test login again")
print("4. If it works, we can fix the security settings properly")