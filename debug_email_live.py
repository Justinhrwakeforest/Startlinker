#!/usr/bin/env python3
"""
Debug email issues on live Render deployment
Run this in Render Shell to diagnose email problems
"""

import os
import django

# Set up Django for Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')

def debug_email_on_render():
    """Debug email configuration and sending on Render"""
    print("🔍 StartLinker Email Debug - Live Render Environment")
    print("=" * 60)
    
    try:
        django.setup()
        
        # Check environment variables
        print(f"\n1. Environment Variables:")
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        from_email = os.environ.get('DEFAULT_FROM_EMAIL')
        cors_debug = os.environ.get('CORS_DEBUG')
        
        print(f"   SENDGRID_API_KEY: {'✅ SET' if sendgrid_key else '❌ MISSING'}")
        print(f"   DEFAULT_FROM_EMAIL: {from_email or '❌ MISSING'}")
        print(f"   CORS_DEBUG: {cors_debug or 'Not set'}")
        
        if sendgrid_key:
            print(f"   Key preview: {sendgrid_key[:15]}...")
        
        # Check Django settings
        from django.conf import settings
        print(f"\n2. Django Email Settings:")
        print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"   DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   REQUIRE_EMAIL_VERIFICATION: {getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', 'Not set')}")
        
        # Test basic email sending
        print(f"\n3. Testing SendGrid Connection...")
        
        from django.core.mail import send_mail
        
        # Get a test email
        test_email = input("Enter your email for testing (or press Enter for default): ").strip()
        if not test_email:
            test_email = "test@example.com"
            
        print(f"   Testing email to: {test_email}")
        
        try:
            result = send_mail(
                subject="🔗 StartLinker - Live Render Email Test",
                message="This email confirms SendGrid is working on Render!",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@startlinker.com'),
                recipient_list=[test_email],
                html_message="""
                <html>
                    <body>
                        <h2>🎉 Live Render Email Test</h2>
                        <p>This email was sent from your live Render deployment!</p>
                        <ul>
                            <li>✅ SendGrid API working</li>
                            <li>✅ Django email backend working</li>
                            <li>✅ Email verification ready</li>
                        </ul>
                        <p><strong>Time:</strong> {datetime.now()}</p>
                    </body>
                </html>
                """,
                fail_silently=False
            )
            
            if result:
                print(f"   ✅ SUCCESS: Basic email sent!")
            else:
                print(f"   ❌ FAILED: Email sending returned 0")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Check recent user signups and verification status
        print(f"\n4. Checking Recent Users...")
        
        from django.contrib.auth import get_user_model
        from datetime import datetime, timedelta
        
        User = get_user_model()
        
        # Get recent unverified users
        yesterday = datetime.now() - timedelta(days=1)
        recent_users = User.objects.filter(
            date_joined__gte=yesterday,
            email_verified=False
        ).order_by('-date_joined')[:5]
        
        print(f"   Unverified users (last 24h): {recent_users.count()}")
        
        for user in recent_users:
            print(f"   📧 {user.email}")
            print(f"      Joined: {user.date_joined}")
            print(f"      Token: {'✅' if user.email_verification_token else '❌'}")
            print(f"      Last sent: {user.email_verification_sent_at or 'Never'}")
            print(f"      Verified: {'✅' if user.email_verified else '❌'}")
            print()
        
        # Test verification email function
        if recent_users.exists():
            print(f"\n5. Testing Verification Email Function...")
            
            from apps.users.email_utils import send_verification_email, can_resend_verification_email
            
            test_user = recent_users.first()
            print(f"   Testing with user: {test_user.email}")
            
            # Check cooldown
            can_resend = can_resend_verification_email(test_user)
            print(f"   Can resend: {'✅' if can_resend else '❌ (cooldown active)'}")
            
            if can_resend:
                try:
                    success = send_verification_email(test_user)
                    if success:
                        print(f"   ✅ SUCCESS: Verification email sent!")
                        test_user.refresh_from_db()
                        print(f"   Token: {test_user.email_verification_token[:20]}...")
                        print(f"   Sent at: {test_user.email_verification_sent_at}")
                    else:
                        print(f"   ❌ FAILED: Verification function returned False")
                except Exception as e:
                    print(f"   ❌ ERROR: {e}")
            else:
                print(f"   ⏳ COOLDOWN: Need to wait before resending")
        
        print(f"\n6. SendGrid Troubleshooting Tips:")
        print(f"   - Check spam/junk folder")
        print(f"   - Check 'Promotions' tab in Gmail")
        print(f"   - Verify sender in SendGrid dashboard")
        print(f"   - Check SendGrid activity logs")
        
        return True
        
    except Exception as e:
        print(f"❌ SETUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def reset_email_cooldowns():
    """Reset email verification cooldowns for testing"""
    try:
        print(f"\n🔄 Resetting Email Cooldowns...")
        
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Reset cooldowns by clearing sent_at timestamps
        unverified_users = User.objects.filter(email_verified=False)
        
        print(f"Found {unverified_users.count()} unverified users")
        
        for user in unverified_users:
            user.email_verification_sent_at = None
            user.save(update_fields=['email_verification_sent_at'])
            print(f"   Reset cooldown for: {user.email}")
        
        print(f"✅ Cooldowns reset! Users can now request verification emails again.")
        
    except Exception as e:
        print(f"❌ Error resetting cooldowns: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Full email debug")
    print("2. Reset email cooldowns")
    print("3. Both")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        debug_email_on_render()
    
    if choice in ['2', '3']:
        reset_email_cooldowns()
    
    print(f"\n🎯 Next Steps:")
    print(f"1. If emails still don't work, check SendGrid dashboard")
    print(f"2. Try signing up with a new email")
    print(f"3. Check all email folders (inbox, spam, promotions)")