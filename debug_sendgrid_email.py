"""
Debug script to test SendGrid email configuration on Render
Run this script on your Render service to diagnose email sending issues
"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings
from apps.users.email_utils import send_verification_email
from apps.users.models import User

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_sendgrid_configuration():
    """Test SendGrid configuration and environment variables"""
    
    print("=" * 60)
    print("SENDGRID EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # 1. Check if SendGrid API key is configured
    api_key = os.environ.get('SENDGRID_API_KEY')
    if api_key:
        print("✓ SENDGRID_API_KEY is configured")
        print(f"  API Key starts with: {api_key[:10]}...")
        print(f"  API Key length: {len(api_key)} characters")
    else:
        print("✗ SENDGRID_API_KEY is NOT configured!")
        print("  Please set SENDGRID_API_KEY environment variable on Render")
        return False
    
    # 2. Check email backend
    email_backend = getattr(settings, 'EMAIL_BACKEND', None)
    print(f"\nEmail Backend: {email_backend}")
    
    if email_backend == 'apps.users.sendgrid_backend.SendGridBackend':
        print("✓ Using custom SendGrid backend")
    else:
        print("✗ NOT using SendGrid backend!")
        print(f"  Current backend: {email_backend}")
    
    # 3. Check FROM email
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    print(f"\nDefault FROM Email: {from_email}")
    if from_email:
        print("✓ DEFAULT_FROM_EMAIL is configured")
    else:
        print("✗ DEFAULT_FROM_EMAIL is NOT configured!")
    
    # 4. Check if SendGrid backend can be imported
    try:
        from apps.users.sendgrid_backend import SendGridBackend
        backend = SendGridBackend()
        if backend.client:
            print("\n✓ SendGrid client initialized successfully")
        else:
            print("\n✗ SendGrid client failed to initialize")
            print("  Check API key configuration")
    except Exception as e:
        print(f"\n✗ Error importing SendGrid backend: {e}")
        return False
    
    # 5. Check FRONTEND_URL for verification links
    frontend_url = getattr(settings, 'FRONTEND_URL', None)
    print(f"\nFrontend URL: {frontend_url}")
    if not frontend_url:
        print("⚠ FRONTEND_URL not configured - using fallback")
        print("  Verification links may not work correctly")
    
    # 6. Check email verification settings
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    print("\nEmail Verification Settings:")
    for key, value in email_settings.items():
        print(f"  {key}: {value}")
    
    return True

def test_send_email(test_email=None):
    """Test sending an actual email"""
    
    print("\n" + "=" * 60)
    print("TESTING EMAIL SENDING")
    print("=" * 60)
    
    if not test_email:
        print("No test email provided. Usage: python debug_sendgrid_email.py test@example.com")
        return
    
    # Create or get a test user
    try:
        test_user = User.objects.get(email=test_email)
        print(f"Using existing user: {test_user.username}")
    except User.DoesNotExist:
        # Create a temporary test user
        import uuid
        test_user = User.objects.create(
            username=f"test_{uuid.uuid4().hex[:8]}",
            email=test_email,
            first_name="Test",
            last_name="User"
        )
        print(f"Created test user: {test_user.username}")
    
    # Try to send verification email
    print(f"\nSending verification email to: {test_email}")
    
    try:
        # Import send_mail directly to test
        from django.core.mail import send_mail
        
        # First test basic email sending
        print("\n1. Testing basic email sending...")
        result = send_mail(
            subject='Test Email from StartLinker',
            message='This is a test email to verify SendGrid configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        
        if result:
            print("✓ Basic email sent successfully!")
        else:
            print("✗ Basic email failed to send")
        
        # Now test verification email
        print("\n2. Testing verification email...")
        from apps.users.email_utils import send_verification_email
        success = send_verification_email(test_user)
        
        if success:
            print("✓ Verification email sent successfully!")
            print(f"  Check inbox for: {test_email}")
        else:
            print("✗ Verification email failed to send")
            print("  Check logs for details")
            
    except Exception as e:
        print(f"\n✗ Error sending email: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up test user if we created one
    if test_user.username.startswith("test_"):
        test_user.delete()
        print(f"\nCleaned up test user: {test_user.username}")

def main():
    """Main function"""
    
    # Test configuration
    config_ok = test_sendgrid_configuration()
    
    if not config_ok:
        print("\n⚠ Configuration issues detected. Please fix them before testing email sending.")
        return
    
    # Test email sending if email provided
    if len(sys.argv) > 1:
        test_email = sys.argv[1]
        test_send_email(test_email)
    else:
        print("\n" + "=" * 60)
        print("To test actual email sending, run:")
        print("python debug_sendgrid_email.py your-email@example.com")
        print("=" * 60)

if __name__ == "__main__":
    main()