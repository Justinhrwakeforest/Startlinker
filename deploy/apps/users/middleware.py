# apps/users/middleware.py - Middleware for tracking user login streaks
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .social_models import UserLoginStreak

@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """Track user login for streak calculation and daily points"""
    try:
        UserLoginStreak.update_login_streak(user)
    except Exception as e:
        # Log the error but don't fail the login process
        pass