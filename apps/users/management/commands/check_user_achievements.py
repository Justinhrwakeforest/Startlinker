# apps/users/management/commands/check_user_achievements.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.achievement_tracker import AchievementTracker

User = get_user_model()

class Command(BaseCommand):
    help = 'Check and unlock achievements for all users or a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to check achievements for (if not provided, checks all users)',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        
        if username:
            try:
                user = User.objects.get(username=username)
                users = [user]
                self.stdout.write(f'Checking achievements for user: {username}')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" not found')
                )
                return
        else:
            users = User.objects.filter(is_active=True)
            self.stdout.write(f'Checking achievements for {users.count()} users')

        total_unlocked = 0
        
        for user in users:
            try:
                unlocked_achievements = AchievementTracker.check_and_unlock_achievements(user)
                
                if unlocked_achievements:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  {user.username}: Unlocked {len(unlocked_achievements)} achievements'
                        )
                    )
                    for user_achievement in unlocked_achievements:
                        self.stdout.write(
                            f'    - {user_achievement.achievement.name} (+{user_achievement.achievement.points} points)'
                        )
                    total_unlocked += len(unlocked_achievements)
                else:
                    self.stdout.write(f'  {user.username}: No new achievements unlocked')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error checking {user.username}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Total achievements unlocked: {total_unlocked}'
            )
        )