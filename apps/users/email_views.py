# apps/users/email_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from .gmail_friendly_email_utils import (
    send_gmail_friendly_verification_email as send_verification_email, 
    verify_email_token, 
    can_resend_verification_email,
    is_verification_token_valid
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user's email address using verification token
    Supports both GET (from email links) and POST (from frontend forms)
    """
    # Get token from either GET params or POST data
    token = request.GET.get('token') or request.data.get('token')
    
    if not token:
        return Response({
            'success': False,
            'message': 'Verification token is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user, message = verify_email_token(token)
    
    # Handle GET requests (email clicks) with redirect
    if request.method == 'GET':
        from django.conf import settings
        from django.shortcuts import redirect
        from django.http import HttpResponse
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://startlinker-frontend.onrender.com')
        
        if user:
            # Redirect to login page with success message
            redirect_url = f"{frontend_url}/login?verified=true&message=Your email has been verified! Please log in to continue."
            return redirect(redirect_url)
        else:
            # Redirect to login page with error message
            redirect_url = f"{frontend_url}/login?error=true&message=Verification failed. Please try again or request a new verification email."
            return redirect(redirect_url)
    
    # Handle POST requests (API calls) with JSON response
    else:
        if user:
            return Response({
                'success': True,
                'message': message,
                'redirect_to_login': True,  # Tell frontend to redirect to login
                'login_message': 'Your email has been verified! Please log in to continue.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'email_verified': user.email_verified
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email(request):
    """
    Resend email verification email to authenticated user
    """
    user = request.user
    
    # Check if email is already verified
    if user.email_verified:
        return Response({
            'success': False,
            'message': 'Your email is already verified.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check cooldown period
    if not can_resend_verification_email(user):
        return Response({
            'success': False,
            'message': 'Please wait a few minutes before requesting another verification email.'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Send verification email
    success = send_verification_email(user, request)
    
    if success:
        return Response({
            'success': True,
            'message': 'Verification email has been sent to your email address.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': 'Failed to send verification email. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_to_email(request):
    """
    Send verification email to a specific email address (for registration flow)
    """
    import json
    
    try:
        # Try multiple ways to get the email
        email = None
        
        # Method 1: request.data (DRF standard)
        if hasattr(request, 'data') and request.data:
            email = request.data.get('email')
            logger.info(f"Got email from request.data: {email}")
        
        # Method 2: JSON body
        if not email and request.body:
            try:
                data = json.loads(request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body)
                email = data.get('email')
                logger.info(f"Got email from JSON body: {email}")
            except (json.JSONDecodeError, UnicodeDecodeError) as json_error:
                logger.warning(f"Failed to parse JSON body: {json_error}")
        
        # Method 3: POST data
        if not email:
            email = request.POST.get('email')
            if email:
                logger.info(f"Got email from POST data: {email}")
        
        logger.info(f"Final email value: {email}")
        
    except Exception as e:
        logger.error(f"Error parsing request in send_verification_to_email: {str(e)}")
        return Response({
            'success': False,
            'message': 'Invalid request format.',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email address is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        logger.info(f"Found user for verification: {user.username} ({email})")
        
        # Check if email is already verified
        if user.email_verified:
            logger.info(f"Email already verified for user: {user.username}")
            return Response({
                'success': False,
                'message': 'This email is already verified.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check cooldown period
        if not can_resend_verification_email(user):
            logger.info(f"Cooldown period active for user: {user.username}")
            return Response({
                'success': False,
                'message': 'Please wait a few minutes before requesting another verification email.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Send verification email
        logger.info(f"Attempting to send verification email to: {email}")
        success = send_verification_email(user, request)
        
        if success:
            logger.info(f"Verification email sent successfully to: {email}")
            return Response({
                'success': True,
                'message': 'Verification email has been sent.'
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Failed to send verification email to: {email}")
            return Response({
                'success': False,
                'message': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        # Don't reveal that the email doesn't exist for security
        logger.info(f"User does not exist for email: {email}")
        return Response({
            'success': True,
            'message': 'If an account with this email exists, a verification email has been sent.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in send_verification_to_email: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verification_status(request):
    """
    Get email verification status for authenticated user
    """
    user = request.user
    
    data = {
        'email_verified': user.email_verified,
        'email': user.email
    }
    
    # If not verified, add token status
    if not user.email_verified:
        data.update({
            'has_pending_verification': bool(user.email_verification_token),
            'can_resend': can_resend_verification_email(user),
            'token_valid': is_verification_token_valid(user) if user.email_verification_token else False
        })
    
    return Response({
        'success': True,
        'data': data
    }, status=status.HTTP_200_OK)