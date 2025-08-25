#!/bin/bash

# Deployment script to fix posting issues on AWS server
# This script will update both backend and frontend with the fixes

echo "=========================================="
echo "DEPLOYING POSTING FIXES TO AWS"
echo "=========================================="

# Configuration
SERVER_IP="13.50.234.250"
SSH_KEY="startlinker-key"
REMOTE_USER="ubuntu"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Creating deployment package...${NC}"

# Create a temporary directory for deployment
rm -rf deploy_temp
mkdir -p deploy_temp

# Copy backend files
echo "Copying backend files..."
cp -r startup_hub deploy_temp/
cp requirements.txt deploy_temp/
cp manage.py deploy_temp/

# Create deployment archive
echo "Creating deployment archive..."
cd deploy_temp
tar -czf ../backend_fix.tar.gz *
cd ..

echo -e "${GREEN}✓ Deployment package created${NC}"

echo -e "${YELLOW}Step 2: Uploading to server...${NC}"

# Upload the package
scp -i $SSH_KEY backend_fix.tar.gz $REMOTE_USER@$SERVER_IP:/tmp/

echo -e "${GREEN}✓ Files uploaded${NC}"

echo -e "${YELLOW}Step 3: Applying fixes on server...${NC}"

# SSH into server and apply fixes
ssh -i $SSH_KEY $REMOTE_USER@$SERVER_IP << 'ENDSSH'

echo "Extracting files..."
cd /var/www/startlinker
sudo tar -xzf /tmp/backend_fix.tar.gz

echo "Installing any new dependencies..."
sudo pip3 install -r requirements.txt

echo "Running migrations..."
sudo python3 manage.py migrate

echo "Collecting static files..."
sudo python3 manage.py collectstatic --noinput

echo "Creating/updating nginx configuration..."
sudo tee /etc/nginx/sites-available/startlinker << 'EOF'
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 13.50.234.250;
    
    client_max_body_size 50M;
    
    # Handle OPTIONS requests for CORS
    location /api/ {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With, X-CSRFToken' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 86400 always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            return 204;
        }
        
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Add CORS headers to responses
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
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

echo "Enabling nginx site..."
sudo ln -sf /etc/nginx/sites-available/startlinker /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "Testing nginx configuration..."
sudo nginx -t

echo "Restarting services..."
sudo systemctl restart nginx
sudo systemctl restart gunicorn

echo "Creating systemd service for Django if not exists..."
sudo tee /etc/systemd/system/gunicorn.service << 'EOF'
[Unit]
Description=gunicorn daemon for StartLinker
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

sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn

echo "Checking service status..."
sudo systemctl status gunicorn --no-pager

echo "Testing API endpoint..."
curl -I http://127.0.0.1:8000/api/v1/

ENDSSH

echo -e "${GREEN}✓ Server configuration updated${NC}"

# Clean up
rm -rf deploy_temp
rm -f backend_fix.tar.gz

echo -e "${YELLOW}Step 4: Updating frontend configuration...${NC}"

# Create frontend fix
cat > frontend_api_fix.js << 'EOF'
// Update this file in frontend/src/services/api.js or frontend/src/config/api.config.js

const getApiUrl = () => {
  if (window.location.hostname === 'startlinker.com' || 
      window.location.hostname === 'www.startlinker.com') {
    return 'http://startlinker.com/api/v1';
  }
  return 'http://13.50.234.250/api/v1';
};

export const API_BASE_URL = getApiUrl();

// Setup axios defaults
import axios from 'axios';

axios.defaults.baseURL = API_BASE_URL;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add token to requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default axios;
EOF

echo -e "${GREEN}✓ Frontend configuration created${NC}"

echo "=========================================="
echo -e "${GREEN}DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update frontend/src/services/api.js with the configuration in frontend_api_fix.js"
echo "2. Rebuild frontend: cd frontend && npm run build"
echo "3. Deploy frontend build to server"
echo "4. Test the functionality at http://startlinker.com"

echo -e "${YELLOW}Test the API:${NC}"
echo "curl -X POST http://13.50.234.250/api/v1/auth/login/ -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"password\"}'"