"""
Special admin setup views for production deployment
"""
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from .admin_setup import create_admin_user
import json

# Secret key for admin creation (should be set in environment)
ADMIN_SETUP_SECRET = os.environ.get('ADMIN_SETUP_SECRET', 'create-admin-2024-secret-key')

def is_admin_setup_request(request):
    """Check if request has the correct secret key"""
    secret = request.GET.get('secret') or request.POST.get('secret')
    return secret == ADMIN_SETUP_SECRET

@csrf_exempt
@require_http_methods(["GET", "POST"])
def setup_admin(request):
    """
    Special endpoint to create admin user in production
    Requires secret key for security
    
    Usage: 
    GET /api/users/setup-admin/?secret=your-secret-key
    """
    
    # Check if we're in production or have the secret key
    if not settings.DEBUG and not is_admin_setup_request(request):
        return JsonResponse({
            'error': 'Unauthorized. Secret key required.',
            'hint': 'Add ?secret=your-secret-key to the URL'
        }, status=403)
    
    # Create admin user
    result = create_admin_user()
    
    if request.GET.get('format') == 'html':
        # Return HTML response for browser viewing
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Setup - StartLinker</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 50px auto; 
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .success {{ color: #27ae60; }}
                .warning {{ color: #f39c12; }}
                .error {{ color: #e74c3c; }}
                .credentials {{
                    background: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-family: monospace;
                }}
                .admin-link {{
                    display: inline-block;
                    background: #3498db;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .admin-link:hover {{ background: #2980b9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 StartLinker Admin Setup</h1>
        """
        
        if result['status'] == 'created':
            html_content += f"""
                <div class="success">
                    <h2>✅ {result['message']}</h2>
                    <div class="credentials">
                        <strong>Admin Credentials:</strong><br>
                        Username: {result['username']}<br>
                        Email: {result['email']}<br>
                        Password: {result['password']}<br>
                    </div>
                    <p><strong>⚠️ Important:</strong> Save these credentials! The password won't be shown again.</p>
                    <a href="{result['admin_url']}" class="admin-link" target="_blank">Go to Admin Panel</a>
                </div>
            """
        elif result['status'] == 'exists':
            html_content += f"""
                <div class="warning">
                    <h2>ℹ️ {result['message']}</h2>
                    <p>Username: {result['username']}</p>
                    <p>Email: {result['email']}</p>
                    <p>Is Superuser: {result['is_superuser']}</p>
                    <p>Is Staff: {result['is_staff']}</p>
                    <a href="https://startlinker-backend.onrender.com/admin/" class="admin-link" target="_blank">Go to Admin Panel</a>
                </div>
            """
        else:
            html_content += f"""
                <div class="error">
                    <h2>❌ Error</h2>
                    <p>{result['message']}</p>
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content)
    
    # Return JSON response
    return JsonResponse(result, json_dumps_params={'indent': 2})

@require_http_methods(["GET"])
def admin_status(request):
    """Check if admin user exists"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    admin_exists = User.objects.filter(is_superuser=True).exists()
    admin_count = User.objects.filter(is_superuser=True).count()
    
    return JsonResponse({
        'admin_exists': admin_exists,
        'admin_count': admin_count,
        'setup_url': '/api/users/setup-admin/?format=html&secret=your-secret-key'
    })