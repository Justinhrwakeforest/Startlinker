# Management command to collect static files for production

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Collect static files for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for input',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting static files collection...'))
        
        # Ensure static directory exists
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            os.makedirs(settings.STATIC_ROOT, exist_ok=True)
            self.stdout.write(f'Static root directory: {settings.STATIC_ROOT}')
        
        # Collect static files
        try:
            call_command(
                'collectstatic',
                '--no-input' if options['no_input'] else None,
                verbosity=2,
                interactive=False if options['no_input'] else True,
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully collected static files')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error collecting static files: {str(e)}')
            )
            return
        
        # Verify static files
        self.verify_static_files()
        
        self.stdout.write(
            self.style.SUCCESS('Static files collection completed!')
        )

    def verify_static_files(self):
        """Verify that important static files exist"""
        self.stdout.write('Verifying static files...')
        
        # Check for admin static files
        admin_css = os.path.join(settings.STATIC_ROOT, 'admin', 'css', 'base.css')
        if os.path.exists(admin_css):
            self.stdout.write('✓ Admin CSS files found')
        else:
            self.stdout.write(self.style.WARNING('⚠ Admin CSS files not found'))
        
        # Check for DRF static files
        drf_css = os.path.join(settings.STATIC_ROOT, 'rest_framework', 'css', 'bootstrap.min.css')
        if os.path.exists(drf_css):
            self.stdout.write('✓ DRF static files found')
        else:
            self.stdout.write(self.style.WARNING('⚠ DRF static files not found'))
        
        self.stdout.write('Static files verification completed')