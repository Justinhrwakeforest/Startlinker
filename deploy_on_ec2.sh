#!/bin/bash
# EC2 deployment script - runs on the EC2 instance

echo "Starting deployment on EC2..."

# Create directories
sudo mkdir -p /opt/startlinker/{backend,frontend}
sudo chown -R ec2-user:ec2-user /opt/startlinker

# Extract backend
cd /opt/startlinker/backend
tar -xzf /tmp/backend.tar.gz

# Install Python and dependencies
sudo yum install -y python3 python3-pip python3-devel postgresql-devel gcc
pip3 install --user -r requirements.txt

# Setup environment variables
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=$HOSTNAME,$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
DATABASE_URL=sqlite:////opt/startlinker/backend/db.sqlite3
CORS_ALLOWED_ORIGINS=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
EOF

# Run migrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput

# Create superuser (optional)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@startlinker.com').exists() or User.objects.create_superuser('admin@startlinker.com', 'admin', 'AdminPass123!')" | python3 manage.py shell

# Setup frontend
cd /opt/startlinker/frontend
tar -xzf /tmp/frontend.tar.gz

# Configure Nginx
sudo tee /etc/nginx/conf.d/startlinker.conf << EOF
server {
    listen 80;
    server_name _;
    
    # Frontend
    location / {
        root /opt/startlinker/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Static files
    location /static/ {
        alias /opt/startlinker/backend/static/;
    }
    
    # Media files
    location /media/ {
        alias /opt/startlinker/backend/media/;
    }
}
EOF

# Start services
sudo systemctl restart nginx

# Create systemd service for Django
sudo tee /etc/systemd/system/startlinker.service << EOF
[Unit]
Description=StartLinker Django Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/startlinker/backend
ExecStart=/usr/bin/python3 manage.py runserver 0.0.0.0:8000
Restart=always
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable startlinker
sudo systemctl start startlinker

echo "Deployment complete!"
echo "Services started:"
echo "- Nginx: $(sudo systemctl is-active nginx)"
echo "- Django: $(sudo systemctl is-active startlinker)"