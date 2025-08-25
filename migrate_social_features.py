#!/usr/bin/env python
"""
Migration script for social features
Run this script to create and apply migrations for the new social models
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
    django.setup()
    
    print("Creating migrations for social features...")
    
    # Create migrations
    execute_from_command_line(['manage.py', 'makemigrations', 'users'])
    
    print("Applying migrations...")
    
    # Apply migrations
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("✅ Social features migrations completed successfully!")
    print("\n📋 Social features added:")
    print("  • User Following System")
    print("  • Instagram-style Stories")
    print("  • Startup Collections (Pinterest-style)")
    print("  • Achievement Badges")
    print("  • User Mentions with autocomplete")
    print("  • Post Scheduling")
    print("  • Personalized Feeds")
    print("  • Social Statistics")
    
    print("\n🌐 Available API endpoints:")
    print("  • /api/social/follows/ - Follow/unfollow users")
    print("  • /api/social/stories/ - Create and view stories")
    print("  • /api/social/collections/ - Manage startup collections")
    print("  • /api/social/achievements/ - View achievements")
    print("  • /api/social/scheduled-posts/ - Schedule posts")
    print("  • /api/social/feed/personalized/ - Get personalized feed")
    
    print("\n🎨 Frontend routes:")
    print("  • /posts - Enhanced posts feed with stories")
    print("  • /social - Complete social dashboard")
    
    print("\n🚀 Ready to use! Navigate to /social to explore the new features.")