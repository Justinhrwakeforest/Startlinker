# apps/users/gmail_friendly_email_utils.py
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

def send_gmail_friendly_verification_email(user, request=None):
    """
    Send email verification email optimized for Gmail delivery
    Uses patterns proven to work with Gmail's filters
    """
    try:
        # Generate new verification token
        user.email_verification_token = generate_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        
        # Get email settings
        email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
        from_email = 'noreply@startlinker.com'  # Use noreply@ as requested
        
        # Build verification URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/auth/verify-email/{user.email_verification_token}"
        
        # Gmail-friendly subject (avoid "verify" trigger words)
        subject = "Complete Your StartLinker Registration"
        
        # Simple HTML content (avoid complex styling that triggers spam filters)
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #f8f9fa; padding: 30px; text-align: center;">
        <h1 style="color: #333; margin: 0;">StartLinker</h1>
    </div>
    
    <div style="padding: 30px; background: white;">
        <h2>Welcome to StartLinker, {user.first_name or user.username}!</h2>
        
        <p>Thank you for joining our startup community. To complete your registration, please click the link below:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" 
               style="background: #007bff; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                Complete Registration
            </a>
        </div>
        
        <p>Or copy this link to your browser:</p>
        <p style="word-break: break-all; background: #f8f9fa; padding: 15px; border-radius: 5px;">
            {verification_url}
        </p>
        
        <p style="color: #666; font-size: 14px;">
            This link expires in 24 hours. If you didn't create an account, please ignore this email.
        </p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        
        <p style="color: #999; font-size: 12px; text-align: center;">
            StartLinker Team<br>
            This is an automated email. For support, contact support@startlinker.com
        </p>
    </div>
</body>
</html>
"""
        
        # Plain text version
        plain_content = f"""
Welcome to StartLinker!

Hi {user.first_name or user.username},

Thank you for joining our startup community. To complete your registration, please visit:

{verification_url}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
StartLinker Team

For support, contact: support@startlinker.com
"""
        
        # Create email with Gmail-friendly headers
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=f"StartLinker <{from_email}>",
            to=[user.email],
            headers={
                'Reply-To': 'support@startlinker.com',
                'List-Unsubscribe': '<mailto:unsubscribe@startlinker.com>',
                'X-Entity-Ref-ID': f'startlinker-reg-{user.id}'
            }
        )
        
        # Attach HTML alternative
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        success = email.send(fail_silently=False)
        
        if success:
            logger.info(f"Gmail-friendly verification email sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send verification email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def is_verification_token_valid(user):
    """Check if the verification token is still valid (not expired)"""
    if not user.email_verification_token or not user.email_verification_sent_at:
        return False
        
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    expiry_hours = email_settings.get('VERIFICATION_TOKEN_EXPIRY_HOURS', 24)
    
    expiry_time = user.email_verification_sent_at + timedelta(hours=expiry_hours)
    return timezone.now() < expiry_time

def can_resend_verification_email(user):
    """Check if user can resend verification email (cooldown period check)"""
    if not user.email_verification_sent_at:
        return True
        
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    cooldown_minutes = email_settings.get('RESEND_COOLDOWN_MINUTES', 5)
    
    cooldown_time = user.email_verification_sent_at + timedelta(minutes=cooldown_minutes)
    return timezone.now() > cooldown_time

def verify_email_token(token):
    """Verify email token and return user if valid"""
    from .models import User
    
    try:
        user = User.objects.get(email_verification_token=token)
        
        if not is_verification_token_valid(user):
            return None, "Verification token has expired. Please request a new verification email."
            
        # Mark email as verified
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None
        user.save(update_fields=['email_verified', 'email_verification_token', 'email_verification_sent_at'])
        
        logger.info(f"Email verified successfully for user {user.email}")
        return user, "Email verified successfully!"
        
    except User.DoesNotExist:
        return None, "Invalid verification token."
    except Exception as e:
        logger.error(f"Error verifying email token {token}: {str(e)}")
        return None, "An error occurred during verification. Please try again."