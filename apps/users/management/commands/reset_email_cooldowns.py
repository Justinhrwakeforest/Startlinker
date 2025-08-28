# apps/users/management/commands/reset_email_cooldowns.py

from django.core.management.base import BaseCommand
from apps.users.models import User

class Command(BaseCommand):
    help = 'Reset email verification cooldowns for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Reset cooldown for specific email address',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                user.email_verification_sent_at = None
                user.save(update_fields=['email_verification_sent_at'])
                self.stdout.write(
                    self.style.SUCCESS(f'Reset email cooldown for {email}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {email} not found')
                )
        else:
            # Reset for all users
            updated = User.objects.filter(
                email_verification_sent_at__isnull=False
            ).update(email_verification_sent_at=None)
            
            self.stdout.write(
                self.style.SUCCESS(f'Reset email cooldowns for {updated} users')
            )