"""
Simple script to check environment variables on Render
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings

print("Render Environment Check")
print("=" * 40)

# Critical environment variables
env_vars = [
    'SENDGRID_API_KEY',
    'DEFAULT_FROM_EMAIL', 
    'FRONTEND_URL',
    'DJANGO_SETTINGS_MODULE',
    'DATABASE_URL'
]

for var in env_vars:
    value = os.environ.get(var)
    if value:
        if var == 'SENDGRID_API_KEY':
            print(f"{var}: {value[:15]}...")
        elif var == 'DATABASE_URL':
            print(f"{var}: postgres://...")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET ❌")

print("\nDjango Settings Check")
print("=" * 40)
print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
print(f"FRONTEND_URL: {getattr(settings, 'FRONTEND_URL', 'Not set')}")
print(f"REQUIRE_EMAIL_VERIFICATION: {getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False)}")
print(f"DEBUG: {settings.DEBUG}")

print("\nSendGrid Test")
print("=" * 40)
try:
    import sendgrid
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    print("✅ SendGrid client created successfully")
except Exception as e:
    print(f"❌ SendGrid error: {e}")