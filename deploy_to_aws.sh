#!/bin/bash

# AWS Deployment Script for Startup Hub
# This script automates the deployment process to AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EC2_IP=""
EC2_KEY_PATH=""
DOMAIN=""
AWS_REGION="us-east-1"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists aws; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Get user input
get_configuration() {
    echo "=== AWS Deployment Configuration ==="
    
    read -p "Enter your EC2 instance IP: " EC2_IP
    read -p "Enter path to your EC2 key file (.pem): " EC2_KEY_PATH
    read -p "Enter your domain name (or press Enter to skip): " DOMAIN
    read -p "Enter AWS region [us-east-1]: " AWS_REGION
    AWS_REGION=${AWS_REGION:-us-east-1}
    
    # Validate inputs
    if [[ -z "$EC2_IP" ]]; then
        print_error "EC2 IP is required"
        exit 1
    fi
    
    if [[ -z "$EC2_KEY_PATH" ]]; then
        print_error "EC2 key path is required"
        exit 1
    fi
    
    if [[ ! -f "$EC2_KEY_PATH" ]]; then
        print_error "EC2 key file not found: $EC2_KEY_PATH"
        exit 1
    fi
    
    # Set key permissions
    chmod 400 "$EC2_KEY_PATH"
}

# Create environment file
create_env_file() {
    print_status "Creating environment file..."
    
    cat > .env.production << EOF
# Django Settings
DEBUG=False
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_SETTINGS_MODULE=startup_hub.settings.aws_production

# Database Settings
DB_HOST=${DB_HOST:-localhost}
DB_NAME=startlinker_db
DB_USER=startlinker
DB_PASSWORD=${DB_PASSWORD:-your-db-password}

# AWS Settings
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME:-startlinker-static-files}
AWS_S3_REGION_NAME=${AWS_REGION}

# Host Settings
ALLOWED_HOSTS=${DOMAIN:-$EC2_IP},www.${DOMAIN:-$EC2_IP},localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://${DOMAIN:-$EC2_IP},https://www.${DOMAIN:-$EC2_IP},http://localhost:3000

# Email Settings (optional)
EMAIL_HOST=${EMAIL_HOST:-smtp.gmail.com}
EMAIL_PORT=${EMAIL_PORT:-587}
EMAIL_HOST_USER=${EMAIL_HOST_USER}
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}

# Stripe Settings (optional)
STRIPE_PUBLIC_KEY=${STRIPE_PUBLIC_KEY}
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
EOF

    print_status "Environment file created: .env.production"
}

# Build frontend
build_frontend() {
    print_status "Building frontend..."
    
    cd frontend
    
    # Install dependencies
    npm install
    
    # Build for production
    npm run build
    
    cd ..
    
    print_status "Frontend build completed!"
}

# Deploy to EC2
deploy_to_ec2() {
    print_status "Deploying to EC2 instance..."
    
    # Create deployment package
    print_status "Creating deployment package..."
    tar -czf deployment.tar.gz \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        startup_hub/ frontend/ .env.production docker-compose.production.yml
    
    # Upload to EC2
    print_status "Uploading files to EC2..."
    scp -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no deployment.tar.gz ubuntu@"$EC2_IP":/home/ubuntu/
    
    # Execute deployment commands on EC2
    print_status "Executing deployment on EC2..."
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
        cd ../frontend
        sudo cp -r build/* /var/www/html/
        
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
        echo "Your website should be accessible at: http://$EC2_IP"
        if [ ! -z "$DOMAIN" ]; then
            echo "Domain: https://$DOMAIN"
        fi
EOF
    
    # Clean up local files
    rm deployment.tar.gz
    
    print_status "Deployment completed!"
}

# Setup SSL certificate
setup_ssl() {
    if [[ -n "$DOMAIN" ]]; then
        print_status "Setting up SSL certificate for $DOMAIN..."
        
        ssh -i "$EC2_KEY_PATH" -o StrictHostKeyChecking=no ubuntu@"$EC2_IP" << EOF
            sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
            
            # Set up auto-renewal
            (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
EOF
        
        print_status "SSL certificate setup completed!"
    else
        print_warning "No domain provided, skipping SSL setup"
    fi
}

# Main deployment function
main() {
    echo "=== Startup Hub AWS Deployment ==="
    echo ""
    
    check_prerequisites
    get_configuration
    create_env_file
    build_frontend
    deploy_to_ec2
    setup_ssl
    
    echo ""
    print_status "Deployment completed successfully!"
    echo ""
    echo "Your website is now live at:"
    echo "  HTTP:  http://$EC2_IP"
    if [[ -n "$DOMAIN" ]]; then
        echo "  HTTPS: https://$DOMAIN"
    fi
    echo ""
    echo "Next steps:"
    echo "1. Create a Django superuser: ssh -i $EC2_KEY_PATH ubuntu@$EC2_IP"
    echo "2. Access Django admin at: http://$EC2_IP/admin"
    echo "3. Monitor logs: docker-compose -f docker-compose.production.yml logs -f"
    echo "4. Set up monitoring and backups as described in AWS_DEPLOYMENT_GUIDE.md"
}

# Run main function
main "$@"