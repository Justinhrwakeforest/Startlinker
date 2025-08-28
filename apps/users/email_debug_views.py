# apps/users/email_debug_views.py

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from .email_utils import send_verification_email
from .models import User
import json
import os
import logging

logger = logging.getLogger(__name__)

def email_config_debug(request):
    """Debug endpoint to check email configuration - GET /api/debug/email-config/"""
    
    config_info = {
        "email_backend": getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
        "default_from_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured'),
        "sendgrid_api_key_configured": bool(os.environ.get('SENDGRID_API_KEY')),
        "sendgrid_api_key_starts_correct": False,
        "frontend_url": getattr(settings, 'FRONTEND_URL', 'Not configured'),
        "require_email_verification": getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False),
        "debug_mode": settings.DEBUG,
        "environment": os.environ.get('DJANGO_SETTINGS_MODULE', 'Unknown')
    }
    
    # Check API key format without exposing it
    api_key = os.environ.get('SENDGRID_API_KEY')
    if api_key:
        config_info["sendgrid_api_key_starts_correct"] = api_key.startswith('SG.')
        config_info["sendgrid_api_key_length"] = len(api_key)
        config_info["sendgrid_api_key_preview"] = f"{api_key[:10]}...{api_key[-5:]}"
    
    # Check if SendGrid can be imported
    try:
        import sendgrid
        config_info["sendgrid_import_success"] = True
        config_info["sendgrid_version"] = getattr(sendgrid, '__version__', 'Unknown')
    except ImportError as e:
        config_info["sendgrid_import_success"] = False
        config_info["sendgrid_import_error"] = str(e)
    
    # Check custom backend
    try:
        from .sendgrid_backend import SendGridBackend
        backend = SendGridBackend()
        config_info["custom_backend_loaded"] = True
        config_info["backend_has_client"] = hasattr(backend, 'client') and backend.client is not None
    except Exception as e:
        config_info["custom_backend_loaded"] = False
        config_info["backend_error"] = str(e)
    
    return JsonResponse({
        "status": "success",
        "message": "Email configuration debug info",
        "configuration": config_info
    }, json_dumps_params={'indent': 2})

