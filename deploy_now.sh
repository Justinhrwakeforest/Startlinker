#!/bin/bash

# Deploy Startup Hub to AWS
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuration
EC2_IP="13.62.96.192"
EC2_KEY_PATH="startlinker-key.pem"
REGION="eu-north-1"
PROJECT_NAME="startlinker"

print_status "Starting deployment to AWS..."

# Check if key file exists
if [ ! -f "$EC2_KEY_PATH" ]; then
    print_error "SSH key file not found: $EC2_KEY_PATH"
    exit 1
fi

# Set key permissions
chmod 400 "$EC2_KEY_PATH"

# Build frontend
print_status "Building frontend..."
cd ../frontend

# Install dependencies and build
npm install
npm run build

print_status "Frontend build completed!"

# Create deployment package
print_status "Creating deployment package..."
cd ../startup_hub

# Create deployment archive
tar -czf deployment.tar.gz \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    . ../frontend/build .env.production docker-compose.production.yml

# Upload to EC2
print_status "Uploading files to EC2..."
scp -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no deployment.tar.gz ubuntu@"$EC2_IP":/home/ubuntu/

# Execute deployment on EC2
print_status "Deploying on EC2..."
ssh -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no ubuntu@"$EC2_IP" << 'EOF'
    set -e
    
    echo "=== Starting deployment on EC2 ==="
    
    # Update system
    sudo apt update && sudo apt upgrade -y
    
    # Install Docker if not installed
    if ! command -v docker >/dev/null 2>&1; then
        echo "Installing Docker..."
        sudo apt install -y docker.io docker-compose
        sudo usermod -aG docker ubuntu
        sudo systemctl enable docker
        sudo systemctl start docker
    fi
    
    # Install nginx if not installed
    if ! command -v nginx >/dev/null 2>&1; then
        echo "Installing nginx..."
        sudo apt install -y nginx certbot python3-certbot-nginx
    fi
    
    # Extract deployment package
    cd /home/ubuntu
    tar -xzf deployment.tar.gz
    rm deployment.tar.gz
    
    # Set up environment
    source .env.production
    
    # Create necessary directories
    mkdir -p logs media staticfiles
    
    # Build and start backend
    echo "Building and starting backend..."
    cd startup_hub
    docker-compose -f ../docker-compose.production.yml up -d --build
    
    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    sleep 30
    
    # Run migrations
    echo "Running database migrations..."
    docker-compose -f ../docker-compose.production.yml exec -T backend python manage.py migrate --noinput || true
    
    # Collect static files
    echo "Collecting static files..."
    docker-compose -f ../docker-compose.production.yml exec -T backend python manage.py collectstatic --noinput || true
    
    # Deploy frontend
    echo "Deploying frontend..."
    cd ../build
    sudo cp -r * /var/www/html/
    
    # Configure nginx
    echo "Configuring nginx..."
    sudo tee /etc/nginx/sites-available/startlinker > /dev/null << 'NGINX_CONFIG'
server {
    listen 80;
    server_name _;
    
    root /var/www/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # React app routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX_CONFIG
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/startlinker /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    
    # Create health check script
    cat > /home/ubuntu/health_check.sh << 'HEALTH_SCRIPT'
#!/bin/bash
if ! curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "Backend is down, restarting..."
    docker-compose -f /home/ubuntu/docker-compose.production.yml restart backend
fi

if ! curl -f http://localhost > /dev/null 2>&1; then
    echo "Frontend is down, restarting nginx..."
    sudo systemctl restart nginx
fi
HEALTH_SCRIPT
    
    chmod +x /home/ubuntu/health_check.sh
    
    # Add health check to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/health_check.sh") | crontab -
    
    echo "=== Deployment completed successfully! ==="
    echo "Your website should be accessible at: http://13.62.96.192"
EOF

# Clean up local files
rm deployment.tar.gz

print_status "Deployment completed!"
echo ""
echo "🎉 Your Startup Hub website is now live!"
echo ""
echo "🌐 Website URL: http://13.62.96.192"
echo "🔧 Django Admin: http://13.62.96.192/admin"
echo ""
echo "📋 Next steps:"
echo "1. Create a Django superuser:"
echo "   ssh -i startlinker-key.pem ubuntu@13.62.96.192"
echo "   docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser"
echo ""
echo "2. Monitor logs:"
echo "   docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "3. Check health:"
echo "   curl http://13.62.96.192/api/health/"
echo ""
print_status "Deployment successful! 🚀"
