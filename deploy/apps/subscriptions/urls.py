from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet, SubscriptionViewSet, PaymentHistoryViewSet,
    PromoCodeViewSet, SubscriptionUsageViewSet, SubscriptionEventViewSet,
    stripe_webhook
)

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'payments', PaymentHistoryViewSet, basename='paymenthistory')
router.register(r'promo-codes', PromoCodeViewSet, basename='promocode')
router.register(r'usage', SubscriptionUsageViewSet, basename='subscriptionusage')
router.register(r'events', SubscriptionEventViewSet, basename='subscriptionevent')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),
]