@csrf_exempt
def send_test_email(request):
    """Send a test email - POST /api/debug/send-test-email/"""
    
    if request.method != 'POST':
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    test_email = data.get('email')
    if not test_email:
        return JsonResponse({"error": "Email address required"}, status=400)
    
    try:
        # Send basic test email
        result = send_mail(
            subject='StartLinker Test Email from Render',
            message=f'''
This is a test email from your StartLinker deployment.

Configuration:
- Environment: {os.environ.get('DJANGO_SETTINGS_MODULE')}
- From Email: {settings.DEFAULT_FROM_EMAIL}
- Backend: {settings.EMAIL_BACKEND}
- Debug Mode: {settings.DEBUG}

If you received this email, your SendGrid configuration is working correctly!
''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        
        if result == 1:
            return JsonResponse({
                "status": "success",
                "message": f"Test email sent successfully to {test_email}",
                "from_email": settings.DEFAULT_FROM_EMAIL
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": f"Email send returned {result} (should be 1)"
            })
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Test email send failed: {error_msg}")
        
        # Provide specific help based on common errors
        help_message = ""
        if "401" in error_msg or "Unauthorized" in error_msg:
            help_message = "API key is invalid or lacks permissions. Check SendGrid dashboard."
        elif "403" in error_msg or "Forbidden" in error_msg:
            help_message = "Account verification required. Complete SendGrid identity verification."
        elif "does not match a verified Sender" in error_msg:
            help_message = f"Sender email '{settings.DEFAULT_FROM_EMAIL}' must be verified in SendGrid."
        
        return JsonResponse({
            "status": "error",
            "message": error_msg,
            "help": help_message,
            "from_email": settings.DEFAULT_FROM_EMAIL
        }, status=500)

@csrf_exempt  
def send_verification_test(request):
    """Send a verification email to test user - POST /api/debug/send-verification-test/"""
    
    if request.method != 'POST':
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    test_email = data.get('email')
    if not test_email:
        return JsonResponse({"error": "Email address required"}, status=400)
    
    try:
        # Create or get test user
        test_user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'username': f'test_{test_email.split("@")[0]}',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Send verification email
        success = send_verification_email(test_user, request)
        
        if success:
            return JsonResponse({
                "status": "success", 
                "message": f"Verification email sent to {test_email}",
                "user_created": created,
                "verification_token_generated": bool(test_user.email_verification_token)
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": "Verification email failed to send"
            })
            
    except Exception as e:
        logger.error(f"Verification email test failed: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

def email_debug_ui(request):
    """Simple UI for testing emails - GET /api/debug/email-ui/"""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StartLinker Email Debug Tool</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #007cba; color: white; padding: 10px 15px; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background: #005a8b; }
            input[type="email"] { width: 300px; padding: 8px; margin: 5px; }
            .result { margin-top: 10px; padding: 10px; border-radius: 3px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>StartLinker Email Debug Tool</h1>
        <p>Use this tool to test email functionality on your Render deployment.</p>
        
        <div class="section">
            <h3>1. Check Email Configuration</h3>
            <button onclick="checkConfig()">Check Configuration</button>
            <div id="configResult"></div>
        </div>
        
        <div class="section">
            <h3>2. Send Test Email</h3>
            <input type="email" id="testEmail" placeholder="Enter your email address">
            <button onclick="sendTestEmail()">Send Test Email</button>
            <div id="testResult"></div>
        </div>
        
        <div class="section">
            <h3>3. Send Verification Email</h3>
            <input type="email" id="verificationEmail" placeholder="Enter your email address">
            <button onclick="sendVerificationEmail()">Send Verification Email</button>
            <div id="verificationResult"></div>
        </div>

        <script>
            function checkConfig() {
                document.getElementById('configResult').innerHTML = 'Checking...';
                fetch('/api/debug/email-config/')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('configResult').innerHTML = 
                            '<div class="result success"><pre>' + JSON.stringify(data.configuration, null, 2) + '</pre></div>';
                    })
                    .catch(error => {
                        document.getElementById('configResult').innerHTML = 
                            '<div class="result error">Error: ' + error + '</div>';
                    });
            }
            
            function sendTestEmail() {
                const email = document.getElementById('testEmail').value;
                if (!email) {
                    alert('Please enter an email address');
                    return;
                }
                
                document.getElementById('testResult').innerHTML = 'Sending...';
                fetch('/api/debug/send-test-email/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                })
                .then(response => response.json())
                .then(data => {
                    const className = data.status === 'success' ? 'success' : 'error';
                    document.getElementById('testResult').innerHTML = 
                        '<div class="result ' + className + '">' + data.message + 
                        (data.help ? '<br><strong>Help:</strong> ' + data.help : '') + '</div>';
                })
                .catch(error => {
                    document.getElementById('testResult').innerHTML = 
                        '<div class="result error">Error: ' + error + '</div>';
                });
            }
            
            function sendVerificationEmail() {
                const email = document.getElementById('verificationEmail').value;
                if (!email) {
                    alert('Please enter an email address');
                    return;
                }
                
                document.getElementById('verificationResult').innerHTML = 'Sending...';
                fetch('/api/debug/send-verification-test/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                })
                .then(response => response.json())
                .then(data => {
                    const className = data.status === 'success' ? 'success' : 'error';
                    document.getElementById('verificationResult').innerHTML = 
                        '<div class="result ' + className + '">' + data.message + '</div>';
                })
                .catch(error => {
                    document.getElementById('verificationResult').innerHTML = 
                        '<div class="result error">Error: ' + error + '</div>';
                });
            }
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html)