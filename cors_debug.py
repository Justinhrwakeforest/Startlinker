#!/usr/bin/env python3
"""
Debug CORS configuration on Render
Run in Render Shell to check CORS settings
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings.render')
django.setup()

from django.conf import settings

def debug_cors_settings():
    """Debug CORS configuration"""
    print("=== CORS Configuration Debug ===")
    
    print(f"\n1. CORS Settings:")
    print(f"   CORS_ALLOWED_ORIGINS: {getattr(settings, 'CORS_ALLOWED_ORIGINS', 'Not set')}")
    print(f"   CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', 'Not set')}")
    print(f"   CORS_ALLOW_CREDENTIALS: {getattr(settings, 'CORS_ALLOW_CREDENTIALS', 'Not set')}")
    print(f"   CORS_ALLOW_METHODS: {getattr(settings, 'CORS_ALLOW_METHODS', 'Not set')}")
    print(f"   CORS_ALLOW_HEADERS: {getattr(settings, 'CORS_ALLOW_HEADERS', 'Not set')}")
    
    print(f"\n2. Environment Variables:")
    print(f"   CORS_ALLOWED_ORIGINS (env): {os.environ.get('CORS_ALLOWED_ORIGINS', 'Not set')}")
    
    print(f"\n3. Middleware Check:")
    middleware = getattr(settings, 'MIDDLEWARE', [])
    cors_middleware = 'corsheaders.middleware.CorsMiddleware'
    if cors_middleware in middleware:
        print(f"   ✅ CORS middleware is installed")
        print(f"   Position: {middleware.index(cors_middleware) + 1} of {len(middleware)}")
    else:
        print(f"   ❌ CORS middleware is NOT installed")
    
    print(f"\n4. CSRF Settings:")
    print(f"   CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'Not set')}")
    
    print(f"\n5. Domain Resolution Test:")
    import socket
    try:
        ip = socket.gethostbyname('startlinker.com')
        print(f"   startlinker.com resolves to: {ip}")
    except:
        print(f"   ❌ Cannot resolve startlinker.com")
    
    print(f"\n6. Suggested Fix:")
    print(f"   Add to Render Environment Variables:")
    print(f"   CORS_ALLOWED_ORIGINS=https://startlinker.com,https://www.startlinker.com")

if __name__ == "__main__":
    debug_cors_settings()