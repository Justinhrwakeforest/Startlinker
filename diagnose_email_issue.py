"""
Comprehensive email debugging script for Render deployment
Run this in Render Shell to diagnose why emails aren't sending
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def diagnose_email_configuration():
    """Comprehensive diagnosis of email configuration"""
    
    print("\n" + "="*70)
    print("EMAIL CONFIGURATION DIAGNOSIS FOR RENDER")
    print("="*70)
    
    issues_found = []
    warnings = []
    
    # 1. Check SendGrid API Key
    print("\n1. CHECKING SENDGRID API KEY...")
    api_key = os.environ.get('SENDGRID_API_KEY')
    if api_key:
        print(f"   ✓ Found: {api_key[:20]}...")
        print(f"   Length: {len(api_key)} characters")
        
        # Check if it looks like a valid SendGrid key
        if not api_key.startswith('SG.'):
            issues_found.append("API key doesn't start with 'SG.' - might not be a valid SendGrid key")
        if len(api_key) < 50:
            issues_found.append(f"API key seems too short ({len(api_key)} chars) - SendGrid keys are usually 69+ chars")
    else:
        issues_found.append("SENDGRID_API_KEY environment variable is NOT set!")
    
    # 2. Check Email Backend
    print("\n2. CHECKING EMAIL BACKEND...")
    email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not configured')
    print(f"   Current backend: {email_backend}")
    
    expected_backend = 'apps.users.sendgrid_backend.SendGridBackend'
    if email_backend != expected_backend:
        issues_found.append(f"Email backend is not set to SendGrid! Current: {email_backend}")
    else:
        print("   ✓ Using SendGrid backend")
    
    # 3. Check Default From Email
    print("\n3. CHECKING FROM EMAIL...")
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if from_email:
        print(f"   ✓ DEFAULT_FROM_EMAIL: {from_email}")
    else:
        issues_found.append("DEFAULT_FROM_EMAIL is not configured!")
    
    # 4. Check Frontend URL
    print("\n4. CHECKING FRONTEND URL...")
    frontend_url = getattr(settings, 'FRONTEND_URL', None)
    if frontend_url:
        print(f"   ✓ FRONTEND_URL: {frontend_url}")
    else:
        warnings.append("FRONTEND_URL not set - verification links might be incorrect")
    
    # 5. Test SendGrid Import
    print("\n5. TESTING SENDGRID IMPORT...")
    try:
        import sendgrid
        print(f"   ✓ SendGrid version: {sendgrid.__version__}")
        
        # Check if SendGrid client can be created
        if api_key:
            try:
                sg = sendgrid.SendGridAPIClient(api_key=api_key)
                print("   ✓ SendGrid client created successfully")
            except Exception as e:
                issues_found.append(f"Failed to create SendGrid client: {e}")
    except ImportError as e:
        issues_found.append(f"SendGrid package not installed or import error: {e}")
    
    # 6. Test Custom Backend
    print("\n6. TESTING CUSTOM SENDGRID BACKEND...")
    try:
        from apps.users.sendgrid_backend import SendGridBackend
        backend = SendGridBackend()
        
        if hasattr(backend, 'api_key'):
            if backend.api_key:
                print("   ✓ Backend has API key configured")
            else:
                issues_found.append("Backend initialized but API key is None!")
        
        if hasattr(backend, 'client'):
            if backend.client:
                print("   ✓ Backend has SendGrid client")
            else:
                issues_found.append("Backend client is None - API key might be missing")
                
    except Exception as e:
        issues_found.append(f"Error loading custom SendGrid backend: {e}")
    
    # 7. Check CORS and ALLOWED_HOSTS
    print("\n7. CHECKING DEPLOYMENT SETTINGS...")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS[:3]}...")  # Show first 3
    
    # 8. Check if in Sandbox Mode
    print("\n8. CHECKING SENDGRID SANDBOX MODE...")
    sandbox_mode = getattr(settings, 'SENDGRID_SANDBOX_MODE_IN_DEBUG', None)
    if sandbox_mode and not settings.DEBUG:
        warnings.append("SENDGRID_SANDBOX_MODE_IN_DEBUG is True but DEBUG is False")
    print(f"   Sandbox mode: {sandbox_mode}")
    
    # Print Summary
    print("\n" + "="*70)
    print("DIAGNOSIS SUMMARY")
    print("="*70)
    
    if issues_found:
        print("\n❌ CRITICAL ISSUES FOUND:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✓ No critical issues found in configuration")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
    
    return len(issues_found) == 0

def test_actual_email_send():
    """Test sending an actual email"""
    
    print("\n" + "="*70)
    print("TESTING ACTUAL EMAIL SEND")
    print("="*70)
    
    test_email = input("\nEnter email address to send test to (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipping email send test")
        return
    
    print(f"\nAttempting to send test email to: {test_email}")
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Try sending with detailed error catching
        result = send_mail(
            subject='StartLinker Email Test from Render',
            message='This is a test email from your StartLinker deployment on Render.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        
        if result == 1:
            print("✓ Email sent successfully!")
            print(f"  Check inbox for: {test_email}")
        else:
            print(f"❌ Email send returned: {result}")
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        
        # Try to get more details about the error
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()
        
        # Common SendGrid error meanings
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n🔧 FIX: Your SendGrid API key is invalid or doesn't have permissions")
            print("   1. Check the API key is copied correctly (no spaces)")
            print("   2. Ensure the API key has 'Mail Send' permissions in SendGrid")
            
        elif "403" in str(e) or "Forbidden" in str(e):
            print("\n🔧 FIX: Your SendGrid account might not be verified")
            print("   1. Complete SendGrid account verification")
            print("   2. Verify your sender identity (Single Sender or Domain)")
            
        elif "does not match a verified Sender" in str(e):
            print("\n🔧 FIX: Your sender email is not verified in SendGrid")
            print("   1. Go to SendGrid → Settings → Sender Authentication")
            print("   2. Add and verify your sender email address")
            print(f"   3. Verify this email: {settings.DEFAULT_FROM_EMAIL}")

def check_sendgrid_account_status():
    """Check SendGrid account status via API"""
    
    print("\n" + "="*70)
    print("CHECKING SENDGRID ACCOUNT STATUS")
    print("="*70)
    
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        print("Cannot check - API key not found")
        return
    
    try:
        import requests
        
        # Test API key validity
        headers = {'Authorization': f'Bearer {api_key}'}
        
        # Check API key scopes
        print("\nChecking API key permissions...")
        response = requests.get(
            'https://api.sendgrid.com/v3/scopes',
            headers=headers
        )
        
        if response.status_code == 200:
            scopes = response.json().get('scopes', [])
            print(f"✓ API key is valid. Permissions: {', '.join(scopes[:5])}...")
            
            if 'mail.send' not in scopes:
                print("❌ API key doesn't have 'mail.send' permission!")
        else:
            print(f"❌ API key check failed: {response.status_code} - {response.text}")
        
        # Check verified senders
        print("\nChecking verified senders...")
        response = requests.get(
            'https://api.sendgrid.com/v3/verified_senders',
            headers=headers
        )
        
        if response.status_code == 200:
            senders = response.json().get('results', [])
            if senders:
                print("✓ Verified senders:")
                for sender in senders:
                    print(f"   - {sender.get('from_email')} ({sender.get('verified', False)})")
            else:
                print("❌ No verified senders found! You must verify at least one sender.")
        else:
            print(f"Could not fetch verified senders: {response.status_code}")
            
    except Exception as e:
        print(f"Error checking SendGrid account: {e}")

def main():
    """Main diagnostic routine"""
    
    print("\nStartLinker Email Diagnostic Tool")
    print("Running on Render deployment...")
    
    # Run diagnosis
    config_ok = diagnose_email_configuration()
    
    if config_ok:
        print("\n✓ Configuration looks good!")
        
        # Check SendGrid account
        check_sendgrid_account_status()
        
        # Offer to send test email
        test_actual_email_send()
    else:
        print("\n❌ Please fix the configuration issues above before testing email sends")
        print("\nCommon fixes:")
        print("1. Ensure SENDGRID_API_KEY is set in Render environment variables")
        print("2. Make sure the API key starts with 'SG.' and is complete")
        print("3. Verify your sender email in SendGrid dashboard")
        print("4. Check that your SendGrid account is activated (not in sandbox)")

if __name__ == "__main__":
    main()