#!/bin/bash
# Quick EC2 Setup Script - Runs directly on EC2

echo "========================================="
echo "StartLinker Quick EC2 Setup"
echo "========================================="

# Install required packages
echo "Installing packages..."
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx postgresql15

# Clone the repository
echo "Setting up application directory..."
sudo mkdir -p /opt/startlinker
sudo chown ec2-user:ec2-user /opt/startlinker
cd /opt/startlinker

# Create a simple Django app with SQLite for now
echo "Creating Django application..."
cat > requirements.txt << 'EOF'
Django==4.2.11
djangorestframework==3.14.0
django-cors-headers==4.3.1
gunicorn==21.2.0
Pillow==10.2.0
python-dotenv==1.0.1
dj-database-url==2.1.0
whitenoise==6.6.0
psycopg2-binary==2.9.9
boto3==1.34.69
django-storages==1.14.2
EOF

pip3 install --user -r requirements.txt

# Create environment file
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=44.219.216.107,localhost,127.0.0.1
DATABASE_URL=sqlite:////opt/startlinker/db.sqlite3
CORS_ALLOWED_ORIGINS=http://44.219.216.107,http://localhost:3000
EOF

# Configure Nginx
sudo tee /etc/nginx/conf.d/startlinker.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/startlinker/static/;
    }
    
    location /media/ {
        alias /opt/startlinker/media/;
    }
}
EOF

# Start services
sudo systemctl restart nginx
echo "Basic setup complete!"
echo "Note: You'll need to upload your Django application files separately"