#!/bin/bash

# Complete server fix for startlinker.com
# Run this on the AWS server

echo "=========================================="
echo "COMPLETE STARTLINKER SERVER FIX"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Stopping all services${NC}"
sudo systemctl stop gunicorn
sudo systemctl stop nginx

echo -e "${YELLOW}Step 2: Setting up Django backend${NC}"
cd /var/www/startlinker

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << 'EOF'
DJANGO_ENVIRONMENT=production
SECRET_KEY=django-insecure-production-key-change-this-immediately-$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=startlinker.com,www.startlinker.com,13.50.234.250,localhost
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=https://startlinker.com,http://startlinker.com,http://13.50.234.250
EOF
fi

echo -e "${YELLOW}Step 3: Installing Python dependencies${NC}"
sudo pip3 install django djangorestframework django-cors-headers python-dotenv gunicorn

echo -e "${YELLOW}Step 4: Running migrations${NC}"
sudo python3 manage.py migrate --noinput

echo -e "${YELLOW}Step 5: Creating superuser and test user${NC}"
sudo python3 manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()

# Create superuser
try:
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@startlinker.com',
            password='Admin@123456'
        )
        print(f'Created superuser: {admin.email}')
    else:
        print(f'Superuser exists: {admin.email}')
except Exception as e:
    print(f'Error creating superuser: {e}')

# Create test user
try:
    user = User.objects.filter(email='test@startlinker.com').first()
    if not user:
        user = User.objects.create_user(
            username='testuser',
            email='test@startlinker.com',
            password='Test@123456'
        )
    else:
        user.set_password('Test@123456')
        user.save()
    
    token, created = Token.objects.get_or_create(user=user)
    print(f'Test user: {user.email}')
    print(f'Token: {token.key}')
except Exception as e:
    print(f'Error creating test user: {e}')

# Create basic data
from apps.startups.models import Industry
from apps.jobs.models import JobType

industries = ['Technology', 'Healthcare', 'Finance', 'Education']
for name in industries:
    Industry.objects.get_or_create(name=name)
    
job_types = [('Full-time', 'full-time'), ('Part-time', 'part-time')]
for name, slug in job_types:
    JobType.objects.get_or_create(name=name, defaults={'slug': slug})

print('Basic data created')
EOF

echo -e "${YELLOW}Step 6: Collecting static files${NC}"
sudo python3 manage.py collectstatic --noinput

echo -e "${YELLOW}Step 7: Setting up Gunicorn service${NC}"
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=gunicorn daemon for StartLinker
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/startlinker
Environment="DJANGO_ENVIRONMENT=production"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    startup_hub.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}Step 8: Creating log directories${NC}"
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/log/nginx
sudo chown -R ubuntu:www-data /var/log/gunicorn
sudo chown -R ubuntu:www-data /var/www/startlinker

echo -e "${YELLOW}Step 9: Setting up Nginx${NC}"
sudo tee /etc/nginx/sites-available/startlinker > /dev/null << 'EOF'
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 13.50.234.250;
    
    client_max_body_size 50M;
    
    # CORS and security headers
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location /api/ {
        # Handle CORS preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin' always;
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
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-CSRFToken' always;
    }
    
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/startlinker/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/www/startlinker/media/;
        expires 7d;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        root /var/www/startlinker/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Add CORS headers for frontend assets
        add_header 'Access-Control-Allow-Origin' '*' always;
    }
}
EOF

echo -e "${YELLOW}Step 10: Enabling Nginx site${NC}"
sudo ln -sf /etc/nginx/sites-available/startlinker /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo -e "${YELLOW}Step 11: Testing configurations${NC}"
sudo nginx -t

echo -e "${YELLOW}Step 12: Starting services${NC}"
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl enable nginx
sudo systemctl start gunicorn
sudo systemctl start nginx

echo -e "${YELLOW}Step 13: Checking service status${NC}"
sudo systemctl status gunicorn --no-pager | head -10
echo ""
sudo systemctl status nginx --no-pager | head -10

echo -e "${YELLOW}Step 14: Testing API${NC}"
echo "Testing local API..."
curl -I http://localhost:8000/api/v1/

echo ""
echo "Testing through Nginx..."
curl -I http://localhost/api/v1/

echo ""
echo -e "${GREEN}=========================================="
echo "SERVER FIX COMPLETE!"
echo "=========================================="
echo -e "${NC}"
echo "Test credentials:"
echo "  Admin: admin@startlinker.com / Admin@123456"
echo "  Test: test@startlinker.com / Test@123456"
echo ""
echo "Test the API:"
echo "  curl -X POST http://13.50.234.250/api/v1/auth/login/ \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@startlinker.com\",\"password\":\"Test@123456\"}'"
echo ""
echo "Check logs if issues persist:"
echo "  sudo tail -f /var/log/gunicorn/error.log"
echo "  sudo tail -f /var/log/nginx/error.log"