# AWS Deployment Guide for Startup Hub

## Overview
This guide will help you deploy your Startup Hub website (Django + React) to AWS using:
- **EC2** for hosting
- **RDS** for PostgreSQL database
- **S3** for static/media files
- **CloudFront** for CDN (optional)
- **Route 53** for domain management (optional)

## Prerequisites
1. AWS Account with appropriate permissions
2. Domain name (optional but recommended)
3. AWS CLI installed and configured
4. Docker and Docker Compose installed locally

## Step 1: AWS Infrastructure Setup

### 1.1 Create RDS Database
```bash
# Create PostgreSQL RDS instance
aws rds create-db-instance \
    --db-instance-identifier startlinker-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username startlinker \
    --master-user-password YOUR_SECURE_PASSWORD \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-name startlinker_db
```

### 1.2 Create S3 Bucket
```bash
# Create S3 bucket for static files
aws s3 mb s3://startlinker-static-files
aws s3 mb s3://startlinker-media-files

# Enable public access for static files
aws s3api put-public-access-block \
    --bucket startlinker-static-files \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

### 1.3 Create EC2 Instance
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=startlinker-server}]'
```

## Step 2: Server Configuration

### 2.1 Connect to EC2 and Install Dependencies
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# Install additional dependencies
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 2.2 Clone and Configure Project
```bash
# Clone your repository
git clone https://github.com/yourusername/startup_hub.git
cd startup_hub

# Create environment file
cat > .env.production << EOF
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DB_HOST=your-rds-endpoint.amazonaws.com
DB_NAME=startlinker_db
DB_USER=startlinker
DB_PASSWORD=your-db-password
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=startlinker-static-files
USE_S3=True
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-ec2-ip
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
EOF
```

## Step 3: Frontend Deployment

### 3.1 Build and Deploy Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies and build
npm install
npm run build

# Create production nginx config
cat > nginx.production.conf << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    root /usr/share/nginx/html;
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
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Deploy to nginx
sudo cp -r build/* /var/www/html/
sudo cp nginx.production.conf /etc/nginx/sites-available/startlinker
sudo ln -s /etc/nginx/sites-available/startlinker /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Step 4: Backend Deployment

### 4.1 Configure Django for Production
```bash
# Navigate back to project root
cd ..

# Create production docker-compose
cat > docker-compose.production.yml << EOF
version: '3.8'

services:
  backend:
    build: .
    container_name: startlinker_backend
    environment:
      - DJANGO_SETTINGS_MODULE=startup_hub.settings.aws_production
      - DEBUG=False
      - SECRET_KEY=\${SECRET_KEY}
      - DB_HOST=\${DB_HOST}
      - DB_NAME=\${DB_NAME}
      - DB_USER=\${DB_USER}
      - DB_PASSWORD=\${DB_PASSWORD}
      - AWS_ACCESS_KEY_ID=\${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=\${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=\${AWS_STORAGE_BUCKET_NAME}
      - ALLOWED_HOSTS=\${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=\${CORS_ALLOWED_ORIGINS}
    volumes:
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    networks:
      - startlinker_network
    restart: unless-stopped

networks:
  startlinker_network:
    driver: bridge
EOF

# Build and start services
docker-compose -f docker-compose.production.yml up -d --build
```

## Step 5: SSL Certificate (Optional but Recommended)

### 5.1 Install SSL Certificate
```bash
# Install SSL certificate using Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up auto-renewal
sudo crontab -e
# Add this line: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Step 6: Monitoring and Maintenance

### 6.1 Set up Logging
```bash
# Create log directory
sudo mkdir -p /var/log/startlinker
sudo chown ubuntu:ubuntu /var/log/startlinker

# Configure log rotation
sudo tee /etc/logrotate.d/startlinker << EOF
/var/log/startlinker/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
EOF
```

### 6.2 Set up Monitoring
```bash
# Install basic monitoring tools
sudo apt install -y htop iotop nethogs

# Create health check script
cat > /home/ubuntu/health_check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "Backend is down, restarting..."
    docker-compose -f /home/ubuntu/startup_hub/docker-compose.production.yml restart backend
fi

if ! curl -f http://localhost > /dev/null 2>&1; then
    echo "Frontend is down, restarting nginx..."
    sudo systemctl restart nginx
fi
EOF

chmod +x /home/ubuntu/health_check.sh

# Add to crontab for regular health checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/health_check.sh") | crontab -
```

## Step 7: Backup Strategy

### 7.1 Database Backups
```bash
# Create backup script
cat > /home/ubuntu/backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup_db.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup_db.sh") | crontab -
```

## Step 8: Performance Optimization

### 8.1 Enable CloudFront (Optional)
```bash
# Create CloudFront distribution for S3 bucket
aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json
```

### 8.2 Configure Redis for Caching
```bash
# Add Redis to docker-compose
# Update docker-compose.production.yml to include Redis service
```

## Troubleshooting

### Common Issues:
1. **Database Connection**: Check security groups and network ACLs
2. **Static Files**: Verify S3 bucket permissions and CORS settings
3. **CORS Errors**: Ensure CORS_ALLOWED_ORIGINS includes your domain
4. **SSL Issues**: Check certificate installation and nginx configuration

### Useful Commands:
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps
sudo systemctl status nginx

# View logs
docker-compose -f docker-compose.production.yml logs backend
sudo tail -f /var/log/nginx/error.log

# Restart services
docker-compose -f docker-compose.production.yml restart
sudo systemctl restart nginx
```

## Security Checklist

- [ ] Change default database password
- [ ] Use strong Django secret key
- [ ] Configure firewall rules
- [ ] Enable HTTPS
- [ ] Set up regular backups
- [ ] Monitor access logs
- [ ] Keep system packages updated
- [ ] Use IAM roles instead of access keys where possible

## Cost Optimization

- Use t3.micro for development/testing
- Enable S3 lifecycle policies for old files
- Use RDS reserved instances for production
- Monitor CloudWatch metrics
- Set up billing alerts

Your website should now be live on AWS! The deployment includes both the Django backend API and React frontend, with proper SSL, monitoring, and backup strategies in place.