#!/bin/bash
set -e

echo "========================================="
echo "StartLinker EC2 Server Setup"
echo "========================================="

# Read configuration
EC2_IP=$(head -n 1 /tmp/deploy_config.txt)
RDS_ENDPOINT=$(sed -n '2p' /tmp/deploy_config.txt)
STATIC_BUCKET=$(sed -n '3p' /tmp/deploy_config.txt)
MEDIA_BUCKET=$(sed -n '4p' /tmp/deploy_config.txt)

# Extract database host from RDS endpoint
DB_HOST=$(echo $RDS_ENDPOINT | cut -d: -f1)
DB_PORT=5432

echo "Configuration:"
echo "  EC2 IP: $EC2_IP"
echo "  DB Host: $DB_HOST"
echo "  Static Bucket: $STATIC_BUCKET"
echo "  Media Bucket: $MEDIA_BUCKET"

# Update system
echo "Updating system packages..."
sudo yum update -y

# Install required packages
echo "Installing required packages..."
sudo yum install -y \
    python3 python3-pip python3-devel \
    postgresql15 postgresql15-devel \
    nginx git gcc \
    libffi-devel openssl-devel

# Install Node.js for any frontend tools
curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Create application directory
echo "Setting up application directories..."
sudo mkdir -p /opt/startlinker/{backend,frontend,logs}
sudo chown -R ec2-user:ec2-user /opt/startlinker

# Extract backend
echo "Extracting backend application..."
cd /opt/startlinker/backend
tar -xzf /tmp/backend-deploy.tar.gz

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary boto3 django-storages

# Extract frontend
echo "Extracting frontend application..."
cd /opt/startlinker/frontend
tar -xzf /tmp/frontend-deploy.tar.gz

# Create environment file
echo "Creating environment configuration..."
cat > /opt/startlinker/backend/.env << EOF
# Django Settings
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=$EC2_IP,$HOSTNAME,localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://startlinker_admin:$(grep db_password /tmp/terraform.tfvars | cut -d'"' -f2)@$DB_HOST:$DB_PORT/startlinker_db

# AWS Settings
AWS_STORAGE_BUCKET_NAME=$STATIC_BUCKET
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=$STATIC_BUCKET.s3.amazonaws.com
AWS_DEFAULT_ACL=public-read

# CORS
CORS_ALLOWED_ORIGINS=http://$EC2_IP,http://localhost:3000
CORS_ALLOW_CREDENTIALS=True

# Security
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
EOF

# Update Django settings for production
echo "Configuring Django settings..."
cd /opt/startlinker/backend

# Run Django migrations
echo "Running database migrations..."
source venv/bin/activate
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser
echo "Creating admin user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@startlinker.com').exists():
    User.objects.create_superuser(
        email='admin@startlinker.com',
        username='admin',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User'
    )
    print("Admin user created successfully")
else:
    print("Admin user already exists")
EOF

# Create Gunicorn service
echo "Creating Gunicorn service..."
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << EOF
[Unit]
Description=StartLinker Gunicorn Service
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/startlinker/backend
Environment="PATH=/opt/startlinker/backend/venv/bin"
ExecStart=/opt/startlinker/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --error-logfile /opt/startlinker/logs/gunicorn-error.log \
    --access-logfile /opt/startlinker/logs/gunicorn-access.log \
    startup_hub.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/conf.d/startlinker.conf > /dev/null << 'EOF'
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 100M;

    # Frontend React App
    location / {
        root /opt/startlinker/frontend/build;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # Django API
    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/startlinker/backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/startlinker/backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Remove default Nginx config
sudo rm -f /etc/nginx/conf.d/default.conf

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl enable nginx
sudo systemctl restart nginx

# Create a health check script
cat > /opt/startlinker/health_check.sh << 'EOF'
#!/bin/bash
echo "========================================="
echo "StartLinker Health Check"
echo "========================================="
echo ""

# Check Gunicorn
if systemctl is-active --quiet gunicorn; then
    echo "✅ Gunicorn: Running"
else
    echo "❌ Gunicorn: Not running"
    systemctl status gunicorn --no-pager | head -10
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: Running"
else
    echo "❌ Nginx: Not running"
    systemctl status nginx --no-pager | head -10
fi

# Check API endpoint
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/ | grep -q "200\|301\|302"; then
    echo "✅ API: Responding"
else
    echo "❌ API: Not responding"
fi

# Check database connection
cd /opt/startlinker/backend
source venv/bin/activate
python -c "from django.db import connection; cursor = connection.cursor(); print('✅ Database: Connected')" 2>/dev/null || echo "❌ Database: Connection failed"

echo ""
echo "Logs:"
echo "  Gunicorn: /opt/startlinker/logs/gunicorn-*.log"
echo "  Nginx: /var/log/nginx/*.log"
echo "========================================="
EOF

chmod +x /opt/startlinker/health_check.sh

# Run health check
echo ""
echo "Running health check..."
/opt/startlinker/health_check.sh

echo ""
echo "========================================="
echo "Server setup complete!"
echo "========================================="
echo ""
echo "Application URL: http://$EC2_IP"
echo "Admin Panel: http://$EC2_IP/admin/"
echo ""
echo "To check service status:"
echo "  sudo systemctl status gunicorn"
echo "  sudo systemctl status nginx"
echo ""
echo "To view logs:"
echo "  tail -f /opt/startlinker/logs/gunicorn-*.log"
echo "  sudo tail -f /var/log/nginx/*.log"
echo "========================================="