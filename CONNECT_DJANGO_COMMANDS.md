# Connect Django to Frontend - Step by Step Commands

Your frontend is already running at http://44.219.216.107! Now let's connect Django.

## Step 1: Access Your Server

**Go to AWS Console:**
1. AWS Console → EC2 → Instances
2. Find instance with IP `44.219.216.107`
3. Click "Connect" → "Session Manager"
4. Click "Connect" (opens browser terminal)

## Step 2: Run These Commands in AWS Terminal

### Find Your Django Project
```bash
# Check if Django project exists
sudo find /var -name "manage.py" 2>/dev/null
sudo find /home -name "manage.py" 2>/dev/null

# Check common locations
ls -la /var/www/
ls -la /home/ubuntu/
ls -la /opt/

# Check what's running
ps aux | grep python
ps aux | grep gunicorn
sudo systemctl status gunicorn
```

### If Django Project Found
```bash
# Go to your Django project directory (replace with actual path)
cd /var/www/startlinker
# OR
cd /path/to/your/django/project

# Check if it's our project
ls -la apps/
cat startup_hub/settings/base.py | head -10

# Install/update requirements
sudo pip3 install -r requirements.txt

# Run migrations
sudo python3 manage.py migrate

# Create test user
sudo python3 manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()

try:
    user = User.objects.filter(email='test@startlinker.com').first()
    if not user:
        user = User.objects.create_user(
            username='testuser',
            email='test@startlinker.com',
            password='Test@123456',
            is_active=True
        )
    else:
        user.set_password('Test@123456')
        user.save()
    
    token, created = Token.objects.get_or_create(user=user)
    print(f'User: {user.email}')
    print(f'Token: {token.key}')
except Exception as e:
    print(f'Error: {e}')
EOF

# Test Django directly
sudo python3 manage.py runserver 127.0.0.1:8000 &
```

### If Django Project NOT Found
```bash
# Create project directory
sudo mkdir -p /var/www/startlinker
cd /var/www/startlinker

# You'll need to upload your Django code here
# For now, let's create a minimal setup to test

sudo tee requirements.txt > /dev/null << 'EOF'
Django==4.2
djangorestframework==3.14.0
django-cors-headers==4.0.0
python-dotenv==1.0.0
gunicorn==20.1.0
Pillow==10.0.0
EOF

sudo pip3 install -r requirements.txt
```

## Step 3: Configure Nginx (Critical!)

```bash
# Update nginx config to proxy API requests to Django
sudo tee /etc/nginx/sites-available/startlinker > /dev/null << 'EOF'
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 44.219.216.107;
    
    # API requests go to Django
    location /api/ {
        # Handle preflight CORS requests
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
        
        # Proxy to Django
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
    
    # Admin panel
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Static files
    location /static/ {
        alias /var/www/startlinker/staticfiles/;
        expires 30d;
    }
    
    # Media files
    location /media/ {
        alias /var/www/startlinker/media/;
        expires 7d;
    }
    
    # Everything else goes to React frontend
    location / {
        root /var/www/startlinker/frontend;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

## Step 4: Start Django Properly

```bash
# Set up Gunicorn service for Django
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=gunicorn daemon for StartLinker
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/startlinker
Environment="DJANGO_ENVIRONMENT=production"
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 startup_hub.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start gunicorn
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

## Step 5: Test Everything

```bash
# Test Django directly
curl http://127.0.0.1:8000/api/v1/

# Test through nginx
curl http://localhost/api/v1/

# Test login endpoint
curl -X POST http://localhost/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'
```

## Step 6: Check Logs If Issues

```bash
# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Check gunicorn logs
sudo journalctl -u gunicorn -f

# Check Django logs (if any)
sudo tail -f /var/www/startlinker/logs/django.log
```

## Quick Test Commands

After completing the setup, run these to verify:

```bash
# 1. Is Django running?
curl -I http://127.0.0.1:8000/

# 2. Is API accessible through nginx?
curl -I http://localhost/api/v1/

# 3. Does login work?
curl -X POST http://localhost/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'
```

## Expected Results

- Frontend: Already working at http://44.219.216.107
- Backend: Should respond with JSON from API endpoints
- Login: Should return user data and auth token

Run these commands in order, and let me know what you find!