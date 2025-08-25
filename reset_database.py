#!/usr/bin/env python3
"""
Database Reset Script for StartupHub
This script resets the database and creates fresh migrations to fix migration issues.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
import subprocess

def reset_database():
    """Reset the database and create fresh migrations"""
    print("🔄 Resetting database and migrations...")
    
    # Remove database file
    db_file = project_dir / 'db.sqlite3'
    if db_file.exists():
        db_file.unlink()
        print("✅ Removed existing database")
    
    # Remove all migration files except __init__.py
    migration_dirs = [
        project_dir / 'apps' / 'users' / 'migrations',
        project_dir / 'apps' / 'jobs' / 'migrations',
        project_dir / 'apps' / 'messaging' / 'migrations',
        project_dir / 'apps' / 'posts' / 'migrations',
        project_dir / 'apps' / 'startups' / 'migrations',
        project_dir / 'apps' / 'notifications' / 'migrations',
        project_dir / 'apps' / 'connect' / 'migrations',
        project_dir / 'apps' / 'reports' / 'migrations',
    ]
    
    for migration_dir in migration_dirs:
        if migration_dir.exists():
            for migration_file in migration_dir.glob('*.py'):
                if migration_file.name != '__init__.py':
                    migration_file.unlink()
            print(f"✅ Cleaned migrations in {migration_dir.name}")
    
    # Create fresh migrations
    print("📝 Creating fresh migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        print("✅ Created fresh migrations")
    except Exception as e:
        print(f"❌ Error creating migrations: {e}")
        return False
    
    # Apply migrations
    print("🚀 Applying migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Applied migrations successfully")
    except Exception as e:
        print(f"❌ Error applying migrations: {e}")
        return False
    
    # Create superuser
    print("👤 Creating superuser...")
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@startlinker.com', 'admin123')
            print("✅ Created superuser: admin/admin123")
        else:
            print("ℹ️ Superuser already exists")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
    
    print("🎉 Database reset completed successfully!")
    return True

if __name__ == '__main__':
    reset_database()
