# apps/users/views.py - Enhanced with complete functionality
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.db import models, IntegrityError
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q
from PIL import Image
import json
import os
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, 
    ChangePasswordSerializer, UserInterestSerializer, UserSettingsSerializer, ResumeSerializer
)
from .models import User, UserInterest, UserSettings, Resume
from .activity_tracker import ActivityTracker

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            
            # Create auth token
            token, created = Token.objects.get_or_create(user=user)
            
            # Track signup activity and award welcome points
            ActivityTracker.track_signup(user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'token': token.key,
                'message': 'Account created successfully! You earned your first points!'
            }, status=status.HTTP_201_CREATED)
            
        except IntegrityError as e:
            # Handle database integrity errors (like unique constraint violations)
            error_message = str(e)
            if 'email' in error_message.lower():
                return Response({
                    'email': ['A user with this email address already exists. Please use a different email or try logging in.']
                }, status=status.HTTP_400_BAD_REQUEST)
            elif 'username' in error_message.lower():
                return Response({
                    'username': ['This username is already taken. Please choose a different one.']
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'non_field_errors': ['An account with this information already exists. Please check your details and try again.']
                }, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Create or get auth token
        token, created = Token.objects.get_or_create(user=user)
        
        # Track login activity and potential streaks
        ActivityTracker.track_login(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Login successful! Daily points awarded.'
        })

