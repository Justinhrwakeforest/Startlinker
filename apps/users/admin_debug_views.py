"""
Admin debugging views that work without Shell access
Accessible via /api/auth/admin-debug/ endpoints
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # Temporary for debugging
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import os
import logging

from .email_utils import send_verification_email, can_resend_verification_email

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])  # REMOVE THIS IN PRODUCTION!
def debug_email_config(request):
    """Debug email configuration - accessible via browser"""
    
    # Check environment variables
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    from_email = os.environ.get('DEFAULT_FROM_EMAIL')
    
    # Check Django settings
    email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
    default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')
    debug_mode = settings.DEBUG
    require_verification = getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False)
    
    # Check recent unverified users
    yesterday = datetime.now() - timedelta(days=1)
    recent_unverified = User.objects.filter(
        date_joined__gte=yesterday,
        email_verified=False
    ).count()
    
    total_unverified = User.objects.filter(email_verified=False).count()
    
    return Response({
        'status': 'Email Configuration Debug',
        'environment_variables': {
            'SENDGRID_API_KEY': 'SET' if sendgrid_key else 'MISSING',
            'DEFAULT_FROM_EMAIL': from_email or 'MISSING',
            'sendgrid_key_preview': sendgrid_key[:15] + '...' if sendgrid_key else None
        },
        'django_settings': {
            'EMAIL_BACKEND': email_backend,
            'DEFAULT_FROM_EMAIL': default_from,
            'DEBUG': debug_mode,
            'REQUIRE_EMAIL_VERIFICATION': require_verification
        },
        'user_stats': {
            'unverified_users_total': total_unverified,
            'unverified_users_last_24h': recent_unverified
        },
        'next_steps': [
            'Visit /api/auth/admin-debug/test-email/ to test sending',
            'Visit /api/auth/admin-debug/reset-cooldowns/ to reset rate limits',
            'Visit /api/auth/admin-debug/send-verification/ to send test verification'
        ]
    })

@api_view(['POST'])
@permission_classes([AllowAny])  # REMOVE THIS IN PRODUCTION!
def test_email_send(request):
    """Test sending email via SendGrid - accessible via POST request"""
    
    email = request.data.get('email')
    if not email:
        return Response({
            'error': 'Email address required in POST data'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = send_mail(
            subject='🔗 StartLinker - Email Test from API',
            message='This email was sent via the debug API endpoint!',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@startlinker.com'),
            recipient_list=[email],
            html_message=f'''
            <html>
                <body>
                    <h2>🎉 Email Test Success!</h2>
                    <p>This email confirms that:</p>
                    <ul>
                        <li>✅ SendGrid is configured correctly</li>
                        <li>✅ Email backend is working</li>
                        <li>✅ API endpoint is functional</li>
                    </ul>
                    <p><strong>Test time:</strong> {datetime.now()}</p>
                    <p>Your email verification should now work!</p>
                </body>
            </html>
            ''',
            fail_silently=False
        )
        
        return Response({
            'success': True,
            'message': f'Test email sent to {email}',
            'result': bool(result),
            'instructions': 'Check your inbox, spam, and promotions folder'
        })
        
    except Exception as e:
        logger.error(f"Email test failed: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Email sending failed - check SendGrid configuration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])  # REMOVE THIS IN PRODUCTION!
def reset_email_cooldowns(request):
    """Reset email verification cooldowns for all users"""
    
    try:
        # Reset cooldowns by clearing sent_at timestamps
        updated_count = User.objects.filter(
            email_verified=False,
            email_verification_sent_at__isnull=False
        ).update(email_verification_sent_at=None)
        
        return Response({
            'success': True,
            'message': f'Reset email cooldowns for {updated_count} users',
            'instructions': 'Users can now request verification emails again'
        })
        
    except Exception as e:
        logger.error(f"Cooldown reset failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])  # REMOVE THIS IN PRODUCTION!
def send_verification_debug(request):
    """Send verification email to specific user - for debugging"""
    
    email = request.data.get('email')
    if not email:
        return Response({
            'error': 'Email address required in POST data'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Reset cooldown for this user
        user.email_verification_sent_at = None
        user.save(update_fields=['email_verification_sent_at'])
        
        # Send verification email
        success = send_verification_email(user)
        
        if success:
            user.refresh_from_db()
            return Response({
                'success': True,
                'message': f'Verification email sent to {email}',
                'user_info': {
                    'email': user.email,
                    'email_verified': user.email_verified,
                    'token_generated': bool(user.email_verification_token),
                    'sent_at': user.email_verification_sent_at
                }
            })
        else:
            return Response({
                'success': False,
                'message': 'Verification email sending failed',
                'user_info': {
                    'email': user.email,
                    'email_verified': user.email_verified
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        return Response({
            'error': f'User with email {email} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Verification debug failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])  # REMOVE THIS IN PRODUCTION!
def list_unverified_users(request):
    """List recent unverified users for debugging"""
    
    try:
        # Get unverified users from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        unverified_users = User.objects.filter(
            email_verified=False,
            date_joined__gte=week_ago
        ).order_by('-date_joined')[:20]
        
        users_data = []
        for user in unverified_users:
            users_data.append({
                'email': user.email,
                'date_joined': user.date_joined,
                'has_token': bool(user.email_verification_token),
                'last_sent': user.email_verification_sent_at,
                'can_resend': can_resend_verification_email(user)
            })
        
        return Response({
            'unverified_users': users_data,
            'count': len(users_data),
            'instructions': 'Use /api/auth/admin-debug/send-verification/ to send emails to these users'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)