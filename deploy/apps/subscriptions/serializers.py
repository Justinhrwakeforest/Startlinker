from rest_framework import serializers
from .models import (
    SubscriptionPlan, Subscription, PaymentHistory, 
    SubscriptionUsage, PromoCode, SubscriptionEvent
)

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'price', 'currency', 'interval',
            'max_startup_submissions', 'max_job_applications', 
            'can_claim_startups', 'can_edit_startups', 'priority_support',
            'analytics_access', 'advanced_search', 'verified_badge',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscriptions"""
    plan = SubscriptionPlanSerializer(read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_display_name', read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user_email', 'user_name', 'plan', 'status',
            'current_period_start', 'current_period_end',
            'trial_start', 'trial_end', 'canceled_at',
            'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    user_email = serializers.CharField(source='subscription.user.email', read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'subscription_plan', 'user_email', 'amount', 'currency',
            'status', 'payment_method_type', 'last_four', 'brand',
            'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SubscriptionUsageSerializer(serializers.ModelSerializer):
    """Serializer for subscription usage"""
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)
    max_startup_submissions = serializers.IntegerField(
        source='subscription.plan.max_startup_submissions', read_only=True
    )
    max_job_applications = serializers.IntegerField(
        source='subscription.plan.max_job_applications', read_only=True
    )
    
    class Meta:
        model = SubscriptionUsage
        fields = [
            'id', 'plan_name', 'startup_submissions_used', 'job_applications_used',
            'max_startup_submissions', 'max_job_applications', 'api_calls_used',
            'period_start', 'period_end', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class PromoCodeSerializer(serializers.ModelSerializer):
    """Serializer for promo codes"""
    applicable_plan_names = serializers.StringRelatedField(
        source='applicable_plans', many=True, read_only=True
    )
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'max_uses', 'used_count', 'valid_from', 'valid_until',
            'applicable_plan_names', 'is_valid', 'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'used_count', 'created_at']

class SubscriptionEventSerializer(serializers.ModelSerializer):
    """Serializer for subscription events"""
    user_email = serializers.CharField(source='subscription.user.email', read_only=True)
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)
    
    class Meta:
        model = SubscriptionEvent
        fields = [
            'id', 'user_email', 'plan_name', 'event_type', 'event_data',
            'stripe_event_id', 'stripe_event_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for creating subscriptions"""
    plan_id = serializers.IntegerField()
    payment_method_id = serializers.CharField(required=False, allow_blank=True)
    promo_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan")
    
    def validate_promo_code(self, value):
        if value:
            try:
                promo = PromoCode.objects.get(code=value)
                if not promo.is_valid():
                    raise serializers.ValidationError("Promo code is expired or invalid")
                return value
            except PromoCode.DoesNotExist:
                raise serializers.ValidationError("Invalid promo code")
        return value

class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating checkout sessions"""
    plan_id = serializers.IntegerField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    promo_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan")

class ChangePlanSerializer(serializers.Serializer):
    """Serializer for changing subscription plans"""
    new_plan_id = serializers.IntegerField()
    
    def validate_new_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive plan")

class ValidatePromoCodeSerializer(serializers.Serializer):
    """Serializer for validating promo codes"""
    code = serializers.CharField()
    plan_id = serializers.IntegerField()
    
    def validate(self, data):
        try:
            promo = PromoCode.objects.get(code=data['code'])
            plan = SubscriptionPlan.objects.get(id=data['plan_id'])
            
            if not promo.is_valid():
                raise serializers.ValidationError("Promo code is expired or invalid")
            
            if not promo.can_use(plan):
                raise serializers.ValidationError("Promo code cannot be used with this plan")
            
            return data
        except PromoCode.DoesNotExist:
            raise serializers.ValidationError("Invalid promo code")
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan")

class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics"""
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    trial_subscriptions = serializers.IntegerField()
    canceled_subscriptions = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    plan_distribution = serializers.DictField()
    recent_events = SubscriptionEventSerializer(many=True)