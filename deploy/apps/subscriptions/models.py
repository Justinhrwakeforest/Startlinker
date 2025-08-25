from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import stripe
from django.conf import settings
import uuid

User = get_user_model()

class SubscriptionPlan(models.Model):
    """Define subscription plans and pricing"""
    PLAN_TYPES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    interval = models.CharField(max_length=10, choices=[
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    ], default='month')
    
    # Features
    max_startup_submissions = models.IntegerField(default=1)
    max_job_applications = models.IntegerField(default=5)
    can_claim_startups = models.BooleanField(default=False)
    can_edit_startups = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    advanced_search = models.BooleanField(default=False)
    verified_badge = models.BooleanField(default=False)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
        
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.interval}"
    
    def is_free(self):
        return self.plan_type == 'free'
    
    def is_pro(self):
        return self.plan_type == 'pro'
    
    def is_enterprise(self):
        return self.plan_type == 'enterprise'

class Subscription(models.Model):
    """User subscription model"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('paused', 'Paused'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    
    # Stripe fields
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Billing dates
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['active', 'trialing']
    
    @property
    def is_active_pro(self):
        """Check if subscription is active and Pro plan"""
        return self.is_active() and self.plan.is_pro()
    
    def is_trial(self):
        """Check if subscription is in trial period"""
        return self.status == 'trialing'
    
    def is_canceled(self):
        """Check if subscription is canceled"""
        return self.status == 'canceled'
    
    def days_until_expiry(self):
        """Get days until subscription expires"""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - timezone.now()
        return delta.days if delta.days > 0 else 0
    
    def is_past_due(self):
        """Check if subscription is past due"""
        return self.status == 'past_due'
    
    def cancel(self):
        """Cancel subscription"""
        if self.stripe_subscription_id:
            try:
                stripe.Subscription.modify(
                    self.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                self.status = 'canceled'
                self.canceled_at = timezone.now()
                self.save()
                return True
            except stripe.error.StripeError as e:
                print(f"Error canceling subscription: {e}")
                return False
        return False
    
    def resume(self):
        """Resume canceled subscription"""
        if self.stripe_subscription_id and self.status == 'canceled':
            try:
                stripe.Subscription.modify(
                    self.stripe_subscription_id,
                    cancel_at_period_end=False
                )
                self.status = 'active'
                self.canceled_at = None
                self.save()
                return True
            except stripe.error.StripeError as e:
                print(f"Error resuming subscription: {e}")
                return False
        return False

class PaymentHistory(models.Model):
    """Track payment history for subscriptions"""
    PAYMENT_STATUS_CHOICES = [
        ('succeeded', 'Succeeded'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    
    # Payment details
    payment_method_type = models.CharField(max_length=50, blank=True, null=True)  # card, bank_transfer, etc.
    last_four = models.CharField(max_length=4, blank=True, null=True)  # Last 4 digits of card
    brand = models.CharField(max_length=20, blank=True, null=True)  # visa, mastercard, etc.
    
    # Dates
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Payment {self.id} - {self.subscription.user.username} - ${self.amount} ({self.status})"
    
    def is_successful(self):
        return self.status == 'succeeded'
    
    def is_failed(self):
        return self.status == 'failed'
    
    def is_refunded(self):
        return self.status == 'refunded'

class SubscriptionUsage(models.Model):
    """Track usage metrics for subscriptions"""
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage_records')
    
    # Usage metrics
    startup_submissions_used = models.IntegerField(default=0)
    job_applications_used = models.IntegerField(default=0)
    api_calls_used = models.IntegerField(default=0)
    
    # Reset period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_start']
        unique_together = ['subscription', 'period_start']
        
    def __str__(self):
        return f"Usage for {self.subscription.user.username} - {self.period_start.strftime('%Y-%m')}"
    
    def can_submit_startup(self):
        """Check if user can submit another startup"""
        return self.startup_submissions_used < self.subscription.plan.max_startup_submissions
    
    def can_apply_to_job(self):
        """Check if user can apply to another job"""
        return self.job_applications_used < self.subscription.plan.max_job_applications
    
    def increment_startup_submissions(self):
        """Increment startup submissions counter"""
        self.startup_submissions_used += 1
        self.save()
    
    def increment_job_applications(self):
        """Increment job applications counter"""
        self.job_applications_used += 1
        self.save()
    
    def reset_usage(self):
        """Reset usage counters for new period"""
        self.startup_submissions_used = 0
        self.job_applications_used = 0
        self.api_calls_used = 0
        self.save()

class SubscriptionEvent(models.Model):
    """Track subscription events for audit trail"""
    EVENT_TYPES = [
        ('created', 'Subscription Created'),
        ('updated', 'Subscription Updated'),
        ('canceled', 'Subscription Canceled'),
        ('resumed', 'Subscription Resumed'),
        ('payment_succeeded', 'Payment Succeeded'),
        ('payment_failed', 'Payment Failed'),
        ('trial_started', 'Trial Started'),
        ('trial_ended', 'Trial Ended'),
        ('plan_changed', 'Plan Changed'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_data = models.JSONField(default=dict, blank=True)
    
    # Stripe webhook data
    stripe_event_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_event_type = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.event_type} - {self.subscription.user.username}"

class PromoCode(models.Model):
    """Promotional codes for discounts"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_trial', 'Free Trial'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage or amount
    
    # Restrictions
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Applicable plans
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.code} - {self.discount_value}% off"
    
    def is_valid(self):
        """Check if promo code is valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            self.used_count < self.max_uses
        )
    
    def can_use(self, plan):
        """Check if promo code can be used with given plan"""
        if not self.is_valid():
            return False
        
        if self.applicable_plans.exists():
            return self.applicable_plans.filter(id=plan.id).exists()
        
        return True
    
    def use_code(self):
        """Mark promo code as used"""
        if self.used_count < self.max_uses:
            self.used_count += 1
            self.save()
            return True
        return False

class SubscriptionFeatureUsage(models.Model):
    """Track specific feature usage for analytics"""
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='feature_usage')
    feature_name = models.CharField(max_length=100)
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # For time-based features
    total_time_used = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['subscription', 'feature_name']
        ordering = ['-usage_count']
        
    def __str__(self):
        return f"{self.subscription.user.username} - {self.feature_name}: {self.usage_count} uses"
    
    def increment_usage(self):
        """Increment feature usage counter"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save()