from django.core.management.base import BaseCommand
from apps.subscriptions.models import SubscriptionPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        # Create Free plan
        free_plan, created = SubscriptionPlan.objects.get_or_create(
            name='Free',
            plan_type='free',
            defaults={
                'price': Decimal('0.00'),
                'currency': 'USD',
                'interval': 'month',
                'max_startup_submissions': 1,
                'max_job_applications': 5,
                'can_claim_startups': False,
                'can_edit_startups': False,
                'priority_support': False,
                'analytics_access': False,
                'advanced_search': False,
                'verified_badge': False,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Free plan'))
        else:
            self.stdout.write(self.style.WARNING('Free plan already exists'))

        # Create Pro plan
        pro_plan, created = SubscriptionPlan.objects.get_or_create(
            name='Pro',
            plan_type='pro',
            defaults={
                'price': Decimal('29.99'),
                'currency': 'USD',
                'interval': 'month',
                'max_startup_submissions': 10,
                'max_job_applications': 50,
                'can_claim_startups': True,
                'can_edit_startups': True,
                'priority_support': True,
                'analytics_access': True,
                'advanced_search': True,
                'verified_badge': True,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Pro plan'))
        else:
            self.stdout.write(self.style.WARNING('Pro plan already exists'))

        # Create Enterprise plan
        enterprise_plan, created = SubscriptionPlan.objects.get_or_create(
            name='Enterprise',
            plan_type='enterprise',
            defaults={
                'price': Decimal('99.99'),
                'currency': 'USD',
                'interval': 'month',
                'max_startup_submissions': 100,
                'max_job_applications': 500,
                'can_claim_startups': True,
                'can_edit_startups': True,
                'priority_support': True,
                'analytics_access': True,
                'advanced_search': True,
                'verified_badge': True,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Enterprise plan'))
        else:
            self.stdout.write(self.style.WARNING('Enterprise plan already exists'))

        # Create yearly plans
        pro_yearly, created = SubscriptionPlan.objects.get_or_create(
            name='Pro Yearly',
            plan_type='pro',
            defaults={
                'price': Decimal('299.99'),
                'currency': 'USD',
                'interval': 'year',
                'max_startup_submissions': 10,
                'max_job_applications': 50,
                'can_claim_startups': True,
                'can_edit_startups': True,
                'priority_support': True,
                'analytics_access': True,
                'advanced_search': True,
                'verified_badge': True,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Pro Yearly plan'))
        else:
            self.stdout.write(self.style.WARNING('Pro Yearly plan already exists'))

        enterprise_yearly, created = SubscriptionPlan.objects.get_or_create(
            name='Enterprise Yearly',
            plan_type='enterprise',
            defaults={
                'price': Decimal('999.99'),
                'currency': 'USD',
                'interval': 'year',
                'max_startup_submissions': 100,
                'max_job_applications': 500,
                'can_claim_startups': True,
                'can_edit_startups': True,
                'priority_support': True,
                'analytics_access': True,
                'advanced_search': True,
                'verified_badge': True,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Enterprise Yearly plan'))
        else:
            self.stdout.write(self.style.WARNING('Enterprise Yearly plan already exists'))

        self.stdout.write(self.style.SUCCESS('Subscription plans setup complete!'))