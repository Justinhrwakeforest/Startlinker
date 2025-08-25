#!/usr/bin/env python
"""
Script to manually create the reports migration
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.core.management import call_command

try:
    print("Creating migrations for reports app...")
    call_command('makemigrations', 'reports', verbosity=2)
    print("Migration created successfully!")
except Exception as e:
    print(f"Error creating migration: {e}")
    import traceback
    traceback.print_exc()