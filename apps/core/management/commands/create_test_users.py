from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for the platform'

    def handle(self, *args, **options):
        test_users = [
            {
                'username': 'VasanthKumar',
                'email': 'vasanth@example.com',
                'first_name': 'Vasanth',
                'last_name': 'Kumar N',
                'password': 'testpass123'
            },
            {
                'username': 'SarahTech',
                'email': 'sarah@example.com', 
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'password': 'testpass123'
            },
            {
                'username': 'DevMike',
                'email': 'mike@example.com',
                'first_name': 'Michael',
                'last_name': 'Chen', 
                'password': 'testpass123'
            },
            {
                'username': 'TechFounder',
                'email': 'founder@example.com',
                'first_name': 'Alex',
                'last_name': 'Smith',
                'password': 'testpass123'
            }
        ]
        
        created_count = 0
        
        self.stdout.write("Creating test users...")
        
        for user_data in test_users:
            # Check if user already exists
            if User.objects.filter(username=user_data['username']).exists():
                self.stdout.write(f"User {user_data['username']} already exists, skipping...")
                continue
                
            if User.objects.filter(email=user_data['email']).exists():
                self.stdout.write(f"Email {user_data['email']} already exists, skipping...")
                continue
            
            # Create the user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password=user_data['password']
            )
            user.is_active = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"Created user: {user.username} (ID: {user.id})")
            )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"\nCreated {created_count} new test users")
        )
        self.stdout.write(f"Total users in database: {User.objects.count()}")