import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.email_utils import send_verification_email
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

def create_and_test_user():
    """Create a test user and send verification email"""
    try:
        email = "justinhrwakeforest536@gmail.com"
        
        # Create or get the user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': 'Justinhr',
                'first_name': 'Justin',
                'last_name': 'HR'
            }
        )
        
        print(f"User: {user.username} ({user.email}) - {'Created' if created else 'Already existed'}")
        print(f"Email verified: {user.email_verified}")
        print(f"Has verification token: {bool(user.email_verification_token)}")
        
        # Send a simple test email first
        print(f"\n1. Sending simple test email to {email}...")
        try:
            test_result = send_mail(
                subject="Test Email from StartLinker - Direct Test",
                message="This is a simple test email to check if SendGrid is working.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message="""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #4a90e2;">Test Email from StartLinker</h2>
                            <p>Hello! This is a test email to verify that SendGrid email delivery is working correctly.</p>
                            <p>If you receive this email, it means:</p>
                            <ul>
                                <li>SUCCESS: SendGrid API key is valid</li>
                                <li>SUCCESS: Email configuration is correct</li>
                                <li>SUCCESS: Email delivery is working</li>
                            </ul>
                            <p>Thank you for testing!</p>
                            <hr>
                            <p style="font-size: 12px; color: #666;">
                                This is a test email from StartLinker platform.
                            </p>
                        </div>
                    </body>
                </html>
                """,
                fail_silently=False,
            )
            
            if test_result:
                print("SUCCESS: Simple test email sent successfully")
            else:
                print("FAILED: Simple test email failed")
        except Exception as e:
            print(f"ERROR sending simple email: {e}")
            
        # Now send the verification email
        print(f"\n2. Sending verification email to {email}...")
        try:
            success = send_verification_email(user)
            
            if success:
                print("SUCCESS: Verification email sent successfully")
                user.refresh_from_db()
                print(f"   - Token generated: {bool(user.email_verification_token)}")
                print(f"   - Token: {user.email_verification_token[:20]}..." if user.email_verification_token else "No token")
                print(f"   - Sent at: {user.email_verification_sent_at}")
            else:
                print("FAILED: Verification email failed")
        except Exception as e:
            print(f"ERROR sending verification email: {e}")
            
        print(f"\nEmail Configuration Check:")
        print(f"   - FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   - EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"   - SANDBOX_MODE: {getattr(settings, 'SENDGRID_SANDBOX_MODE_IN_DEBUG', 'Not set')}")
        print(f"   - API_KEY: {settings.SENDGRID_API_KEY[:10]}..." if settings.SENDGRID_API_KEY else "No API key")
        
        print(f"\nTroubleshooting Tips:")
        print(f"   1. Check your inbox AND spam/junk folder")
        print(f"   2. Look for emails from: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   3. If using Gmail, check the 'Promotions' tab")
        print(f"   4. Wait a few minutes for delivery")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_and_test_user()