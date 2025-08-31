"""
Django management command to populate Industry model with comprehensive startup industries.
This can be run in production with: python manage.py populate_industries
"""

from django.core.management.base import BaseCommand, CommandError
from apps.startups.models import Industry


class Command(BaseCommand):
    help = 'Populate the Industry model with comprehensive tech startup industries for production'
    
    # Comprehensive list of tech startup industries
    INDUSTRIES = [
        # Core Tech
        {'name': 'Artificial Intelligence', 'icon': '🤖', 'description': 'AI, ML, deep learning, and automation technologies'},
        {'name': 'Software as a Service', 'icon': '💻', 'description': 'Cloud-based software solutions and platforms'},
        {'name': 'Mobile Applications', 'icon': '📱', 'description': 'iOS, Android, and cross-platform mobile apps'},
        {'name': 'Web Development', 'icon': '🌐', 'description': 'Websites, web apps, and online platforms'},
        {'name': 'Cloud Computing', 'icon': '☁️', 'description': 'Cloud infrastructure, hosting, and services'},
        {'name': 'Cybersecurity', 'icon': '🔐', 'description': 'Security software, data protection, and privacy tools'},
        {'name': 'Data Analytics', 'icon': '📊', 'description': 'Big data, business intelligence, and analytics platforms'},
        {'name': 'Blockchain', 'icon': '⛓️', 'description': 'Cryptocurrency, DeFi, NFTs, and distributed ledger tech'},
        
        # Business & Commerce
        {'name': 'E-commerce', 'icon': '🛒', 'description': 'Online retail, marketplaces, and commerce platforms'},
        {'name': 'FinTech', 'icon': '💰', 'description': 'Financial technology, payments, and digital banking'},
        {'name': 'Marketing Technology', 'icon': '📈', 'description': 'Digital marketing, automation, and advertising tools'},
        {'name': 'Human Resources', 'icon': '👥', 'description': 'HR software, recruitment, and workforce management'},
        {'name': 'Customer Service', 'icon': '🎧', 'description': 'Support tools, chatbots, and customer experience'},
        {'name': 'Project Management', 'icon': '📋', 'description': 'Productivity tools, collaboration, and workflow software'},
        
        # Industry Specific
        {'name': 'HealthTech', 'icon': '🏥', 'description': 'Digital health, telemedicine, and medical technology'},
        {'name': 'EdTech', 'icon': '🎓', 'description': 'Educational technology and online learning platforms'},
        {'name': 'AgriTech', 'icon': '🌾', 'description': 'Agricultural technology and farming innovations'},
        {'name': 'Real Estate Technology', 'icon': '🏠', 'description': 'PropTech, real estate platforms, and property management'},
        {'name': 'Travel & Hospitality', 'icon': '✈️', 'description': 'Travel booking, hospitality management, and tourism tech'},
        {'name': 'Food & Beverage', 'icon': '🍔', 'description': 'Food delivery, restaurant tech, and culinary platforms'},
        {'name': 'Transportation', 'icon': '🚗', 'description': 'Logistics, ride-sharing, and transportation solutions'},
        {'name': 'Energy & Clean Tech', 'icon': '⚡', 'description': 'Renewable energy, sustainability, and green technology'},
        
        # Emerging Tech
        {'name': 'Internet of Things', 'icon': '🌐', 'description': 'IoT devices, smart home, and connected technology'},
        {'name': 'Augmented Reality', 'icon': '🥽', 'description': 'AR, VR, and mixed reality applications'},
        {'name': 'Gaming', 'icon': '🎮', 'description': 'Video games, mobile games, and interactive entertainment'},
        {'name': 'Social Media', 'icon': '💬', 'description': 'Social networks, community platforms, and messaging apps'},
        {'name': 'Content & Media', 'icon': '🎬', 'description': 'Digital media, streaming, and content creation tools'},
        {'name': 'Hardware', 'icon': '🔧', 'description': 'Physical products, electronics, and device manufacturing'},
        
        # General Categories
        {'name': 'Enterprise Software', 'icon': '🏢', 'description': 'B2B software solutions and enterprise tools'},
        {'name': 'Consumer Software', 'icon': '👤', 'description': 'B2C applications and consumer-facing products'},
        {'name': 'Other', 'icon': '💡', 'description': 'Innovative technologies and unique business models'},
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing industries with new descriptions/icons',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created/updated without making changes',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        dry_run = options.get('dry_run', False)
        update_existing = options.get('update', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Starting industry population...')
        self.stdout.write(f'Processing {len(self.INDUSTRIES)} industries...')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for industry_data in self.INDUSTRIES:
            try:
                industry, created = Industry.objects.get_or_create(
                    name=industry_data['name'],
                    defaults={
                        'icon': industry_data['icon'],
                        'description': industry_data['description']
                    }
                )
                
                if created:
                    created_count += 1
                    if not dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(f'Created: {industry.name}')
                        )
                    else:
                        self.stdout.write(f'[DRY RUN] Would create: {industry_data["name"]}')
                else:
                    # Check if we should update existing industry
                    should_update = False
                    changes = []
                    
                    if industry.icon != industry_data['icon']:
                        changes.append(f'icon: {industry.icon} -> {industry_data["icon"]}')
                        should_update = True
                    if industry.description != industry_data['description']:
                        changes.append(f'description updated')
                        should_update = True
                    
                    if should_update and update_existing:
                        if not dry_run:
                            industry.icon = industry_data['icon']
                            industry.description = industry_data['description']
                            industry.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Updated: {industry.name} ({", ".join(changes)})')
                            )
                        else:
                            self.stdout.write(f'[DRY RUN] Would update: {industry.name} ({", ".join(changes)})')
                    else:
                        skipped_count += 1
                        if not dry_run:
                            self.stdout.write(f'Exists: {industry.name}')
                        else:
                            self.stdout.write(f'[DRY RUN] Exists: {industry.name}')
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to process {industry_data["name"]}: {str(e)}')
                )
                raise CommandError(f'Failed to process industry: {industry_data["name"]}')
        
        # Get final count
        if not dry_run:
            total_industries = Industry.objects.count()
        else:
            total_industries = Industry.objects.count() + created_count
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN SUMMARY - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('INDUSTRY POPULATION COMPLETE'))
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(f'Would create: {created_count} new industries')
            self.stdout.write(f'Would update: {updated_count} existing industries')
            self.stdout.write(f'Would skip: {skipped_count} existing industries')
            self.stdout.write(f'Total would be: {total_industries} industries')
        else:
            self.stdout.write(self.style.SUCCESS(f'Created: {created_count} new industries'))
            self.stdout.write(self.style.WARNING(f'Updated: {updated_count} existing industries'))
            self.stdout.write(f'Skipped: {skipped_count} existing industries')
            self.stdout.write(self.style.SUCCESS(f'Total industries in database: {total_industries}'))
        
        self.stdout.write('\nIndustries are now ready for the startup submit form!')
        
        if not dry_run:
            # Verify a few industries exist
            self.stdout.write('\nSample industries in database:')
            for industry in Industry.objects.all()[:5]:
                self.stdout.write(f'  - {industry.name}')
            
            if total_industries >= 30:
                self.stdout.write(self.style.SUCCESS(
                    f'\nSUCCESS: {total_industries} industries are ready for production!'
                ))
                self.stdout.write('Users can now submit startups with proper industry selection.')
            else:
                self.stdout.write(self.style.WARNING(
                    f'\nWARNING: Only {total_industries} industries found. Consider running with --update flag.'
                ))
        
        return f'Command completed. {"Dry run" if dry_run else f"{created_count} created, {updated_count} updated"}'