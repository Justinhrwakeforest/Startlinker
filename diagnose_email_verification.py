"""
Comprehensive email verification diagnostic
This will test the EXACT flow that happens during signup
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings
from django.test import RequestFactory
from apps.users.models import User
from apps.users.serializers import UserRegistrationSerializer
from apps.users.views import UserRegistrationView
from apps.users.email_utils import send_verification_email
from apps.users.email_views import send_verification_to_email
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_user_registration_complete_flow():
    """Test the complete user registration flow as it happens in production"""
    
    print("\n" + "="*80)
    print("TESTING COMPLETE USER REGISTRATION FLOW")
    print("="*80)
    
    # Get test email
    test_email = input("Enter your email address to test with: ").strip()
    if not test_email:
        print("No email provided")
        return False
    
    test_username = f"test_{test_email.split('@')[0]}_debug"
    
    print(f"\nTesting with:")
    print(f"  Email: {test_email}")
    print(f"  Username: {test_username}")
    
    # Clean up any existing test user first
    try:
        existing_user = User.objects.get(email=test_email)
        existing_user.delete()
        print("  Cleaned up existing user")
    except User.DoesNotExist:
        pass
    
    # Step 1: Test the registration serializer
    print("\n1. TESTING REGISTRATION SERIALIZER...")
    registration_data = {
        'username': test_username,
        'email': test_email,
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    serializer = UserRegistrationSerializer(data=registration_data)
    if serializer.is_valid():
        print("   ✅ Registration data is valid")
        try:
            user = serializer.save()
            print(f"   ✅ User created: {user.username} (ID: {user.id})")
            print(f"   ✅ Email: {user.email}")
            print(f"   ✅ Email verified: {user.email_verified}")
            print(f"   ✅ Verification token exists: {bool(user.email_verification_token)}")
        except Exception as e:
            print(f"   ❌ Error creating user: {e}")
            return False
    else:
        print(f"   ❌ Registration data invalid: {serializer.errors}")
        return False
    
    # Step 2: Test email sending directly
    print("\n2. TESTING EMAIL SENDING DIRECTLY...")
    
    try:
        # Mock request object
        factory = RequestFactory()
        request = factory.post('/', HTTP_HOST='startlinker.com', HTTP_ORIGIN='https://startlinker.com')
        
        print("   Attempting to send verification email...")
        success = send_verification_email(user, request)
        
        if success:
            print("   ✅ send_verification_email returned True")
            
            # Refresh user from database
            user.refresh_from_db()
            print(f"   ✅ User verification token: {user.email_verification_token[:20] if user.email_verification_token else 'None'}...")
            print(f"   ✅ Email sent at: {user.email_verification_sent_at}")
            
            # Check what URL would be generated
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{frontend_url}/auth/verify-email/{user.email_verification_token}"
            print(f"   ✅ Verification URL: {verification_url}")
            
        else:
            print("   ❌ send_verification_email returned False")
            print("   This means the email sending failed internally")
            
    except Exception as e:
        print(f"   ❌ Exception during email sending: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Test the API endpoint directly
    print("\n3. TESTING SEND-VERIFICATION API ENDPOINT...")
    
    try:
        # Reset the email sent timestamp to allow resending
        user.email_verification_sent_at = None
        user.save(update_fields=['email_verification_sent_at'])
        
        # Create request like frontend would
        factory = RequestFactory()
        request_data = {'email': test_email}
        request = factory.post(
            '/api/auth/send-verification/',
            data=json.dumps(request_data),
            content_type='application/json',
            HTTP_HOST='startlinker.com',
            HTTP_ORIGIN='https://startlinker.com'
        )
        
        print("   Calling send_verification_to_email endpoint...")
        response = send_verification_to_email(request)
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response data: {response.data}")
        
        if response.status_code == 200:
            print("   ✅ API endpoint worked successfully")
        else:
            print(f"   ❌ API endpoint failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception in API endpoint: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Test SendGrid directly
    print("\n4. TESTING SENDGRID DIRECTLY...")
    
    try:
        from django.core.mail import send_mail
        
        result = send_mail(
            subject='Direct SendGrid Test from StartLinker',
            message=f'This is a direct test email to {test_email} from your StartLinker backend.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        
        if result == 1:
            print("   ✅ Direct SendGrid test email sent successfully!")
            print(f"   Check your inbox at {test_email}")
        else:
            print(f"   ❌ Direct SendGrid test failed, result: {result}")
            
    except Exception as e:
        print(f"   ❌ Direct SendGrid test error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Check SendGrid backend configuration
    print("\n5. CHECKING SENDGRID BACKEND CONFIGURATION...")
    
    try:
        from apps.users.sendgrid_backend import SendGridBackend
        
        backend = SendGridBackend()
        print(f"   API Key configured: {bool(backend.api_key)}")
        print(f"   Client initialized: {bool(backend.client)}")
        
        if backend.api_key:
            print(f"   API Key preview: {backend.api_key[:15]}...")
            if not backend.api_key.startswith('SG.'):
                print("   ⚠️  API Key doesn't start with 'SG.' - might be invalid")
        
        # Test backend directly
        if backend.client:
            print("   Testing backend email send...")
            from django.core.mail import EmailMessage
            
            msg = EmailMessage(
                subject='Backend Test Email',
                body=f'This is a test email sent through the custom SendGrid backend to {test_email}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[test_email]
            )
            
            sent_count = backend.send_messages([msg])
            if sent_count > 0:
                print("   ✅ Backend test email sent successfully!")
            else:
                print("   ❌ Backend test email failed")
        
    except Exception as e:
        print(f"   ❌ Backend configuration error: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    try:
        user.delete()
        print(f"\n✅ Cleaned up test user: {test_username}")
    except:
        print(f"\n⚠️  Could not clean up test user")
    
    return success

def check_environment_configuration():
    """Check all environment configuration"""
    
    print("\n" + "="*80)
    print("CHECKING ENVIRONMENT CONFIGURATION")
    print("="*80)
    
    # Critical environment variables
    env_checks = {
        'SENDGRID_API_KEY': os.environ.get('SENDGRID_API_KEY'),
        'DEFAULT_FROM_EMAIL': os.environ.get('DEFAULT_FROM_EMAIL'),
        'FRONTEND_URL': os.environ.get('FRONTEND_URL'),
        'DJANGO_SETTINGS_MODULE': os.environ.get('DJANGO_SETTINGS_MODULE'),
    }
    
    print("Environment Variables:")
    for key, value in env_checks.items():
        if value:
            if key == 'SENDGRID_API_KEY':
                print(f"  ✅ {key}: {value[:15]}...")
            else:
                print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: NOT SET")
    
    # Django settings
    print(f"\nDjango Settings:")
    print(f"  EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"  FRONTEND_URL: {getattr(settings, 'FRONTEND_URL', 'Not set')}")
    print(f"  REQUIRE_EMAIL_VERIFICATION: {getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', 'Not set')}")
    print(f"  DEBUG: {settings.DEBUG}")
    
    # Email verification settings
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    print(f"  EMAIL_VERIFICATION_SETTINGS: {email_settings}")

def main():
    """Main diagnostic function"""
    
    print("STARTLINKER EMAIL VERIFICATION DIAGNOSTIC")
    print("This will test the complete email verification flow")
    print("Make sure you can access your email to check for messages")
    
    # Check environment first
    check_environment_configuration()
    
    # Test complete flow
    success = test_user_registration_complete_flow()
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)
    
    if success:
        print("✅ Email sending appears to work technically")
        print("\nIf you're still not receiving emails, check:")
        print("1. Spam/junk folder")
        print("2. SendGrid activity feed for delivery status")
        print("3. Email address spelling")
        print("4. Email provider blocking")
    else:
        print("❌ Email sending failed")
        print("\nCommon fixes:")
        print("1. Verify SendGrid API key is correct")
        print("2. Verify sender email in SendGrid dashboard")
        print("3. Check SendGrid account is not in sandbox mode")
        print("4. Ensure SendGrid account is verified and active")
    
    print(f"\nNext steps:")
    print("1. Check SendGrid Activity Feed: https://app.sendgrid.com/activity")
    print("2. Run this script on Render: python diagnose_email_verification.py")
    print("3. Check Render logs for any errors")

if __name__ == "__main__":
    main()