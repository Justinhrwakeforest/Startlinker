"""
Management command to synchronize follower counts for all users.
Run this after adding follower_count and following_count fields to User model.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.social_models import UserFollow

User = get_user_model()

class Command(BaseCommand):
    help = 'Synchronize follower and following counts for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Synchronizing follower and following counts...')
        
        users = User.objects.all()
        total_users = users.count()
        updated_count = 0
        
        for user in users:
            # Calculate actual counts
            follower_count = UserFollow.objects.filter(following=user).count()
            following_count = UserFollow.objects.filter(follower=user).count()
            
            # Check if update is needed
            needs_update = (
                user.follower_count != follower_count or 
                user.following_count != following_count
            )
            
            if needs_update:
                if not dry_run:
                    user.follower_count = follower_count
                    user.following_count = following_count
                    user.save(update_fields=['follower_count', 'following_count'])
                
                self.stdout.write(
                    f'{"[DRY RUN] " if dry_run else ""}Updated {user.username}: '
                    f'followers {user.follower_count} -> {follower_count}, '
                    f'following {user.following_count} -> {following_count}'
                )
                updated_count += 1
        
        if updated_count == 0:
            self.stdout.write(self.style.SUCCESS('All follower counts are already in sync!'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{"[DRY RUN] Would update" if dry_run else "Updated"} '
                    f'{updated_count} out of {total_users} users'
                )
            )