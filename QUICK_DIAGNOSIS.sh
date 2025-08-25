#!/bin/bash

# Quick diagnosis script to run on AWS server
# This will tell us exactly what's missing

echo "=========================================="
echo "DJANGO DIAGNOSIS - WHAT'S MISSING?"
echo "=========================================="

echo ""
echo "1. Current location and permissions:"
pwd
ls -la /var/www/startlinker/ 2>/dev/null || echo "  [MISSING] /var/www/startlinker directory"

echo ""
echo "2. Django project structure:"
if [ -f /var/www/startlinker/manage.py ]; then
    echo "  [OK] manage.py exists"
else
    echo "  [MISSING] manage.py"
fi

if [ -d /var/www/startlinker/startup_hub ]; then
    echo "  [OK] startup_hub directory exists"
    ls -la /var/www/startlinker/startup_hub/
else
    echo "  [MISSING] startup_hub directory"
fi

if [ -d /var/www/startlinker/apps ]; then
    echo "  [OK] apps directory exists"
    echo "  Apps found:"
    ls -la /var/www/startlinker/apps/
else
    echo "  [MISSING] apps directory - need to create it"
fi

echo ""
echo "3. URLs configuration:"
if [ -f /var/www/startlinker/startup_hub/urls.py ]; then
    echo "  [OK] Main urls.py exists"
    echo "  Content:"
    cat /var/www/startlinker/startup_hub/urls.py
else
    echo "  [MISSING] startup_hub/urls.py"
fi

echo ""
echo "4. Settings configuration:"
if [ -f /var/www/startlinker/startup_hub/settings.py ]; then
    echo "  [OK] settings.py exists"
    echo "  INSTALLED_APPS:"
    grep -A 15 "INSTALLED_APPS" /var/www/startlinker/startup_hub/settings.py 2>/dev/null || echo "  Could not find INSTALLED_APPS"
else
    echo "  [MISSING] settings.py"
fi

echo ""
echo "5. Django status:"
cd /var/www/startlinker 2>/dev/null || echo "Cannot cd to project directory"
if command -v python3 >/dev/null; then
    echo "  Python3 available: $(python3 --version)"
    
    if [ -f manage.py ]; then
        echo "  Django check:"
        python3 manage.py check 2>&1 | head -5
        
        echo "  Installed apps from Django:"
        python3 -c "
import os, sys
sys.path.append('/var/www/startlinker')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
try:
    import django
    django.setup()
    from django.conf import settings
    print('  INSTALLED_APPS:', settings.INSTALLED_APPS)
except Exception as e:
    print('  Error:', str(e))
" 2>/dev/null || echo "  Could not load Django settings"
    fi
else
    echo "  [ERROR] Python3 not available"
fi

echo ""
echo "6. Services status:"
systemctl is-active gunicorn || echo "  Gunicorn not running"
systemctl is-active nginx || echo "  Nginx not running"

echo ""
echo "7. Process check:"
ps aux | grep python | grep -v grep || echo "  No Python processes running"
ps aux | grep gunicorn | grep -v grep || echo "  No Gunicorn processes running"

echo ""
echo "8. Network check:"
netstat -tlnp | grep :8000 || echo "  Nothing listening on port 8000"

echo ""
echo "=========================================="
echo "RECOMMENDATIONS:"
echo "=========================================="

if [ ! -d /var/www/startlinker/apps ]; then
    echo "1. CREATE MISSING APPS - apps directory missing"
fi

if [ ! -f /var/www/startlinker/startup_hub/urls.py ]; then
    echo "2. CREATE URLs - main urls.py missing"
fi

if ! systemctl is-active gunicorn >/dev/null; then
    echo "3. START GUNICORN - service not running"
fi

echo ""
echo "Next: Run the appropriate fix commands based on what's missing above"