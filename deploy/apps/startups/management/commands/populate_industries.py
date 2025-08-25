# Create this file: startup_hub/apps/startups/management/commands/populate_industries.py
from django.core.management.base import BaseCommand
from apps.startups.models import Industry

class Command(BaseCommand):
    help = 'Populate the database with default industries'

    def handle(self, *args, **options):
        industries = [
            {'name': 'Technology', 'icon': '💻', 'description': 'Software, hardware, and tech services'},
            {'name': 'Healthcare', 'icon': '🏥', 'description': 'Medical, pharmaceutical, and health services'},
            {'name': 'Finance', 'icon': '💰', 'description': 'Banking, fintech, and financial services'},
            {'name': 'E-commerce', 'icon': '🛒', 'description': 'Online retail and marketplace platforms'},
            {'name': 'Education', 'icon': '📚', 'description': 'EdTech and educational services'},
            {'name': 'Food & Beverage', 'icon': '🍕', 'description': 'Food delivery, restaurants, and beverages'},
            {'name': 'Travel & Tourism', 'icon': '✈️', 'description': 'Travel booking, hospitality, and tourism'},
            {'name': 'Real Estate', 'icon': '🏠', 'description': 'Property technology and real estate services'},
            {'name': 'Entertainment', 'icon': '🎬', 'description': 'Media, gaming, and entertainment platforms'},
            {'name': 'Transportation', 'icon': '🚗', 'description': 'Logistics, ride-sharing, and mobility'},
            {'name': 'Energy', 'icon': '⚡', 'description': 'Renewable energy and energy efficiency'},
            {'name': 'Agriculture', 'icon': '🌱', 'description': 'AgTech and agricultural innovation'},
            {'name': 'Manufacturing', 'icon': '🏭', 'description': 'Industrial technology and manufacturing'},
            {'name': 'Media', 'icon': '📺', 'description': 'Digital media and content platforms'},
            {'name': 'Gaming', 'icon': '🎮', 'description': 'Video games and interactive entertainment'},
            {'name': 'AI/Machine Learning', 'icon': '🤖', 'description': 'Artificial intelligence and ML platforms'},
            {'name': 'Blockchain/Crypto', 'icon': '⛓️', 'description': 'Cryptocurrency and blockchain technology'},
            {'name': 'SaaS', 'icon': '☁️', 'description': 'Software as a Service platforms'},
            {'name': 'Social Media', 'icon': '📱', 'description': 'Social networking and communication platforms'},
            {'name': 'Other', 'icon': '🔧', 'description': 'Other industries and emerging sectors'},
        ]

        created_count = 0
        updated_count = 0

        for industry_data in industries:
            industry, created = Industry.objects.get_or_create(
                name=industry_data['name'],
                defaults={
                    'icon': industry_data['icon'],
                    'description': industry_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created industry: {industry.name}')
                )
            else:
                # Update existing industry if needed
                if industry.icon != industry_data['icon'] or industry.description != industry_data['description']:
                    industry.icon = industry_data['icon']
                    industry.description = industry_data['description']
                    industry.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated industry: {industry.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed industries: {created_count} created, {updated_count} updated'
            )
        )