# apps/users/urls.py
from django.urls import path
from .views import (
    UserRegistrationView, UserLoginView, UserLogoutView, UserProfileView,
    ChangePasswordView, user_interests, remove_user_interest, user_activity,
    export_user_data, user_bookmarks, user_stats, upload_profile_picture, delete_profile_picture,
    search_users, get_user_by_id, follow_user, unfollow_user, UserSettingsView,
    password_reset_request, password_reset_confirm, verify_reset_token, get_all_users_for_chat
)
from .api_views import (
    check_username_availability, validate_username_format,
    get_username_suggestions, generate_username_from_name,
    user_points_detail, user_points_history, user_stats_summary,
    user_achievements_list, achievements_leaderboard
)
from .achievements_api import user_achievements_summary
from .activity_api_views import user_activity_feed
from .resume_views import (
    resume_list_create, resume_detail, set_default_resume, get_default_resume
)
from .email_views import (
    verify_email, resend_verification_email, send_verification_to_email, 
    verification_status
)
from .admin_debug_views import (
    debug_email_config, test_email_send, reset_email_cooldowns,
    send_verification_debug, list_unverified_users
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('user/', UserProfileView.as_view(), name='user-current'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('interests/', user_interests, name='user-interests'),
    path('interests/<int:interest_id>/', remove_user_interest, name='remove-interest'),
    path('activity/', user_activity, name='user-activity'),
    path('export-data/', export_user_data, name='export-user-data'),
    path('bookmarks/', user_bookmarks, name='user-bookmarks'),
    path('stats/', user_stats, name='user-stats'),
    
    # Username validation and availability endpoints
    path('check-username/', check_username_availability, name='check-username'),
    path('validate-username/', validate_username_format, name='validate-username'),
    path('username-suggestions/', get_username_suggestions, name='username-suggestions'),
    path('generate-username/', generate_username_from_name, name='generate-username'),
    
    # Profile picture endpoints
    path('upload-profile-picture/', upload_profile_picture, name='upload-profile-picture'),
    path('delete-profile-picture/', delete_profile_picture, name='delete-profile-picture'),
    
    # User search and interaction endpoints
    path('search/', search_users, name='search-users'),
    path('chat-users/', get_all_users_for_chat, name='get-all-users-for-chat'),
    path('<int:user_id>/', get_user_by_id, name='get-user-by-id'),
    path('<int:user_id>/follow/', follow_user, name='follow-user'),
    path('<int:user_id>/unfollow/', unfollow_user, name='unfollow-user'),
    
    # Settings endpoint
    path('settings/', UserSettingsView.as_view(), name='user-settings'),
    
    # Password reset endpoints
    path('password-reset/', password_reset_request, name='password-reset-request'),
    path('password-reset/confirm/', password_reset_confirm, name='password-reset-confirm'),
    path('password-reset/verify/', verify_reset_token, name='verify-reset-token'),
    
    # Email verification endpoints
    path('verify-email/', verify_email, name='verify-email'),
    path('resend-verification/', resend_verification_email, name='resend-verification-email'),
    path('send-verification/', send_verification_to_email, name='send-verification-to-email'),
    path('verification-status/', verification_status, name='verification-status'),
    
    # Resume management endpoints
    path('resumes/', resume_list_create, name='resume-list-create'),
    path('resumes/<int:resume_id>/', resume_detail, name='resume-detail'),
    path('resumes/<int:resume_id>/set-default/', set_default_resume, name='resume-set-default'),
    path('resumes/default/', get_default_resume, name='resume-get-default'),
    
    # Points and achievements endpoints
    path('<int:user_id>/points/', user_points_detail, name='user-points-detail'),
    path('<int:user_id>/points/history/', user_points_history, name='user-points-history'),
    path('<int:user_id>/stats-summary/', user_stats_summary, name='user-stats-summary'),
    path('<int:user_id>/achievements/', user_achievements_list, name='user-achievements-list'),
    path('<int:user_id>/achievements-summary/', user_achievements_summary, name='user-achievements-summary'),
    path('<int:user_id>/activity-feed/', user_activity_feed, name='user-activity-feed'),
    path('leaderboard/', achievements_leaderboard, name='achievements-leaderboard'),
    
    # Admin debug endpoints (REMOVE IN PRODUCTION!)
    path('admin-debug/', debug_email_config, name='debug-email-config'),
    path('admin-debug/test-email/', test_email_send, name='test-email-send'),
    path('admin-debug/reset-cooldowns/', reset_email_cooldowns, name='reset-cooldowns'),
    path('admin-debug/send-verification/', send_verification_debug, name='send-verification-debug'),
    path('admin-debug/users/', list_unverified_users, name='list-unverified-users'),
]