from rest_framework import permissions
from django.contrib.auth import get_user_model
from .models import Subscription, SubscriptionPlan, SubscriptionUsage
from django.utils import timezone

User = get_user_model()

class SubscriptionPermission(permissions.BasePermission):
    """Base permission class for subscription-based features"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow staff users to access everything
        if request.user.is_staff:
            return True
        
        return self.check_subscription_permission(request.user)
    
    def check_subscription_permission(self, user):
        """Override this method in subclasses to check specific subscription requirements"""
        return True

class IsPremiumUser(SubscriptionPermission):
    """Permission for premium users only"""
    
    def check_subscription_permission(self, user):
        return user.is_pro() or user.is_enterprise()

class IsProUser(SubscriptionPermission):
    """Permission for Pro users and above"""
    
    def check_subscription_permission(self, user):
        return user.is_pro() or user.is_enterprise()

class IsEnterpriseUser(SubscriptionPermission):
    """Permission for Enterprise users only"""
    
    def check_subscription_permission(self, user):
        return user.is_enterprise()

class HasActiveSubscription(SubscriptionPermission):
    """Permission for users with active subscriptions"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.is_active()
        except Subscription.DoesNotExist:
            return False

class CanClaimStartups(SubscriptionPermission):
    """Permission for users who can claim startups"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.plan.can_claim_startups and subscription.is_active()
        except Subscription.DoesNotExist:
            return False

class CanEditStartups(SubscriptionPermission):
    """Permission for users who can edit startups"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.plan.can_edit_startups and subscription.is_active()
        except Subscription.DoesNotExist:
            return False

class HasAnalyticsAccess(SubscriptionPermission):
    """Permission for users with analytics access"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.plan.analytics_access and subscription.is_active()
        except Subscription.DoesNotExist:
            return False

class HasAdvancedSearch(SubscriptionPermission):
    """Permission for users with advanced search features"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.plan.advanced_search and subscription.is_active()
        except Subscription.DoesNotExist:
            return False

class HasPrioritySupport(SubscriptionPermission):
    """Permission for users with priority support"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.plan.priority_support and subscription.is_active()
        except Subscription.DoesNotExist:
            return False

class CanSubmitStartup(SubscriptionPermission):
    """Permission for users who can submit startups based on their plan limits"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.is_active():
                return False
            
            # Get current usage
            now = timezone.now()
            current_period_start = subscription.current_period_start or now.replace(day=1)
            
            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=subscription,
                period_start=current_period_start,
                defaults={
                    'period_end': subscription.current_period_end or (now + timezone.timedelta(days=30))
                }
            )
            
            return usage.can_submit_startup()
        except Subscription.DoesNotExist:
            return False

class CanApplyToJob(SubscriptionPermission):
    """Permission for users who can apply to jobs based on their plan limits"""
    
    def check_subscription_permission(self, user):
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.is_active():
                return False
            
            # Get current usage
            now = timezone.now()
            current_period_start = subscription.current_period_start or now.replace(day=1)
            
            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=subscription,
                period_start=current_period_start,
                defaults={
                    'period_end': subscription.current_period_end or (now + timezone.timedelta(days=30))
                }
            )
            
            return usage.can_apply_to_job()
        except Subscription.DoesNotExist:
            return False

class SubscriptionFeaturePermission(permissions.BasePermission):
    """Generic permission class for subscription features"""
    
    def __init__(self, feature_name):
        self.feature_name = feature_name
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow staff users to access everything
        if request.user.is_staff:
            return True
        
        try:
            subscription = Subscription.objects.get(user=request.user)
            if not subscription.is_active():
                return False
            
            # Check if the plan has the specific feature
            return getattr(subscription.plan, self.feature_name, False)
        except Subscription.DoesNotExist:
            return False

# Helper functions for checking permissions programmatically
def user_can_claim_startups(user):
    """Check if user can claim startups"""
    if user.is_staff:
        return True
    
    try:
        subscription = Subscription.objects.get(user=user)
        return subscription.plan.can_claim_startups and subscription.is_active()
    except Subscription.DoesNotExist:
        return False

def user_can_edit_startups(user):
    """Check if user can edit startups"""
    if user.is_staff:
        return True
    
    try:
        subscription = Subscription.objects.get(user=user)
        return subscription.plan.can_edit_startups and subscription.is_active()
    except Subscription.DoesNotExist:
        return False

def user_has_analytics_access(user):
    """Check if user has analytics access"""
    if user.is_staff:
        return True
    
    try:
        subscription = Subscription.objects.get(user=user)
        return subscription.plan.analytics_access and subscription.is_active()
    except Subscription.DoesNotExist:
        return False

