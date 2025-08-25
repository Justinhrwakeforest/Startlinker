# Simple Deployment Commands

## The Issue
Your SSH key `startlinker-key` doesn't match the AWS server. Here are your options:

## Option 1: Use AWS Console (Easiest)

1. **Go to AWS EC2 Console**
   - Find your instance with IP 44.219.216.107
   - Click "Connect" → "Session Manager" 
   - This opens a browser-based terminal

2. **Run these commands in the AWS browser terminal:**

```bash
# Install required packages
sudo apt update
sudo apt install -y python3-pip nginx

# Create web directory
sudo mkdir -p /var/www/startlinker
cd /var/www/startlinker

# Create a simple Django setup
sudo tee requirements.txt > /dev/null << 'EOF'
Django==4.2
djangorestframework==3.14.0
django-cors-headers==4.0.0
python-dotenv==1.0.0
gunicorn==20.1.0
EOF

# Install Python packages
sudo pip3 install -r requirements.txt

# Create minimal Django project (we'll upload your full code later)
sudo python3 -c "
import django
from django.core.management import execute_from_command_line
execute_from_command_line(['django-admin', 'startproject', 'startup_hub', '.'])
"

# Configure nginx
sudo tee /etc/nginx/sites-available/startlinker > /dev/null << 'EOF'
server {
    listen 80;
    server_name startlinker.com www.startlinker.com 44.219.216.107;
    
    location /api/ {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
            return 204;
        }
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        add_header 'Access-Control-Allow-Origin' '*';
    }
    
    location / {
        root /var/www/startlinker/frontend;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/startlinker /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl restart nginx
sudo systemctl enable nginx

# Test - this should return status info
curl -I http://localhost/
```

## Option 2: Find Correct SSH Key

1. **Check AWS EC2 Console:**
   - Go to your instance details
   - Look for "Key pair name" 
   - Download that key if you don't have it

2. **Or create a new key pair:**
   - EC2 → Key Pairs → Create Key Pair
   - Download the .pem file
   - Update your instance to use this key

## Option 3: Test Current Setup

Let's test if your current server is already working:

**Run this in Command Prompt:**
```cmd
curl http://44.219.216.107/
```

If it responds, your server is up and we just need to configure it properly.

## What We Need to Do

The main issues are:
1. ✅ **Fixed**: Frontend now points to correct IP (44.219.216.107)  
2. ✅ **Fixed**: Backend serializer accepts `remember_me` field
3. ❌ **Need**: Deploy updated code to server
4. ❌ **Need**: Configure nginx with CORS headers
5. ❌ **Need**: Start Django with updated code

## Next Steps

Please try Option 1 (AWS Console) first - it's the easiest. Once you get into the server terminal, I can provide the exact commands to run.