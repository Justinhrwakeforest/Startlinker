from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    SubscriptionPlan, Subscription, PaymentHistory, SubscriptionUsage,
    PromoCode, SubscriptionEvent, SubscriptionFeatureUsage
)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'plan_type', 'price', 'currency', 'interval',
        'max_startup_submissions', 'max_job_applications',
        'can_claim_startups', 'can_edit_startups', 'is_active'
    ]
    list_filter = ['plan_type', 'interval', 'is_active']
    search_fields = ['name', 'plan_type']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'plan_name', 'status', 'current_period_start',
        'current_period_end', 'is_active_display', 'created_at'
    ]
    list_filter = ['status', 'plan__plan_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'plan__name']
    readonly_fields = [
        'stripe_subscription_id', 'stripe_customer_id', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def plan_name(self, obj):
        return obj.plan.name
    plan_name.short_description = 'Plan'
    
    def is_active_display(self, obj):
        if obj.is_active():
            return format_html('<span style="color: green;">Active</span>')
        else:
            return format_html('<span style="color: red;">Inactive</span>')
    is_active_display.short_description = 'Status'

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'amount', 'currency', 'status',
        'payment_method_type', 'paid_at', 'created_at'
    ]
    list_filter = ['status', 'currency', 'payment_method_type', 'created_at']
    search_fields = ['subscription__user__email', 'stripe_payment_intent_id']
    readonly_fields = [
        'stripe_payment_intent_id', 'stripe_invoice_id', 'created_at', 'updated_at'
    ]
    
    def subscription_user(self, obj):
        return obj.subscription.user.email
    subscription_user.short_description = 'User'

@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'period_start', 'startup_submissions_used',
        'job_applications_used', 'api_calls_used'
    ]
    list_filter = ['period_start', 'created_at']
    search_fields = ['subscription__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def subscription_user(self, obj):
        return obj.subscription.user.email
    subscription_user.short_description = 'User'

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'used_count',
        'max_uses', 'valid_from', 'valid_until', 'is_active'
    ]
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_plans']

@admin.register(SubscriptionEvent)
class SubscriptionEventAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'event_type', 'stripe_event_type', 'created_at'
    ]
    list_filter = ['event_type', 'stripe_event_type', 'created_at']
    search_fields = ['subscription__user__email', 'stripe_event_id']
    readonly_fields = ['created_at']
    
    def subscription_user(self, obj):
        return obj.subscription.user.email
    subscription_user.short_description = 'User'

@admin.register(SubscriptionFeatureUsage)
class SubscriptionFeatureUsageAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'feature_name', 'usage_count', 'last_used'
    ]
    list_filter = ['feature_name', 'last_used', 'created_at']
    search_fields = ['subscription__user__email', 'feature_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def subscription_user(self, obj):
        return obj.subscription.user.email
    subscription_user.short_description = 'User'