def user_has_advanced_search(user):
    """Check if user has advanced search"""
    if user.is_staff:
        return True
    
    try:
        subscription = Subscription.objects.get(user=user)
        return subscription.plan.advanced_search and subscription.is_active()
    except Subscription.DoesNotExist:
        return False

def user_can_submit_startup(user):
    """Check if user can submit another startup"""
    if user.is_staff:
        return True
    
    try:
        subscription = Subscription.objects.get(user=user)
        if not subscription.is_active():
            return False
        
        # Get current usage
        now = timezone.now()
        current_period_start = subscription.current_period_start or now.replace(day=1)
        
        usage, created = SubscriptionUsage.objects.get_or_create(
            subscription=subscription,
            period_start=current_period_start,
            defaults={
                'period_end': subscription.current_period_end or (now + timezone.timedelta(days=30))
            }
        )
        
        return usage.can_submit_startup()
    except Subscription.DoesNotExist:
        return False

def user_can_apply_to_job(user):
    """Check if user can apply to another job"""
    if user.is_staff:
        return True
    
    try:
        subscription = Subscription.objects.get(user=user)
        if not subscription.is_active():
            return False
        
        # Get current usage
        now = timezone.now()
        current_period_start = subscription.current_period_start or now.replace(day=1)
        
        usage, created = SubscriptionUsage.objects.get_or_create(
            subscription=subscription,
            period_start=current_period_start,
            defaults={
                'period_end': subscription.current_period_end or (now + timezone.timedelta(days=30))
            }
        )
        
        return usage.can_apply_to_job()
    except Subscription.DoesNotExist:
        return False

def get_user_subscription_limits(user):
    """Get user's subscription limits"""
    if user.is_staff:
        return {
            'max_startup_submissions': 999999,  # Use large number instead of infinity
            'max_job_applications': 999999,  # Use large number instead of infinity
            'can_claim_startups': True,
            'can_edit_startups': True,
            'analytics_access': True,
            'advanced_search': True,
            'priority_support': True,
            'verified_badge': True
        }
    
    try:
        subscription = Subscription.objects.get(user=user)
        if not subscription.is_active():
            return {
                'max_startup_submissions': 0,
                'max_job_applications': 0,
                'can_claim_startups': False,
                'can_edit_startups': False,
                'analytics_access': False,
                'advanced_search': False,
                'priority_support': False,
                'verified_badge': False
            }
        
        return {
            'max_startup_submissions': subscription.plan.max_startup_submissions,
            'max_job_applications': subscription.plan.max_job_applications,
            'can_claim_startups': subscription.plan.can_claim_startups,
            'can_edit_startups': subscription.plan.can_edit_startups,
            'analytics_access': subscription.plan.analytics_access,
            'advanced_search': subscription.plan.advanced_search,
            'priority_support': subscription.plan.priority_support,
            'verified_badge': subscription.plan.verified_badge
        }
    except Subscription.DoesNotExist:
        # Return free tier limits
        return {
            'max_startup_submissions': 1,
            'max_job_applications': 5,
            'can_claim_startups': False,
            'can_edit_startups': False,
            'analytics_access': False,
            'advanced_search': False,
            'priority_support': False,
            'verified_badge': False
        }

def get_user_subscription_usage(user):
    """Get user's current subscription usage"""
    if user.is_staff:
        return {
            'startup_submissions_used': 0,
            'job_applications_used': 0,
            'startup_submissions_remaining': 999999,  # Use large number instead of infinity
            'job_applications_remaining': 999999  # Use large number instead of infinity
        }
    
    try:
        subscription = Subscription.objects.get(user=user)
        if not subscription.is_active():
            return {
                'startup_submissions_used': 0,
                'job_applications_used': 0,
                'startup_submissions_remaining': 0,
                'job_applications_remaining': 0
            }
        
        # Get current usage
        now = timezone.now()
        current_period_start = subscription.current_period_start or now.replace(day=1)
        
        usage, created = SubscriptionUsage.objects.get_or_create(
            subscription=subscription,
            period_start=current_period_start,
            defaults={
                'period_end': subscription.current_period_end or (now + timezone.timedelta(days=30))
            }
        )
        
        return {
            'startup_submissions_used': usage.startup_submissions_used,
            'job_applications_used': usage.job_applications_used,
            'startup_submissions_remaining': max(0, subscription.plan.max_startup_submissions - usage.startup_submissions_used),
            'job_applications_remaining': max(0, subscription.plan.max_job_applications - usage.job_applications_used)
        }
    except Subscription.DoesNotExist:
        return {
            'startup_submissions_used': 0,
            'job_applications_used': 0,
            'startup_submissions_remaining': 1,
            'job_applications_remaining': 5
        }