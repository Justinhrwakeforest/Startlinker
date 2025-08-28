"""
Debug script to test the complete signup and email verification flow
Run this on Render to see where the process is failing
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings
from apps.users.models import User
from apps.users.email_utils import send_verification_email
from apps.users.serializers import UserRegistrationSerializer
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_complete_signup_flow(test_email, test_username=None):
    """Test the complete signup flow that matches your frontend"""
    
    if not test_username:
        test_username = f"test_{test_email.split('@')[0]}"
    
    print(f"\n{'='*60}")
    print(f"TESTING COMPLETE SIGNUP FLOW")
    print(f"Email: {test_email}")
    print(f"Username: {test_username}")
    print(f"{'='*60}")
    
    # Step 1: Simulate user registration like the frontend does
    print("\n1. TESTING USER REGISTRATION SERIALIZER...")
    
    registration_data = {
        'username': test_username,
        'email': test_email,
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    try:
        # Test the serializer (same one used by UserRegistrationView)
        serializer = UserRegistrationSerializer(data=registration_data)
        if serializer.is_valid():
            print("   ✓ Registration data is valid")
            
            # Create user (this is what happens in the view)
            user = serializer.save()
            print(f"   ✓ User created successfully: {user.username}")
            print(f"   ✓ User ID: {user.id}")
            print(f"   ✓ Email verified: {user.email_verified}")
            print(f"   ✓ Has verification token: {bool(user.email_verification_token)}")
            
        else:
            print(f"   ✗ Registration data invalid: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error during user creation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Test email verification sending (this happens in UserRegistrationView)
    print("\n2. TESTING EMAIL VERIFICATION SENDING...")
    
    try:
        # Simulate the request object (since we don't have one in this script)
        class MockRequest:
            def __init__(self):
                self.scheme = 'https'
            
            def get_host(self):
                return 'startlinker-backend.onrender.com'
        
        mock_request = MockRequest()
        
        # This is the exact same call made in UserRegistrationView
        verification_sent = send_verification_email(user, mock_request)
        
        print(f"   Email sending result: {verification_sent}")
        
        if verification_sent:
            print("   ✓ Verification email sent successfully")
            
            # Check user state after sending
            user.refresh_from_db()
            print(f"   ✓ User has verification token: {bool(user.email_verification_token)}")
            print(f"   ✓ Token sent at: {user.email_verification_sent_at}")
            
            if user.email_verification_token:
                print(f"   ✓ Token preview: {user.email_verification_token[:20]}...")
        else:
            print("   ✗ Verification email failed to send")
            
    except Exception as e:
        print(f"   ✗ Error sending verification email: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Check what the response would be
    print("\n3. CHECKING RESPONSE DATA...")
    
    try:
        from apps.users.serializers import UserProfileSerializer
        
        include_token = settings.DEBUG or not getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', True)
        
        print(f"   DEBUG mode: {settings.DEBUG}")
        print(f"   REQUIRE_EMAIL_VERIFICATION: {getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', True)}")
        print(f"   Would include token: {include_token}")
        
        response_data = {
            'user': UserProfileSerializer(user).data,
            'message': 'Account created successfully!',
            'email_verification_required': True,
            'email_verification_sent': verification_sent
        }
        
        if verification_sent:
            response_data['verification_message'] = 'Please check your email to verify your account before logging in.'
        else:
            response_data['verification_message'] = 'Account created, but verification email could not be sent. Please contact support.'
        
        print(f"   Response would contain:")
        print(f"   - User data: {bool(response_data['user'])}")
        print(f"   - Email verification required: {response_data['email_verification_required']}")
        print(f"   - Email verification sent: {response_data['email_verification_sent']}")
        print(f"   - Message: {response_data['verification_message']}")
        
    except Exception as e:
        print(f"   ✗ Error creating response data: {e}")
    
    # Step 4: Clean up
    print(f"\n4. CLEANING UP...")
    try:
        user.delete()
        print("   ✓ Test user deleted")
    except:
        print("   ⚠ Could not delete test user")
    
    return verification_sent

def check_settings_configuration():
    """Check critical settings that affect email sending"""
    
    print("\n" + "="*60)
    print("CHECKING CRITICAL SETTINGS")
    print("="*60)
    
    print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"REQUIRE_EMAIL_VERIFICATION: {getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', 'Not set')}")
    print(f"FRONTEND_URL: {getattr(settings, 'FRONTEND_URL', 'Not set')}")
    
    # Check SendGrid settings
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if sendgrid_key:
        print(f"SENDGRID_API_KEY: {sendgrid_key[:15]}... (configured)")
    else:
        print("SENDGRID_API_KEY: Not configured")
    
    # Check email settings
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    print(f"EMAIL_VERIFICATION_SETTINGS: {email_settings}")
    
def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage: python debug_signup_flow.py your-email@example.com [username]")
        return
    
    test_email = sys.argv[1]
    test_username = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check settings first
    check_settings_configuration()
    
    # Test the complete signup flow
    success = test_complete_signup_flow(test_email, test_username)
    
    print(f"\n{'='*60}")
    if success:
        print("✓ SIGNUP FLOW TEST COMPLETED SUCCESSFULLY")
        print("If you're not receiving emails, check:")
        print("1. Spam folder")
        print("2. SendGrid activity feed for delivery status")
        print("3. Email address is correct")
    else:
        print("✗ SIGNUP FLOW TEST FAILED")
        print("Check the error messages above and fix the issues")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()