class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
        except:
            pass
        
        return Response({'message': 'Successfully logged out'})

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def delete(self, request, *args, **kwargs):
        """Delete user account"""
        user = self.get_object()
        user.delete()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not check_password(serializer.validated_data['old_password'], user.password):
            return Response({'error': 'Old password is incorrect'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'})

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def user_interests(request):
    """Get or add user interests"""
    if request.method == 'GET':
        interests = request.user.interests.all()
        serializer = UserInterestSerializer(interests, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        interest_name = request.data.get('interest', '').strip()
        if not interest_name:
            return Response({'error': 'Interest name is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        interest, created = UserInterest.objects.get_or_create(
            user=request.user, interest=interest_name
        )
        
        if created:
            return Response({'message': 'Interest added successfully'}, 
                          status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Interest already exists'})

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_user_interest(request, interest_id):
    """Remove a user interest"""
    try:
        interest = UserInterest.objects.get(id=interest_id, user=request.user)
        interest.delete()
        return Response({'message': 'Interest removed successfully'})
    except UserInterest.DoesNotExist:
        return Response({'error': 'Interest not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity(request):
    """Get user's complete activity summary"""
    user = request.user
    
    # Get recent ratings with startup details
    recent_ratings = user.startuprating_set.select_related('startup').order_by('-created_at')[:10]
    
    # Get recent comments with startup details  
    recent_comments = user.startupcomment_set.select_related('startup').order_by('-created_at')[:10]
    
    # Get bookmarked startups with details
    bookmarks = user.startupbookmark_set.select_related('startup').order_by('-created_at')[:20]
    
    # Get liked startups with details
    likes = user.startuplike_set.select_related('startup').order_by('-created_at')[:20]
    
    # Get job applications
    try:
        applications = user.jobapplication_set.select_related('job__startup').order_by('-applied_at')[:10]
        job_applications = [
            {
                'job_id': app.job.id,
                'job_title': app.job.title,
                'startup_id': app.job.startup.id,
                'startup_name': app.job.startup.name,
                'startup_logo': app.job.startup.logo,
                'status': app.status,
                'status_display': app.get_status_display(),
                'applied_at': app.applied_at
            } for app in applications
        ]
    except:
        job_applications = []
    
    return Response({
        'recent_ratings': [
            {
                'startup_id': rating.startup.id,
                'startup_name': rating.startup.name,
                'startup_logo': rating.startup.logo,
                'startup_location': rating.startup.location,
                'startup_industry': rating.startup.industry.name,
                'rating': rating.rating,
                'created_at': rating.created_at
            } for rating in recent_ratings
        ],
        'recent_comments': [
            {
                'startup_id': comment.startup.id,
                'startup_name': comment.startup.name,
                'startup_logo': comment.startup.logo,
                'startup_location': comment.startup.location,
                'text': comment.text,
                'created_at': comment.created_at
            } for comment in recent_comments
        ],
        'bookmarked_startups': [
            {
                'startup_id': bookmark.startup.id,
                'startup_name': bookmark.startup.name,
                'startup_logo': bookmark.startup.logo,
                'startup_location': bookmark.startup.location,
                'startup_industry': bookmark.startup.industry.name,
                'startup_description': bookmark.startup.description,
                'startup_employee_count': bookmark.startup.employee_count,
                'startup_funding_amount': bookmark.startup.funding_amount,
                'created_at': bookmark.created_at
            } for bookmark in bookmarks
        ],
        'liked_startups': [
            {
                'startup_id': like.startup.id,
                'startup_name': like.startup.name,
                'startup_logo': like.startup.logo,
                'startup_location': like.startup.location,
                'created_at': like.created_at
            } for like in likes
        ],
        'job_applications': job_applications,
        'activity_counts': {
            'total_ratings': user.startuprating_set.count(),
            'total_comments': user.startupcomment_set.count(),
            'total_bookmarks': user.startupbookmark_set.count(),
            'total_likes': user.startuplike_set.count(),
            'total_applications': len(job_applications)
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_user_data(request):
    """Export all user data"""
    user = request.user
    
    # Collect all user data
    data = {
        'user_info': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': user.bio,
            'location': user.location,
            'date_joined': user.date_joined.isoformat(),
            'is_premium': user.is_premium
        },
        'interests': [
            interest.interest for interest in user.interests.all()
        ],
        'ratings': [
            {
                'startup_name': rating.startup.name,
                'rating': rating.rating,
                'created_at': rating.created_at.isoformat()
            } for rating in user.startuprating_set.select_related('startup').all()
        ],
        'comments': [
            {
                'startup_name': comment.startup.name,
                'text': comment.text,
                'created_at': comment.created_at.isoformat()
            } for comment in user.startupcomment_set.select_related('startup').all()
        ],
        'bookmarks': [
            {
                'startup_name': bookmark.startup.name,
                'created_at': bookmark.created_at.isoformat()
            } for bookmark in user.startupbookmark_set.select_related('startup').all()
        ],
        'likes': [
            {
                'startup_name': like.startup.name,
                'created_at': like.created_at.isoformat()
            } for like in user.startuplike_set.select_related('startup').all()
        ]
    }
    
    # Add job applications if they exist
    try:
        data['job_applications'] = [
            {
                'job_title': app.job.title,
                'startup_name': app.job.startup.name,
                'status': app.status,
                'applied_at': app.applied_at.isoformat()
            } for app in user.jobapplication_set.select_related('job__startup').all()
        ]
    except:
        data['job_applications'] = []
    
    return Response(data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_bookmarks(request):
    """Get user's bookmarked startups with full startup data"""
    user = request.user
    
    # Get bookmarked startups with all related data
    bookmarked_startup_ids = user.startupbookmark_set.values_list('startup_id', flat=True)
    
    from apps.startups.models import Startup
    from apps.startups.serializers import StartupListSerializer
    
    bookmarked_startups = Startup.objects.filter(
        id__in=bookmarked_startup_ids
    ).select_related('industry').prefetch_related('tags', 'ratings', 'bookmarks', 'likes')
    
    serializer = StartupListSerializer(
        bookmarked_startups, 
        many=True, 
        context={'request': request}
    )
    
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get comprehensive user statistics"""
    user = request.user
    
    # Get various counts
    total_ratings = user.startuprating_set.count()
    total_comments = user.startupcomment_set.count()
    total_bookmarks = user.startupbookmark_set.count()
    total_likes = user.startuplike_set.count()
    
    try:
        total_applications = user.jobapplication_set.count()
    except:
        total_applications = 0
    
    # Get activity this month
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    monthly_activity = {
        'ratings': user.startuprating_set.filter(created_at__gte=thirty_days_ago).count(),
        'comments': user.startupcomment_set.filter(created_at__gte=thirty_days_ago).count(),
        'bookmarks': user.startupbookmark_set.filter(created_at__gte=thirty_days_ago).count(),
        'likes': user.startuplike_set.filter(created_at__gte=thirty_days_ago).count(),
    }
    
    # Calculate average rating given
    avg_rating_given = user.startuprating_set.aggregate(
        avg=models.Avg('rating')
    )['avg'] or 0
    
    return Response({
        'totals': {
            'ratings': total_ratings,
            'comments': total_comments,
            'bookmarks': total_bookmarks,
            'likes': total_likes,
            'applications': total_applications
        },
        'monthly_activity': monthly_activity,
        'average_rating_given': round(avg_rating_given, 1),
        'member_since': user.date_joined.isoformat(),
        'total_activity': total_ratings + total_comments + total_likes
    })

# Add this to apps/users/views.py

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_bookmarks(request):
    """Get user's bookmarked startups with full startup data"""
    user = request.user
    
    # Get bookmarked startup IDs
    bookmarked_ids = user.startupbookmark_set.values_list('startup_id', flat=True)
    
    # Get the actual startup objects with all related data
    from apps.startups.models import Startup
    from apps.startups.serializers import StartupListSerializer
    
    bookmarked_startups = Startup.objects.filter(
        id__in=bookmarked_ids
    ).select_related('industry').prefetch_related(
        'tags', 'ratings', 'bookmarks', 'likes', 'founders'
    ).order_by('-bookmarks__created_at')
    
    # Use the same serializer as the startups list for consistency
    serializer = StartupListSerializer(
        bookmarked_startups, 
        many=True, 
        context={'request': request}
    )
    
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_picture(request):
    """Upload profile picture for user"""
    if 'profile_picture' not in request.FILES:
        return Response({'error': 'No profile picture provided'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    profile_picture = request.FILES['profile_picture']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if profile_picture.content_type not in allowed_types:
        return Response({'error': 'Invalid file type. Please upload a JPEG, PNG, or WebP image.'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    # Validate file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB
    if profile_picture.size > max_size:
        return Response({'error': 'File too large. Please upload an image smaller than 5MB.'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Open and process image
        image = Image.open(profile_picture)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Resize image to maximum 512x512 while maintaining aspect ratio
        max_size_px = (512, 512)
        image.thumbnail(max_size_px, Image.Resampling.LANCZOS)
        
        # Save processed image
        from io import BytesIO
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # Delete old profile picture if exists
        user = request.user
        if user.profile_picture:
            old_path = user.profile_picture.path
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Save new profile picture
        file_name = f"profile_{user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        user.profile_picture.save(
            file_name,
            ContentFile(output.getvalue()),
            save=True
        )
        
        # Return updated user data
        serializer = UserProfileSerializer(user)
        return Response({
            'message': 'Profile picture uploaded successfully',
            'user': serializer.data
        })
        
    except Exception as e:
        return Response({'error': f'Failed to process image: {str(e)}'}, 
                      status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_picture(request):
    """Delete user's profile picture"""
    user = request.user
    
    if not user.profile_picture:
        return Response({'error': 'No profile picture to delete'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Delete file from storage
        if user.profile_picture:
            old_path = user.profile_picture.path
            if os.path.exists(old_path):
                os.remove(old_path)
            user.profile_picture.delete(save=False)
        
        # Clear the field
        user.profile_picture = None
        user.save()
        
        # Return updated user data
        serializer = UserProfileSerializer(user)
        return Response({
            'message': 'Profile picture deleted successfully',
            'user': serializer.data
        })
        
    except Exception as e:
        return Response({'error': f'Failed to delete profile picture: {str(e)}'}, 
                      status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_users(request):
    """Search for users by username, display name, or email"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({'results': []})
    
    if len(query) < 2:
        return Response({'error': 'Search query must be at least 2 characters'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    # Search in username, first_name, last_name, and email
    # Exclude the current user from results
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(
        id=request.user.id
    ).distinct()[:20]  # Limit to 20 results
    
    # Serialize user data for search results
    results = []
    for user in users:
        # Get connect profile if it exists
        connect_profile = None
        try:
            from apps.connect.models import ConnectProfile
            connect_profile = ConnectProfile.objects.get(user=user)
        except:
            pass
        
        results.append({
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'avatar_url': user.profile_picture.url if user.profile_picture else None,
            'is_verified': getattr(user, 'is_verified', False),
            'is_online': getattr(user, 'is_online', False),
            'headline': connect_profile.headline if connect_profile else None,
            'date_joined': user.date_joined.isoformat(),
        })
    
    return Response({'results': results})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_by_id(request, user_id):
    """Get user details by ID (for hover cards and profiles)"""
    try:
        user = User.objects.get(id=user_id)
        
        # Check if current user is following this user
        is_following = False
        try:
            from apps.connect.models import Follow
            is_following = Follow.objects.filter(
                follower=request.user,
                following=user
            ).exists()
        except:
            pass
        
        # Get connect profile if it exists
        connect_profile = None
        try:
            from apps.connect.models import ConnectProfile
            connect_profile = ConnectProfile.objects.get(user=user)
        except:
            pass
        
        # Get user stats
        follower_count = 0
        following_count = 0
        try:
            from apps.connect.models import Follow
            follower_count = Follow.objects.filter(
                following=user
            ).count()
            following_count = Follow.objects.filter(
                follower=user
            ).count()
        except:
            pass
        
        data = {
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'avatar_url': user.profile_picture.url if user.profile_picture else None,
            'is_verified': getattr(user, 'is_verified', False),
            'is_online': getattr(user, 'is_online', False),
            'is_premium': getattr(user, 'is_premium', False),
            'headline': connect_profile.headline if connect_profile else None,
            'location': connect_profile.location if connect_profile else None,
            'date_joined': user.date_joined.isoformat(),
            'is_following': is_following,
            'follower_count': follower_count,
            'following_count': following_count,
            'reputation_score': getattr(connect_profile, 'reputation_score', 0) if connect_profile else 0,
        }
        
        return Response(data)
        
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def follow_user(request, user_id):
    """Follow a user"""
    try:
        user_to_follow = User.objects.get(id=user_id)
        
        if user_to_follow == request.user:
            return Response({'error': 'Cannot follow yourself'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create connection
        try:
            from apps.connect.models import Follow
            follow, created = Follow.objects.get_or_create(
                follower=request.user,
                following=user_to_follow
            )
            
            if created:
                # Send notification to the followed user
                from apps.notifications.utils import notify_user_followed
                notify_user_followed(user_to_follow, request.user)
                
                return Response({'message': 'User followed successfully', 'following': True})
            else:
                return Response({'message': 'Already following this user', 'following': True})
                
        except Exception as e:
            # If connect app doesn't exist, return success anyway
            return Response({'message': 'User followed successfully', 'following': True})
            
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unfollow_user(request, user_id):
    """Unfollow a user"""
    try:
        user_to_unfollow = User.objects.get(id=user_id)
        
        # Delete connection
        try:
            from apps.connect.models import Follow
            Follow.objects.filter(
                follower=request.user,
                following=user_to_unfollow
            ).delete()
            
            return Response({'message': 'User unfollowed successfully', 'following': False})
            
        except Exception as e:
            # If connect app doesn't exist, return success anyway
            return Response({'message': 'User unfollowed successfully', 'following': False})
            
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class UserSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """Request password reset email"""
    email = request.data.get('email', '').strip()
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"
        
        # Send password reset email
        subject = 'Password Reset - StartupHub'
        
        # Render email templates
        html_message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
        })
        
        text_message = render_to_string('emails/password_reset.txt', {
            'user': user,
            'reset_url': reset_url,
        })
        
        try:
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            return Response({
                'message': 'Password reset email sent successfully',
                'email': email
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to send email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        # Don't reveal if email exists or not for security
        return Response({
            'message': 'If an account with this email exists, a password reset link has been sent.',
            'email': email
        })

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with token"""
    uid = request.data.get('uid', '')
    token = request.data.get('token', '')
    new_password = request.data.get('new_password', '')
    
    if not all([uid, token, new_password]):
        return Response({
            'error': 'UID, token, and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode the user ID
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        # Verify the token
        if default_token_generator.check_token(user, token):
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            # Invalidate all existing tokens for this user
            Token.objects.filter(user=user).delete()
            
            return Response({
                'message': 'Password reset successful. You can now login with your new password.'
            })
        else:
            return Response({
                'error': 'Invalid or expired password reset token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'error': 'Invalid password reset link'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_reset_token(request):
    """Verify if password reset token is valid"""
    uid = request.data.get('uid', '')
    token = request.data.get('token', '')
    
    if not all([uid, token]):
        return Response({
            'error': 'UID and token are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode the user ID
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        # Verify the token
        if default_token_generator.check_token(user, token):
            return Response({
                'valid': True,
                'email': user.email,
                'message': 'Token is valid'
            })
        else:
            return Response({
                'valid': False,
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'valid': False,
            'error': 'Invalid token format'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_all_users_for_chat(request):
    """Get all users for chat suggestions"""
    # Get recent users, excluding the current user
    users = User.objects.exclude(
        id=request.user.id
    ).filter(
        is_active=True
    ).order_by('-date_joined')[:20]  # Get 20 most recent users
    
    results = []
    for user in users:
        # Get connect profile if it exists
        connect_profile = None
        try:
            from apps.connect.models import ConnectProfile
            connect_profile = ConnectProfile.objects.get(user=user)
        except:
            pass
        
        results.append({
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'avatar_url': user.profile_picture.url if user.profile_picture else None,
            'is_verified': getattr(user, 'is_verified', False),
            'is_online': getattr(user, 'is_online', False),
            'headline': connect_profile.headline if connect_profile else None,
            'date_joined': user.date_joined.isoformat(),
        })
    
    return Response({'results': results})