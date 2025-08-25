from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timezone as datetime_timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.conf import settings
import stripe
import json
from datetime import datetime, timedelta

from .models import (
    SubscriptionPlan, Subscription, PaymentHistory, 
    SubscriptionUsage, PromoCode, SubscriptionEvent
)
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, PaymentHistorySerializer,
    SubscriptionUsageSerializer, PromoCodeSerializer, SubscriptionEventSerializer,
    CreateSubscriptionSerializer, CreateCheckoutSessionSerializer, 
    ChangePlanSerializer, ValidatePromoCodeSerializer, SubscriptionStatsSerializer
)
from .services import StripeService
from .permissions import (
    get_user_subscription_limits, get_user_subscription_usage,
    user_can_claim_startups, user_can_edit_startups, user_has_analytics_access,
    user_has_advanced_search
)

User = get_user_model()

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for subscription plans"""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        plan_type = self.request.query_params.get('plan_type')
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        return queryset.order_by('price')

class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all().select_related('user', 'plan')
        return Subscription.objects.filter(user=self.request.user).select_related('plan')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's subscription"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No active subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current user's subscription status and limits"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        try:
            subscription = Subscription.objects.get(user=request.user)
            subscription_data = {
                'subscription_status': request.user.subscription_status,
                'plan_name': subscription.plan.name,
                'is_active': subscription.is_active(),
                'is_trial': subscription.is_trial(),
                'days_until_expiry': subscription.days_until_expiry(),
                'current_period_end': subscription.current_period_end,
            }
        except Subscription.DoesNotExist:
            subscription_data = {
                'subscription_status': 'free',
                'plan_name': 'Free',
                'is_active': True,
                'is_trial': False,
                'days_until_expiry': None,
                'current_period_end': None,
            }
        
        # Get subscription limits and usage
        limits = get_user_subscription_limits(request.user)
        usage = get_user_subscription_usage(request.user)
        
        # Get feature permissions
        permissions_data = {
            'can_claim_startups': user_can_claim_startups(request.user),
            'can_edit_startups': user_can_edit_startups(request.user),
            'has_analytics_access': user_has_analytics_access(request.user),
            'has_advanced_search': user_has_advanced_search(request.user),
        }
        
        return Response({
            'subscription': subscription_data,
            'limits': limits,
            'usage': usage,
            'permissions': permissions_data
        })
    
    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        """Create a new subscription"""
        serializer = CreateSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user already has a subscription
            if Subscription.objects.filter(user=request.user).exists():
                return Response(
                    {'error': 'User already has a subscription'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            stripe_service = StripeService()
            
            result = stripe_service.create_subscription(
                user=request.user,
                plan=plan,
                payment_method_id=serializer.validated_data.get('payment_method_id'),
                promo_code=serializer.validated_data.get('promo_code')
            )
            
            if result['success']:
                subscription_serializer = self.get_serializer(result['subscription'])
                return Response({
                    'subscription': subscription_serializer.data,
                    'requires_action': result.get('requires_action', False)
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_checkout_session(self, request):
        """Create Stripe checkout session"""
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if serializer.is_valid():
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            stripe_service = StripeService()
            
            result = stripe_service.create_checkout_session(
                user=request.user,
                plan=plan,
                success_url=serializer.validated_data['success_url'],
                cancel_url=serializer.validated_data['cancel_url'],
                promo_code=serializer.validated_data.get('promo_code')
            )
            
            if result['success']:
                return Response({
                    'session_id': result['session_id'],
                    'session_url': result['session_url']
                })
            else:
                return Response(
                    {'error': result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_billing_portal_session(self, request):
        """Create Stripe billing portal session"""
        return_url = request.data.get('return_url')
        if not return_url:
            return Response(
                {'error': 'return_url is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stripe_service = StripeService()
        result = stripe_service.create_billing_portal_session(
            user=request.user,
            return_url=return_url
        )
        
        if result['success']:
            return Response({'session_url': result['session_url']})
        else:
            # If billing portal is not configured, provide fallback information
            if result.get('error_code') == 'portal_not_configured':
                billing_info = stripe_service.get_customer_billing_info(request.user)
                if billing_info['success']:
                    return Response({
                        'error': result['error'],
                        'error_code': result['error_code'],
                        'billing_info': billing_info,
                        'fallback_available': True
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(
                {
                    'error': result['error'],
                    'error_code': result.get('error_code')
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def cancel_subscription(self, request):
        """Cancel current subscription"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            stripe_service = StripeService()
            
            result = stripe_service.cancel_subscription(subscription)
            
            if result['success']:
                serializer = self.get_serializer(subscription)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No active subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def resume_subscription(self, request):
        """Resume canceled subscription"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            stripe_service = StripeService()
            
            result = stripe_service.resume_subscription(subscription)
            
            if result['success']:
                serializer = self.get_serializer(subscription)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No active subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def change_plan(self, request):
        """Change subscription plan"""
        serializer = ChangePlanSerializer(data=request.data)
        if serializer.is_valid():
            try:
                subscription = Subscription.objects.get(user=request.user)
                new_plan = SubscriptionPlan.objects.get(
                    id=serializer.validated_data['new_plan_id']
                )
                
                stripe_service = StripeService()
                result = stripe_service.change_subscription_plan(subscription, new_plan)
                
                if result['success']:
                    subscription.refresh_from_db()
                    subscription_serializer = self.get_serializer(subscription)
                    return Response(subscription_serializer.data)
                else:
                    return Response(
                        {'error': result['error']}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Subscription.DoesNotExist:
                return Response(
                    {'error': 'No active subscription found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def usage(self, request):
        """Get current subscription usage"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            
            # Get current usage period
            now = timezone.now()
            current_period_start = subscription.current_period_start or now.replace(day=1)
            
            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=subscription,
                period_start=current_period_start,
                defaults={
                    'period_end': subscription.current_period_end or (now + timedelta(days=30))
                }
            )
            
            serializer = SubscriptionUsageSerializer(usage)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No active subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def payment_methods(self, request):
        """Get user's payment methods"""
        stripe_service = StripeService()
        result = stripe_service.get_payment_methods(request.user)
        
        if result['success']:
            return Response({'payment_methods': result['payment_methods']})
        else:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def upcoming_invoice(self, request):
        """Get upcoming invoice"""
        stripe_service = StripeService()
        result = stripe_service.get_upcoming_invoice(request.user)
        
        if result['success']:
            return Response({'invoice': result['invoice']})
        else:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def verify_session(self, request):
        """Verify Stripe checkout session and update subscription"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            stripe_service = StripeService()
            
            # Retrieve the session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Handle different session states
            if session.mode != 'subscription':
                return Response({'error': 'Not a subscription session'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if payment is still processing
            if session.payment_status == 'unpaid':
                return Response({
                    'error': 'Payment is still processing. Please wait a moment and try again.',
                    'payment_status': session.payment_status,
                    'session_status': session.status
                }, status=status.HTTP_202_ACCEPTED)
            
            # Check if payment failed
            if session.payment_status in ['failed', 'canceled']:
                return Response({
                    'error': f'Payment {session.payment_status}. Please try again.',
                    'payment_status': session.payment_status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Only proceed if payment is completed
            if session.payment_status != 'paid':
                return Response({
                    'error': f'Unexpected payment status: {session.payment_status}',
                    'payment_status': session.payment_status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if subscription exists in session
            if not session.subscription:
                return Response({'error': 'No subscription found in session'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the subscription from Stripe
            stripe_subscription = stripe.Subscription.retrieve(session.subscription)
            
            # Find the plan based on the price ID
            price_id = stripe_subscription.items.data[0].price.id
            
            # First try to find plan by stripe_price_id
            plan = None
            try:
                plan = SubscriptionPlan.objects.get(stripe_price_id=price_id)
            except SubscriptionPlan.DoesNotExist:
                # If not found, try to match by metadata or create/update the plan
                metadata = session.metadata or {}
                plan_id = metadata.get('plan_id')
                if plan_id:
                    try:
                        plan = SubscriptionPlan.objects.get(id=plan_id)
                        # Update the plan with the Stripe price ID
                        plan.stripe_price_id = price_id
                        plan.save()
                    except SubscriptionPlan.DoesNotExist:
                        pass
                
                if not plan:
                    # As a fallback, try to find plan by price amount
                    stripe_price = stripe.Price.retrieve(price_id)
                    amount = stripe_price.unit_amount / 100  # Convert from cents
                    
                    plan = SubscriptionPlan.objects.filter(
                        price=amount, 
                        interval=stripe_price.recurring.interval
                    ).first()
                    
                    if plan:
                        plan.stripe_price_id = price_id
                        plan.save()
            
            if not plan:
                return Response({'error': 'Plan not found for this subscription'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update the subscription in our database
            subscription, created = Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'stripe_subscription_id': stripe_subscription.id,
                    'stripe_customer_id': stripe_subscription.customer,
                    'status': stripe_subscription.status,
                    'current_period_start': timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_start, tz=datetime_timezone.utc
                    ),
                    'current_period_end': timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end, tz=datetime_timezone.utc
                    ),
                }
            )
            
            # Update user subscription status
            request.user.subscription_status = plan.plan_type
            request.user.save()
            
            # Create subscription event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='subscription_created' if created else 'subscription_updated',
                stripe_event_id=session_id,
                event_data={
                    'session_id': session_id, 
                    'stripe_subscription_id': stripe_subscription.id,
                    'plan_name': plan.name,
                    'amount': str(plan.price)
                }
            )
            
            # Return subscription details
            serializer = SubscriptionSerializer(subscription)
            return Response({
                'subscription': serializer.data,
                'plan_name': plan.name,
                'next_billing_date': subscription.current_period_end,
                'message': 'Subscription verified successfully'
            })
            
        except stripe.error.StripeError as e:
            return Response({'error': f'Stripe error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            print(f"Verification error: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': f'Verification failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def stats(self, request):
        """Get subscription statistics (admin only)"""
        total_subscriptions = Subscription.objects.count()
        active_subscriptions = Subscription.objects.filter(status='active').count()
        trial_subscriptions = Subscription.objects.filter(status='trialing').count()
        canceled_subscriptions = Subscription.objects.filter(status='canceled').count()
        
        # Calculate monthly revenue
        this_month = timezone.now().replace(day=1)
        monthly_revenue = PaymentHistory.objects.filter(
            status='succeeded',
            paid_at__gte=this_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Plan distribution
        plan_distribution = Subscription.objects.values('plan__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent events
        recent_events = SubscriptionEvent.objects.select_related(
            'subscription__user', 'subscription__plan'
        ).order_by('-created_at')[:10]
        
        data = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'trial_subscriptions': trial_subscriptions,
            'canceled_subscriptions': canceled_subscriptions,
            'monthly_revenue': monthly_revenue,
            'plan_distribution': {item['plan__name']: item['count'] for item in plan_distribution},
            'recent_events': SubscriptionEventSerializer(recent_events, many=True).data
        }
        
        return Response(data)

class PaymentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for payment history"""
    serializer_class = PaymentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PaymentHistory.objects.all().select_related('subscription__user', 'subscription__plan')
        return PaymentHistory.objects.filter(
            subscription__user=self.request.user
        ).select_related('subscription__plan')

class PromoCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for promo codes"""
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def validate_code(self, request):
        """Validate a promo code"""
        serializer = ValidatePromoCodeSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            try:
                promo = PromoCode.objects.get(code=code)
                plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
                
                if promo.can_use(plan):
                    return Response({
                        'valid': True,
                        'discount_type': promo.discount_type,
                        'discount_value': promo.discount_value,
                        'code': promo.code
                    })
                else:
                    return Response({
                        'valid': False,
                        'error': 'Promo code cannot be used with this plan'
                    })
            except PromoCode.DoesNotExist:
                return Response({
                    'valid': False,
                    'error': 'Invalid promo code'
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    stripe_service = StripeService()
    result = stripe_service.handle_webhook_event(event)
    
    if result['success']:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)

class SubscriptionUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for subscription usage"""
    serializer_class = SubscriptionUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return SubscriptionUsage.objects.all().select_related('subscription__user', 'subscription__plan')
        return SubscriptionUsage.objects.filter(
            subscription__user=self.request.user
        ).select_related('subscription__plan')

class SubscriptionEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for subscription events"""
    serializer_class = SubscriptionEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return SubscriptionEvent.objects.all().select_related('subscription__user', 'subscription__plan')
        return SubscriptionEvent.objects.filter(
            subscription__user=self.request.user
        ).select_related('subscription__plan')