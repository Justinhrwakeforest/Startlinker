"""
Debug authentication and verification errors
Run this to see what's causing the 500 errors
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings
from django.test import RequestFactory
from apps.users.models import User
from apps.users.email_views import send_verification_to_email
import json

def test_send_verification_endpoint():
    """Test the send-verification endpoint that's failing"""
    
    print("Testing /api/auth/send-verification/ endpoint")
    print("=" * 50)
    
    # Create a request factory
    factory = RequestFactory()
    
    # Test with a real email
    test_email = input("Enter email to test verification with: ").strip()
    if not test_email:
        print("No email provided, exiting")
        return
    
    try:
        # Create or get user
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'username': f'test_{test_email.split("@")[0]}',
                'first_name': 'Test',
                'last_name': 'User',
                'email_verified': False  # Make sure it's not verified
            }
        )
        
        print(f"User: {user.username} ({'created' if created else 'existing'})")
        print(f"Email verified: {user.email_verified}")
        
        # Create a POST request like the frontend would send
        request_data = {'email': test_email}
        request = factory.post(
            '/api/auth/send-verification/',
            data=json.dumps(request_data),
            content_type='application/json',
            HTTP_ORIGIN='https://startlinker-frontend.onrender.com'
        )
        
        # Call the view function directly
        print("\nCalling send_verification_to_email view...")
        response = send_verification_to_email(request)
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        if response.status_code == 500:
            print("\n❌ 500 Error occurred!")
            print("Check server logs for the actual error")
        else:
            print("\n✅ Request processed successfully")
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test user if created
        if created and 'user' in locals():
            user.delete()
            print(f"\nCleaned up test user: {user.username}")

def test_cors_settings():
    """Check CORS and CSRF settings"""
    
    print("\nCORS and CSRF Configuration")
    print("=" * 50)
    
    print(f"CORS_ALLOWED_ORIGINS: {getattr(settings, 'CORS_ALLOWED_ORIGINS', [])}")
    print(f"CORS_ALLOW_CREDENTIALS: {getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)}")
    print(f"CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)}")
    print(f"CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])}")
    print(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', False)}")
    print(f"SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', False)}")
    
    # Check environment variables
    print(f"\nEnvironment Variables:")
    print(f"CORS_ALLOWED_ORIGINS: {os.environ.get('CORS_ALLOWED_ORIGINS', 'Not set')}")
    print(f"CSRF_TRUSTED_ORIGINS: {os.environ.get('CSRF_TRUSTED_ORIGINS', 'Not set')}")
    print(f"CORS_DEBUG: {os.environ.get('CORS_DEBUG', 'Not set')}")

def main():
    """Main debug function"""
    
    print("Authentication Debug Tool")
    print("=" * 50)
    
    # Check CORS settings
    test_cors_settings()
    
    # Test send verification endpoint
    test_send_verification_endpoint()
    
    print("\n" + "=" * 50)
    print("Recommendations:")
    print("1. Check server logs on Render for detailed 500 error")
    print("2. Ensure frontend URL is exactly correct")
    print("3. Add CORS_DEBUG=true to Render env vars temporarily")
    print("4. Check if user email already exists and is verified")

if __name__ == "__main__":
    main()