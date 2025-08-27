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

from django.contrib.auth import get_user_model
from apps.users.email_utils import send_verification_email
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

def send_fresh_verification():
    """Send a fresh verification email to codingcobby@gmail.com"""
    try:
        print("=== Sending Fresh Verification Email ===")
        
        # Get the user
        user = User.objects.get(email="codingcobby@gmail.com")
        print(f"Found user: {user.email}")
        print(f"User joined: {user.date_joined}")
        print(f"Email verified: {user.email_verified}")
        print(f"Current token: {user.email_verification_token[:20] if user.email_verification_token else 'None'}")
        
        # Send verification email
        print(f"\nSending verification email...")
        success = send_verification_email(user)
        
        if success:
            user.refresh_from_db()
            print(f"SUCCESS: Verification email sent!")
            print(f"New token generated: {user.email_verification_token[:20]}...")
            print(f"Sent at: {user.email_verification_sent_at}")
            
            # Also send a direct test email
            print(f"\nSending additional test email...")
            result = send_mail(
                subject="🔗 StartLinker Email Test - Direct Delivery",
                message="This is a direct test email to verify delivery.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["codingcobby@gmail.com"],
                html_message="""
                <html>
                    <body>
                        <h2>📧 StartLinker Email Test</h2>
                        <p>If you receive this email, it means:</p>
                        <ul>
                            <li>✅ Email delivery is working</li>
                            <li>✅ Your verification emails should arrive</li>
                            <li>✅ Check your spam folder if you don't see verification emails</li>
                        </ul>
                        <p><strong>Next steps:</strong></p>
                        <ol>
                            <li>Check your spam/junk folder</li>
                            <li>Check "Promotions" tab in Gmail</li>
                            <li>Add noreply@startlinker.com to your contacts</li>
                        </ol>
                        <p>Email sent from: {}</p>
                    </body>
                </html>
                """.format(settings.DEFAULT_FROM_EMAIL),
                fail_silently=False
            )
            
            if result:
                print(f"SUCCESS: Test email also sent!")
            else:
                print(f"WARNING: Test email may have failed")
                
        else:
            print(f"FAILED: Could not send verification email")
            
        return success
        
    except User.DoesNotExist:
        print(f"ERROR: User codingcobby@gmail.com not found")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = send_fresh_verification()
    
    if success:
        print(f"\n🎯 EMAILS SENT!")
        print(f"Check your email: codingcobby@gmail.com")
        print(f"Look in these locations:")
        print(f"  1. Inbox (primary)")
        print(f"  2. Spam/Junk folder")
        print(f"  3. Promotions tab (Gmail)")
        print(f"  4. From: noreply@startlinker.com")
        print(f"\nIf still not received, check SendGrid dashboard for delivery status")
    else:
        print(f"\n❌ Email sending failed - check error messages above")