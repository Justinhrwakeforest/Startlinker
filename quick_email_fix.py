#!/usr/bin/env python3
"""
Quick fix for email verification issues on Render
Run this in Render Shell as a one-liner
"""

# Quick one-liner commands for Render Shell:

print("""
🚀 QUICK EMAIL FIX COMMANDS FOR RENDER SHELL:

1. RESET EMAIL COOLDOWNS:
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
count = User.objects.filter(email_verified=False).update(email_verification_sent_at=None)
print(f'Reset cooldown for {count} users')
"

2. TEST SENDGRID CONNECTION:
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()
from django.core.mail import send_mail
from django.conf import settings
result = send_mail('Test', 'Testing from Render', settings.DEFAULT_FROM_EMAIL, ['YOUR_EMAIL_HERE'])
print(f'Email sent: {result}')
"

3. CHECK ENVIRONMENT VARIABLES:
python -c "
import os
print('SENDGRID_API_KEY:', 'SET' if os.environ.get('SENDGRID_API_KEY') else 'MISSING')
print('DEFAULT_FROM_EMAIL:', os.environ.get('DEFAULT_FROM_EMAIL', 'MISSING'))
"

4. SEND VERIFICATION TO SPECIFIC EMAIL:
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()
from django.contrib.auth import get_user_model
from apps.users.email_utils import send_verification_email
User = get_user_model()
user = User.objects.get(email='YOUR_EMAIL_HERE')
user.email_verification_sent_at = None
user.save()
success = send_verification_email(user)
print(f'Verification sent: {success}')
"

REPLACE 'YOUR_EMAIL_HERE' with your actual email address!
""")

if __name__ == "__main__":
    # Import and setup for direct execution
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
    django.setup()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Reset all cooldowns
    print("Resetting email verification cooldowns...")
    count = User.objects.filter(email_verified=False).update(email_verification_sent_at=None)
    print(f"✅ Reset cooldown for {count} unverified users")
    
    # Show recent unverified users
    unverified = User.objects.filter(email_verified=False).order_by('-date_joined')[:5]
    print(f"\n📧 Recent unverified users:")
    for user in unverified:
        print(f"  - {user.email} (joined: {user.date_joined.strftime('%Y-%m-%d %H:%M')})")
    
    print(f"\n✅ Users can now request verification emails again!")