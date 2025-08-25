# Manual Deployment Guide for Startlinker.com

Since automated deployment is having SSH key issues, here's how to manually deploy:

## Step 1: Check AWS EC2 Console

1. Go to AWS EC2 Console
2. Check if instance `44.219.216.107` is running
3. Note the correct SSH key pair name
4. Check Security Groups - ensure ports 80, 443, 22 are open

## Step 2: Get Correct SSH Key

If you don't have the correct SSH key for the server:
1. Download the correct key pair from AWS
2. Place it in this directory as `server-key.pem`
3. Set permissions: `chmod 600 server-key.pem`

## Step 3: Manual Upload and Deploy

### Upload Files
```bash
# Create deployment package
tar -czf backend_deploy.tar.gz apps startup_hub manage.py requirements.txt

# Upload to server (replace server-key.pem with your key)
scp -i server-key.pem backend_deploy.tar.gz ubuntu@44.219.216.107:/tmp/

# Connect to server
ssh -i server-key.pem ubuntu@44.219.216.107
```

### On Server - Run These Commands
```bash
# Go to web directory
cd /var/www/startlinker

# Extract files
sudo tar -xzf /tmp/backend_deploy.tar.gz

# Install dependencies
sudo pip3 install -r requirements.txt

# Run migrations
sudo python3 manage.py migrate --noinput

# Create test user
sudo python3 manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()

# Create test user
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

# Collect static files
sudo python3 manage.py collectstatic --noinput

# Set up Gunicorn service
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/startlinker
Environment="DJANGO_ENVIRONMENT=production"
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 startup_hub.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx configuration
sudo tee /etc/nginx/sites-available/startlinker > /dev/null << 'EOF'
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 44.219.216.107;
    
    client_max_body_size 50M;
    
    location /api/ {
        # CORS headers
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Add CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
    }
    
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static/ {
        alias /var/www/startlinker/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/www/startlinker/media/;
        expires 7d;
    }
    
    location / {
        root /var/www/startlinker/frontend/build;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/startlinker /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Start services
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl enable nginx
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Test API
curl -I http://localhost:8000/api/v1/
```

## Step 4: Update Frontend

On your local machine:

```bash
# Update frontend configuration
cd frontend
npm install
npm run build

# Upload frontend build
scp -r build/* ubuntu@44.219.216.107:/var/www/startlinker/frontend/
```

## Step 5: Test

After deployment, test:
1. Visit http://startlinker.com
2. Try logging in with:
   - Email: test@startlinker.com
   - Password: Test@123456

## Alternative: Use AWS Systems Manager

If SSH key issues persist, you can:
1. Go to AWS Systems Manager > Session Manager
2. Connect to your EC2 instance through the browser
3. Run all the deployment commands there

## Troubleshooting

If services fail to start:
```bash
# Check logs
sudo journalctl -u gunicorn -n 50
sudo tail -f /var/log/nginx/error.log

# Check if Django is running
sudo netstat -tlnp | grep 8000

# Restart services
sudo systemctl restart gunicorn nginx
```