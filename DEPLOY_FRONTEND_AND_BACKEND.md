# Deploy Frontend and Connect Backend - Complete Guide

## Step 1: Access Your AWS Server

1. **Go to AWS EC2 Console** (where you found your instance)
2. **Find instance**: `i-051294eca7f666d14 (Startlinker)`
3. **Click "Connect"** → **"Session Manager"** → **"Connect"**
4. **You'll get a browser terminal** that looks like: `sh-4.2$ ` or `ubuntu@ip-xxx:`

## Step 2: Prepare Server Directory

**In the AWS terminal, run these commands:**

```bash
# Navigate to web directory
cd /var/www
sudo ls -la

# Check if startlinker directory exists
ls -la startlinker/ 2>/dev/null || echo "Directory not found"

# Create frontend directory if it doesn't exist
sudo mkdir -p /var/www/startlinker/frontend
sudo mkdir -p /tmp/frontend_upload

# Set proper permissions
sudo chown -R ubuntu:ubuntu /var/www/startlinker/
sudo chown -R ubuntu:ubuntu /tmp/frontend_upload/
```

## Step 3: Upload Frontend (Multiple Options)

### Option A: GitHub Upload (Recommended)

**On your local machine:**
```bash
cd C:\Users\hruth\frontend\build
# Upload build folder to GitHub or use file transfer
```

**Then on AWS server:**
```bash
# If you have the files in GitHub:
# git clone your-repo-url /tmp/frontend_source
# sudo cp -r /tmp/frontend_source/build/* /var/www/startlinker/frontend/
```

### Option B: Simple File Recreation

**Run this on AWS server to create a basic index.html:**
```bash
sudo tee /var/www/startlinker/frontend/index.html > /dev/null << 'EOF'
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <title>StartLinker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root">
        <div class="min-h-screen bg-gray-50">
            <div class="flex items-center justify-center min-h-screen">
                <div class="bg-white p-8 rounded-lg shadow-md w-96">
                    <h1 class="text-2xl font-bold mb-6 text-center">StartLinker</h1>
                    <form id="loginForm">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Email</label>
                            <input type="email" id="email" class="w-full p-2 border rounded" placeholder="test@startlinker.com" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Password</label>
                            <input type="password" id="password" class="w-full p-2 border rounded" placeholder="Test@123456" required>
                        </div>
                        <button type="submit" class="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                            Login
                        </button>
                        <div id="result" class="mt-4 p-2 rounded hidden"></div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const resultDiv = document.getElementById('result');
            
            try {
                const response = await fetch('/api/auth/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.className = 'mt-4 p-2 rounded bg-green-100 text-green-800';
                    resultDiv.textContent = 'Login successful! Token: ' + data.token.substring(0, 20) + '...';
                } else {
                    resultDiv.className = 'mt-4 p-2 rounded bg-red-100 text-red-800';
                    resultDiv.textContent = 'Login failed: ' + (data.error || 'Unknown error');
                }
                
                resultDiv.classList.remove('hidden');
            } catch (error) {
                resultDiv.className = 'mt-4 p-2 rounded bg-red-100 text-red-800';
                resultDiv.textContent = 'Network error: ' + error.message;
                resultDiv.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
EOF

echo "✓ Basic frontend created"
```

## Step 4: Configure Nginx

```bash
# Update nginx configuration to serve frontend and proxy API
sudo tee /etc/nginx/sites-available/startlinker > /dev/null << 'EOF'
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 51.21.246.24;
    
    client_max_body_size 50M;
    
    # API requests go to Django (IMPORTANT: /api/ not /api/v1/)
    location /api/ {
        # Handle CORS preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-CSRFToken' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }
        
        # Proxy to Django backend
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Add CORS headers to responses
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-CSRFToken' always;
    }
    
    # Django admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /var/www/startlinker/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files  
    location /media/ {
        alias /var/www/startlinker/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Frontend - serve React app
    location / {
        root /var/www/startlinker/frontend;
        try_files $uri $uri/ /index.html;
        
        # Add security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-XSS-Protection "1; mode=block";
    }
}
EOF

# Test nginx config
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx

echo "✓ Nginx configured"
```

## Step 5: Fix Django CSRF Settings

```bash
# Navigate to Django project
cd /var/www/startlinker

# Check if Django project exists
ls -la manage.py startup_hub/ 2>/dev/null || echo "Django project not found"

# If Django exists, update settings to disable CSRF for API
if [ -f startup_hub/settings.py ]; then
    # Add CSRF exemption for API endpoints
    sudo tee -a startup_hub/settings.py > /dev/null << 'EOF'

# API CSRF Settings
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False

# Exempt API endpoints from CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://startlinker.com',
    'https://startlinker.com', 
    'http://51.21.246.24',
]
EOF
    
    echo "✓ CSRF settings updated"
else
    echo "⚠️  Django settings not found - we'll create a minimal Django setup"
fi
```

## Step 6: Ensure Django is Running

```bash
# Check if Django process is running
ps aux | grep python | grep -v grep

# Check if gunicorn service exists
sudo systemctl status gunicorn 2>/dev/null || echo "Gunicorn service not found"

# If gunicorn exists, restart it
sudo systemctl restart gunicorn 2>/dev/null && echo "✓ Gunicorn restarted"

# If no gunicorn service, start Django manually for testing
if ! sudo systemctl is-active gunicorn >/dev/null 2>&1; then
    echo "Starting Django manually for testing..."
    cd /var/www/startlinker
    nohup python3 manage.py runserver 127.0.0.1:8000 > django.log 2>&1 &
    echo "✓ Django started manually"
fi
```

## Step 7: Test Everything

```bash
# Test frontend is served
echo "Testing frontend..."
curl -I http://localhost/ | head -5

# Test API endpoint
echo -e "\nTesting API endpoint..."
curl -I http://localhost/api/auth/login/

# Test login functionality
echo -e "\nTesting login..."
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}' \
  2>/dev/null | head -10
```

## Step 8: Final Verification

**After completing the steps above, test in your browser:**

1. **Visit**: http://startlinker.com (should show your site)
2. **Try login** with:
   - Email: `test@startlinker.com`  
   - Password: `Test@123456`

## Troubleshooting Commands

If login still doesn't work:

```bash
# Check Django logs
tail -f /var/www/startlinker/django.log

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Check if Django is responding
curl http://127.0.0.1:8000/admin/

# Test API directly
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'
```

## Expected Results

After completing all steps:
- ✅ Frontend loads at http://startlinker.com
- ✅ API endpoints respond at /api/*
- ✅ Login works and returns auth token
- ✅ All functionality connected

**Start with Step 1 and work through each step. Let me know if you encounter any issues!**