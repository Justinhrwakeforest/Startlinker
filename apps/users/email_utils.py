# apps/users/email_utils.py
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

def send_verification_email(user, request=None):
    """
    Send email verification email to user
    """
    try:
        # Generate new verification token
        user.email_verification_token = generate_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        
        # Get email settings
        email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
        from_email = email_settings.get('FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        subject_prefix = email_settings.get('SUBJECT_PREFIX', '[StartLinker] ')
        
        # Build verification URL
        if request:
            base_url = f"{request.scheme}://{request.get_host()}"
        else:
            base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            
        verification_url = f"{base_url}/auth/verify-email/{user.email_verification_token}"
        
        # Email content
        subject = f"{subject_prefix}Verify Your Email Address"
        
        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 14px; color: #666; }}
                .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">StartLinker</div>
                    <h2>Welcome to StartLinker!</h2>
                </div>
                <div class="content">
                    <h3>Hi {user.first_name or user.username}!</h3>
                    <p>Thank you for joining StartLinker, the premier platform for connecting startups, founders, and talent.</p>
                    <p>To complete your registration and start exploring opportunities, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify My Email</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #e5e7eb; padding: 10px; border-radius: 4px; font-family: monospace;">{verification_url}</p>
                    
                    <p><strong>This verification link will expire in 24 hours.</strong></p>
                    
                    <p>If you didn't create an account with us, you can safely ignore this email.</p>
                    
                    <div class="footer">
                        <p>Best regards,<br>The StartLinker Team</p>
                        <p style="font-size: 12px; color: #888;">
                            This is an automated email. Please do not reply to this message.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        plain_content = f"""
        Hi {user.first_name or user.username}!
        
        Thank you for joining StartLinker, the premier platform for connecting startups, founders, and talent.
        
        To complete your registration and start exploring opportunities, please verify your email address by visiting:
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create an account with us, you can safely ignore this email.
        
        Best regards,
        The StartLinker Team
        """
        
        # Send email
        success = send_mail(
            subject=subject,
            message=plain_content,
            from_email=from_email,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Verification email sent successfully to {user.email}")
            return True
        else:
            logger.error(f"Failed to send verification email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False

def is_verification_token_valid(user):
    """
    Check if the verification token is still valid (not expired)
    """
    if not user.email_verification_token or not user.email_verification_sent_at:
        return False
        
    # Get expiry hours from settings
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    expiry_hours = email_settings.get('VERIFICATION_TOKEN_EXPIRY_HOURS', 24)
    
    expiry_time = user.email_verification_sent_at + timedelta(hours=expiry_hours)
    return timezone.now() < expiry_time

def can_resend_verification_email(user):
    """
    Check if user can resend verification email (cooldown period check)
    """
    if not user.email_verification_sent_at:
        return True
        
    # Get cooldown minutes from settings
    email_settings = getattr(settings, 'EMAIL_VERIFICATION_SETTINGS', {})
    cooldown_minutes = email_settings.get('RESEND_COOLDOWN_MINUTES', 5)
    
    cooldown_time = user.email_verification_sent_at + timedelta(minutes=cooldown_minutes)
    return timezone.now() > cooldown_time

def verify_email_token(token):
    """
    Verify email token and return user if valid
    """
    from .models import User
    
    try:
        user = User.objects.get(email_verification_token=token)
        
        if not is_verification_token_valid(user):
            return None, "Verification token has expired. Please request a new verification email."
            
        # Mark email as verified
        user.email_verified = True
        user.email_verification_token = None  # Clear the token
        user.email_verification_sent_at = None
        user.save(update_fields=['email_verified', 'email_verification_token', 'email_verification_sent_at'])
        
        logger.info(f"Email verified successfully for user {user.email}")
        return user, "Email verified successfully!"
        
    except User.DoesNotExist:
        return None, "Invalid verification token."
    except Exception as e:
        logger.error(f"Error verifying email token {token}: {str(e)}")
        return None, "An error occurred during verification. Please try again."