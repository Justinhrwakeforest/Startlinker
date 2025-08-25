import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timezone as datetime_timezone
from typing import Optional, Dict, Any
from .models import Subscription, SubscriptionPlan, PaymentHistory, SubscriptionEvent, PromoCode

User = get_user_model()

class StripeService:
    """Service layer for Stripe operations"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_customer(self, user: User) -> Optional[str]:
        """Create a Stripe customer for the user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_display_name(),
                metadata={
                    'user_id': user.id,
                    'username': user.username
                }
            )
            
            # Update user with Stripe customer ID
            user.stripe_customer_id = customer.id
            user.save()
            
            return customer.id
        except stripe.error.StripeError as e:
            print(f"Error creating Stripe customer: {e}")
            return None
    
    def get_or_create_customer(self, user: User) -> Optional[str]:
        """Get existing customer or create new one"""
        if user.stripe_customer_id:
            try:
                # Verify customer exists
                stripe.Customer.retrieve(user.stripe_customer_id)
                return user.stripe_customer_id
            except stripe.error.StripeError:
                # Customer doesn't exist, create new one
                pass
        
        return self.create_customer(user)
    
    def create_subscription(self, user: User, plan: SubscriptionPlan, 
                          payment_method_id: str = None, 
                          promo_code: str = None) -> Dict[str, Any]:
        """Create a new subscription"""
        try:
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                return {'success': False, 'error': 'Failed to create customer'}
            
            # Attach payment method to customer if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id,
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id,
                    },
                )
            
            # Get or create Stripe price for this plan
            stripe_price_id = self._get_or_create_price(plan)
            if not stripe_price_id:
                return {'success': False, 'error': 'Failed to create Stripe price'}
            
            # Create subscription parameters
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': stripe_price_id}],
                'metadata': {
                    'user_id': user.id,
                    'plan_id': plan.id,
                    'plan_name': plan.name
                }
            }
            
            # Add trial period if configured
            if settings.SUBSCRIPTION_SETTINGS.get('TRIAL_PERIOD_DAYS', 0) > 0:
                subscription_params['trial_period_days'] = settings.SUBSCRIPTION_SETTINGS['TRIAL_PERIOD_DAYS']
            
            # Apply promo code if provided
            if promo_code:
                try:
                    promo = PromoCode.objects.get(code=promo_code)
                    if promo.can_use(plan):
                        # Create Stripe coupon if needed
                        coupon = self._create_or_get_coupon(promo)
                        if coupon:
                            subscription_params['coupon'] = coupon.id
                            promo.use_code()
                except PromoCode.DoesNotExist:
                    pass
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(**subscription_params)
            
            # Create local subscription record
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer_id,
                status=stripe_subscription.status,
                current_period_start=timezone.datetime.fromtimestamp(
                    stripe_subscription.current_period_start, tz=datetime_timezone.utc
                ),
                current_period_end=timezone.datetime.fromtimestamp(
                    stripe_subscription.current_period_end, tz=datetime_timezone.utc
                ),
                trial_start=timezone.datetime.fromtimestamp(
                    stripe_subscription.trial_start, tz=datetime_timezone.utc
                ) if stripe_subscription.trial_start else None,
                trial_end=timezone.datetime.fromtimestamp(
                    stripe_subscription.trial_end, tz=datetime_timezone.utc
                ) if stripe_subscription.trial_end else None,
            )
            
            # Update user subscription status
            user.subscription_status = plan.plan_type
            user.save()
            
            # Create subscription event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='created',
                event_data={
                    'stripe_subscription_id': stripe_subscription.id,
                    'plan_name': plan.name,
                    'status': stripe_subscription.status
                }
            )
            
            return {
                'success': True,
                'subscription': subscription,
                'stripe_subscription': stripe_subscription,
                'requires_action': stripe_subscription.status == 'incomplete'
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            if subscription.stripe_subscription_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                
                subscription.status = 'canceled'
                subscription.canceled_at = timezone.now()
                subscription.save()
                
                # Update user subscription status
                subscription.user.subscription_status = 'free'
                subscription.user.save()
                
                # Create subscription event
                SubscriptionEvent.objects.create(
                    subscription=subscription,
                    event_type='canceled',
                    event_data={'canceled_at': timezone.now().isoformat()}
                )
                
                return {'success': True}
            
            return {'success': False, 'error': 'No Stripe subscription ID'}
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def resume_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """Resume a canceled subscription"""
        try:
            if subscription.stripe_subscription_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=False
                )
                
                subscription.status = 'active'
                subscription.canceled_at = None
                subscription.save()
                
                # Update user subscription status
                subscription.user.subscription_status = subscription.plan.plan_type
                subscription.user.save()
                
                # Create subscription event
                SubscriptionEvent.objects.create(
                    subscription=subscription,
                    event_type='resumed',
                    event_data={'resumed_at': timezone.now().isoformat()}
                )
                
                return {'success': True}
            
            return {'success': False, 'error': 'No Stripe subscription ID'}
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def change_subscription_plan(self, subscription: Subscription, 
                               new_plan: SubscriptionPlan) -> Dict[str, Any]:
        """Change subscription plan"""
        try:
            if not subscription.stripe_subscription_id:
                return {'success': False, 'error': 'No Stripe subscription ID'}
            
            # Get current subscription
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Update subscription item with new price
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0]['id'],
                    'price': new_plan.stripe_price_id,
                }],
                proration_behavior='always_invoice' if settings.SUBSCRIPTION_SETTINGS.get('PRORATE_CHANGES') else 'none'
            )
            
            # Update local subscription
            old_plan = subscription.plan
            subscription.plan = new_plan
            subscription.save()
            
            # Update user subscription status
            subscription.user.subscription_status = new_plan.plan_type
            subscription.user.save()
            
            # Create subscription event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='plan_changed',
                event_data={
                    'old_plan': old_plan.name,
                    'new_plan': new_plan.name,
                    'changed_at': timezone.now().isoformat()
                }
            )
            
            return {'success': True}
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def create_checkout_session(self, user: User, plan: SubscriptionPlan, 
                              success_url: str, cancel_url: str,
                              promo_code: str = None) -> Dict[str, Any]:
        """Create Stripe checkout session for subscription"""
        try:
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                return {'success': False, 'error': 'Failed to create customer'}
            
            # Get or create Stripe price for this plan
            stripe_price_id = self._get_or_create_price(plan)
            if not stripe_price_id:
                return {'success': False, 'error': 'Failed to create Stripe price'}
            
            session_params = {
                'customer': customer_id,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': stripe_price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'user_id': user.id,
                    'plan_id': plan.id
                }
            }
            
            # Add trial period if configured
            if settings.SUBSCRIPTION_SETTINGS.get('TRIAL_PERIOD_DAYS', 0) > 0:
                session_params['subscription_data'] = {
                    'trial_period_days': settings.SUBSCRIPTION_SETTINGS['TRIAL_PERIOD_DAYS']
                }
            
            # Apply promo code if provided
            if promo_code:
                try:
                    promo = PromoCode.objects.get(code=promo_code)
                    if promo.can_use(plan):
                        coupon = self._create_or_get_coupon(promo)
                        if coupon:
                            session_params['discounts'] = [{'coupon': coupon.id}]
                except PromoCode.DoesNotExist:
                    pass
            
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                'success': True,
                'session_id': session.id,
                'session_url': session.url
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def create_billing_portal_session(self, user: User, return_url: str) -> Dict[str, Any]:
        """Create Stripe billing portal session"""
        try:
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                return {'success': False, 'error': 'Failed to create or retrieve customer'}
            
            # Check if user has any subscriptions
            try:
                customer = stripe.Customer.retrieve(customer_id)
                subscriptions = stripe.Subscription.list(customer=customer_id, limit=1)
                
                if not subscriptions.data:
                    return {
                        'success': False, 
                        'error': 'No active subscriptions found. Please subscribe to a plan first.',
                        'error_code': 'no_subscription'
                    }
            except stripe.error.StripeError as e:
                return {'success': False, 'error': f'Error checking customer subscriptions: {str(e)}'}
            
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                'success': True,
                'session_url': session.url
            }
            
        except stripe.error.StripeError as e:
            error_message = str(e)
            
            # Handle specific Stripe billing portal configuration error
            if ('No configuration provided' in error_message and 'portal' in error_message) or 'customer portal settings' in error_message:
                return {
                    'success': False, 
                    'error': 'Billing portal is not configured. Please contact support for billing assistance.',
                    'error_code': 'portal_not_configured',
                    'fallback_available': True
                }
            
            return {'success': False, 'error': error_message}
    
    def get_payment_methods(self, user: User) -> Dict[str, Any]:
        """Get user's payment methods"""
        try:
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                return {'success': False, 'error': 'Failed to create customer'}
            
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card',
            )
            
            return {
                'success': True,
                'payment_methods': payment_methods.data
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def get_upcoming_invoice(self, user: User) -> Dict[str, Any]:
        """Get upcoming invoice for user"""
        try:
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                return {'success': False, 'error': 'Failed to create customer'}
            
            invoice = stripe.Invoice.upcoming(customer=customer_id)
            
            return {
                'success': True,
                'invoice': invoice
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def _create_or_get_coupon(self, promo_code: PromoCode) -> Optional[stripe.Coupon]:
        """Create or retrieve Stripe coupon for promo code"""
        try:
            coupon_id = f"promo_{promo_code.code.lower()}"
            
            # Try to retrieve existing coupon
            try:
                return stripe.Coupon.retrieve(coupon_id)
            except stripe.error.InvalidRequestError:
                # Coupon doesn't exist, create it
                pass
            
            # Create new coupon
            coupon_params = {
                'id': coupon_id,
                'name': f"Promo Code: {promo_code.code}",
                'duration': 'once',
                'metadata': {
                    'promo_code_id': promo_code.id,
                    'promo_code': promo_code.code
                }
            }
            
            if promo_code.discount_type == 'percentage':
                coupon_params['percent_off'] = float(promo_code.discount_value)
            elif promo_code.discount_type == 'fixed_amount':
                coupon_params['amount_off'] = int(promo_code.discount_value * 100)  # Convert to cents
                coupon_params['currency'] = 'usd'
            
            return stripe.Coupon.create(**coupon_params)
            
        except stripe.error.StripeError as e:
            print(f"Error creating coupon: {e}")
            return None
    
    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event_type = event['type']
            data = event['data']['object']
            
            if event_type == 'customer.subscription.created':
                return self._handle_subscription_created(data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(data)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(data)
            elif event_type == 'customer.subscription.trial_will_end':
                return self._handle_trial_will_end(data)
            
            return {'success': True, 'message': f'Unhandled event type: {event_type}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created webhook"""
        try:
            # Try to get existing subscription first
            subscription = None
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=data['id'])
            except Subscription.DoesNotExist:
                # If subscription doesn't exist, create it
                customer_id = data['customer']
                
                # Find the user by customer ID
                user = User.objects.filter(stripe_customer_id=customer_id).first()
                if not user:
                    return {'success': False, 'error': 'User not found for customer'}
                
                # Find the plan by price ID
                price_id = data['items']['data'][0]['price']['id']
                plan = SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()
                
                if not plan:
                    # Try to find plan by metadata
                    metadata = data.get('metadata', {})
                    plan_id = metadata.get('plan_id')
                    if plan_id:
                        plan = SubscriptionPlan.objects.filter(id=plan_id).first()
                        if plan:
                            plan.stripe_price_id = price_id
                            plan.save()
                
                if not plan:
                    return {'success': False, 'error': 'Plan not found for subscription'}
                
                # Create the subscription
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    stripe_subscription_id=data['id'],
                    stripe_customer_id=customer_id,
                    status=data['status'],
                    current_period_start=timezone.datetime.fromtimestamp(
                        data['current_period_start'], tz=datetime_timezone.utc
                    ),
                    current_period_end=timezone.datetime.fromtimestamp(
                        data['current_period_end'], tz=datetime_timezone.utc
                    ),
                )
                
                # Update user subscription status
                user.subscription_status = plan.plan_type
                user.save()
            
            # Update subscription status if it already exists
            if subscription:
                subscription.status = data['status']
                subscription.current_period_start = timezone.datetime.fromtimestamp(
                    data['current_period_start'], tz=datetime_timezone.utc
                )
                subscription.current_period_end = timezone.datetime.fromtimestamp(
                    data['current_period_end'], tz=datetime_timezone.utc
                )
                subscription.save()
            
            # Create event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='created',
                stripe_event_id=data.get('id'),
                event_data=data
            )
            
            return {'success': True}
            
        except Exception as e:
            print(f"Error handling subscription created webhook: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated webhook"""
        try:
            # Try to get existing subscription
            subscription = None
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=data['id'])
            except Subscription.DoesNotExist:
                # If subscription doesn't exist, try to create it (similar to created handler)
                return self._handle_subscription_created(data)
            
            # Update subscription status
            subscription.status = data['status']
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                data['current_period_start'], tz=datetime_timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                data['current_period_end'], tz=datetime_timezone.utc
            )
            
            if data.get('canceled_at'):
                subscription.canceled_at = timezone.datetime.fromtimestamp(
                    data['canceled_at'], tz=datetime_timezone.utc
                )
            
            subscription.save()
            
            # Update user subscription status
            subscription.user.subscription_status = subscription.plan.plan_type if subscription.is_active() else 'free'
            subscription.user.save()
            
            # Create event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='updated',
                stripe_event_id=data.get('id'),
                event_data=data
            )
            
            return {'success': True}
            
        except Exception as e:
            print(f"Error handling subscription updated webhook: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deleted webhook"""
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=data['id'])
            
            # Update subscription status
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
            subscription.save()
            
            # Update user subscription status
            subscription.user.subscription_status = 'free'
            subscription.user.save()
            
            # Create event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='canceled',
                stripe_event_id=data.get('id'),
                event_data=data
            )
            
            return {'success': True}
            
        except Subscription.DoesNotExist:
            return {'success': False, 'error': 'Subscription not found'}
    
    def _handle_payment_succeeded(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment succeeded webhook"""
        try:
            # If this is a subscription payment, make sure the subscription exists
            if data.get('subscription'):
                try:
                    subscription = Subscription.objects.get(stripe_subscription_id=data['subscription'])
                except Subscription.DoesNotExist:
                    # Try to create the subscription if it doesn't exist
                    stripe_subscription = stripe.Subscription.retrieve(data['subscription'])
                    result = self._handle_subscription_created(stripe_subscription)
                    if not result['success']:
                        return result
                    subscription = Subscription.objects.get(stripe_subscription_id=data['subscription'])
                
                # Create payment record
                PaymentHistory.objects.create(
                    subscription=subscription,
                    stripe_payment_intent_id=data.get('payment_intent'),
                    stripe_invoice_id=data.get('id'),
                    amount=data['amount_paid'] / 100,  # Convert from cents
                    currency=data['currency'],
                    status='succeeded',
                    paid_at=timezone.datetime.fromtimestamp(data['created'], tz=datetime_timezone.utc)
                )
                
                # Ensure subscription is active and user status is updated
                if subscription.status != 'active':
                    subscription.status = 'active'
                    subscription.save()
                    
                subscription.user.subscription_status = subscription.plan.plan_type
                subscription.user.save()
                
                # Create event
                SubscriptionEvent.objects.create(
                    subscription=subscription,
                    event_type='payment_succeeded',
                    stripe_event_id=data.get('id'),
                    event_data=data
                )
            
            return {'success': True}
            
        except Exception as e:
            print(f"Error handling payment succeeded webhook: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failed webhook"""
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=data['subscription'])
            
            # Create payment record
            PaymentHistory.objects.create(
                subscription=subscription,
                stripe_payment_intent_id=data.get('payment_intent'),
                stripe_invoice_id=data.get('id'),
                amount=data['amount_due'] / 100,  # Convert from cents
                currency=data['currency'],
                status='failed'
            )
            
            # Create event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='payment_failed',
                stripe_event_id=data.get('id'),
                event_data=data
            )
            
            return {'success': True}
            
        except Subscription.DoesNotExist:
            return {'success': False, 'error': 'Subscription not found'}
    
    def _handle_trial_will_end(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trial will end webhook"""
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=data['id'])
            
            # Create event
            SubscriptionEvent.objects.create(
                subscription=subscription,
                event_type='trial_ended',
                stripe_event_id=data.get('id'),
                event_data=data
            )
            
            # Here you could send email notification about trial ending
            
            return {'success': True}
            
        except Subscription.DoesNotExist:
            return {'success': False, 'error': 'Subscription not found'}
    
    def _get_or_create_price(self, plan: 'SubscriptionPlan') -> str:
        """Get or create Stripe price for a subscription plan"""
        try:
            # If plan already has stripe_price_id, return it
            if plan.stripe_price_id:
                return plan.stripe_price_id
            
            # Skip free plans
            if plan.price == 0:
                return None
            
            # Create or get product first
            product_name = f"StartupHub {plan.name}"
            
            try:
                # Try to find existing product
                products = stripe.Product.list(limit=100)
                product = next((p for p in products if p.name == product_name), None)
                
                if not product:
                    # Create new product
                    product = stripe.Product.create(
                        name=product_name,
                        description=f"StartupHub {plan.name} subscription plan"
                    )
            except stripe.error.StripeError:
                # Create new product if search fails
                product = stripe.Product.create(
                    name=product_name,
                    description=f"StartupHub {plan.name} subscription plan"
                )
            
            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(plan.price * 100),  # Convert to cents
                currency='usd',
                recurring={'interval': plan.interval}
            )
            
            # Save the price ID to the plan
            plan.stripe_price_id = price.id
            plan.save()
            
            return price.id
            
        except stripe.error.StripeError as e:
            print(f"Error creating Stripe price: {e}")
            return None
    
    def get_customer_billing_info(self, user: User) -> Dict[str, Any]:
        """Get customer billing information as fallback when portal is not available"""
        try:
            customer_id = self.get_or_create_customer(user)
            if not customer_id:
                return {'success': False, 'error': 'Failed to get customer'}
            
            # Get customer info
            customer = stripe.Customer.retrieve(customer_id)
            
            # Get subscriptions
            subscriptions = stripe.Subscription.list(customer=customer_id)
            
            # Get payment methods
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            # Get recent invoices
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=5
            )
            
            return {
                'success': True,
                'customer': {
                    'email': customer.email,
                    'name': customer.name,
                    'created': customer.created
                },
                'subscriptions': [{
                    'id': sub.id,
                    'status': sub.status,
                    'current_period_start': getattr(sub, 'current_period_start', None),
                    'current_period_end': getattr(sub, 'current_period_end', None),
                    'cancel_at_period_end': getattr(sub, 'cancel_at_period_end', False)
                } for sub in subscriptions.data],
                'payment_methods': [{
                    'id': pm.id,
                    'card': {
                        'brand': pm.card.brand,
                        'last4': pm.card.last4,
                        'exp_month': pm.card.exp_month,
                        'exp_year': pm.card.exp_year
                    }
                } for pm in payment_methods.data if hasattr(pm, 'card') and pm.card],
                'invoices': [{
                    'id': inv.id,
                    'amount_paid': inv.amount_paid / 100,
                    'currency': inv.currency,
                    'status': inv.status,
                    'created': inv.created,
                    'hosted_invoice_url': getattr(inv, 'hosted_invoice_url', None)
                } for inv in invoices.data]
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}