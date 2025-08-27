# apps/users/email_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from .email_utils import (
    send_verification_email, 
    verify_email_token, 
    can_resend_verification_email,
    is_verification_token_valid
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user's email address using verification token
    """
    token = request.data.get('token')
    
    if not token:
        return Response({
            'success': False,
            'message': 'Verification token is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user, message = verify_email_token(token)
    
    if user:
        return Response({
            'success': True,
            'message': message,
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
    email = request.data.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email address is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Check if email is already verified
        if user.email_verified:
            return Response({
                'success': False,
                'message': 'This email is already verified.'
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
                'message': 'Verification email has been sent.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        # Don't reveal that the email doesn't exist for security
        return Response({
            'success': True,
            'message': 'If an account with this email exists, a verification email has been sent.'
        }, status=status.HTTP_200_OK)

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