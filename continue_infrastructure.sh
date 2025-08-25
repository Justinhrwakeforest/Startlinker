#!/bin/bash

# Continue AWS Infrastructure Setup
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Use existing resources
REGION="eu-north-1"
PROJECT_NAME="startlinker"
VPC_ID="vpc-028920c6760cf1a99"
SUBNET_ID="subnet-0f61b5a8bd3147d99"
SG_ID="sg-03453d24cd074eaef"

print_status "Continuing infrastructure setup with existing resources..."

# Create S3 Buckets with lowercase names
print_status "Creating S3 buckets..."
STATIC_BUCKET="startlinker-static-files-$(date +%s)"
MEDIA_BUCKET="startlinker-media-files-$(date +%s)"

aws s3 mb s3://$STATIC_BUCKET --region $REGION
aws s3 mb s3://$MEDIA_BUCKET --region $REGION

# Configure static bucket for public access
aws s3api put-public-access-block \
    --bucket $STATIC_BUCKET \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

aws s3api put-bucket-policy \
    --bucket $STATIC_BUCKET \
    --policy "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Sid\": \"PublicReadGetObject\",
                \"Effect\": \"Allow\",
                \"Principal\": \"*\",
                \"Action\": \"s3:GetObject\",
                \"Resource\": \"arn:aws:s3:::$STATIC_BUCKET/*\"
            }
        ]
    }"

print_status "S3 buckets created:"
print_status "  Static: $STATIC_BUCKET"
print_status "  Media: $MEDIA_BUCKET"

# Create RDS Subnet Group
print_status "Creating RDS Subnet Group..."
aws rds create-db-subnet-group \
    --db-subnet-group-name $PROJECT_NAME-subnet-group \
    --db-subnet-group-description "Subnet group for $PROJECT_NAME RDS" \
    --subnet-ids $SUBNET_ID

# Create RDS Instance
print_status "Creating RDS PostgreSQL instance..."
DB_PASSWORD=$(openssl rand -base64 32)

aws rds create-db-instance \
    --db-instance-identifier $PROJECT_NAME-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username $PROJECT_NAME \
    --master-user-password $DB_PASSWORD \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids $SG_ID \
    --db-subnet-group-name $PROJECT_NAME-subnet-group \
    --db-name ${PROJECT_NAME}_db \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "sun:04:00-sun:05:00" \
    --storage-encrypted \
    --tags "Key=Name,Value=$PROJECT_NAME-db"

print_status "RDS instance creation started. This may take several minutes..."

# Create EC2 Instance
print_status "Creating EC2 instance..."

# Get latest Ubuntu AMI
AMI_ID=$(aws ssm get-parameters \
    --names /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
    --region $REGION \
    --query 'Parameters[0].Value' \
    --output text)

# Create key pair
KEY_NAME="$PROJECT_NAME-key"
aws ec2 create-key-pair \
    --key-name $KEY_NAME \
    --query 'KeyMaterial' \
    --output text > $KEY_NAME.pem

chmod 400 $KEY_NAME.pem

# Launch EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type t3.medium \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --subnet-id $SUBNET_ID \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME-server}]" \
    --user-data "#!/bin/bash
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker
" \
    --query 'Instances[0].InstanceId' \
    --output text)

print_status "EC2 instance created: $INSTANCE_ID"

# Wait for instance to be running
print_status "Waiting for EC2 instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

print_status "EC2 instance is running with public IP: $PUBLIC_IP"

# Create configuration file
cat > aws_config.env << EOF
# AWS Infrastructure Configuration
PROJECT_NAME=$PROJECT_NAME
REGION=$REGION
VPC_ID=$VPC_ID
SUBNET_ID=$SUBNET_ID
SECURITY_GROUP_ID=$SG_ID
EC2_INSTANCE_ID=$INSTANCE_ID
EC2_PUBLIC_IP=$PUBLIC_IP
RDS_ENDPOINT=$PROJECT_NAME-db.$REGION.rds.amazonaws.com
S3_STATIC_BUCKET=$STATIC_BUCKET
S3_MEDIA_BUCKET=$MEDIA_BUCKET
DB_PASSWORD=$DB_PASSWORD
SSH_KEY_FILE=$KEY_NAME.pem
EOF

print_status "Configuration saved to aws_config.env"

# Create deployment configuration
cat > .env.production << EOF
# Django Settings
DEBUG=False
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_SETTINGS_MODULE=startup_hub.settings.aws_production

# Database Settings
DB_HOST=$PROJECT_NAME-db.$REGION.rds.amazonaws.com
DB_NAME=${PROJECT_NAME}_db
DB_USER=$PROJECT_NAME
DB_PASSWORD=$DB_PASSWORD

# AWS Settings
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_STORAGE_BUCKET_NAME=$STATIC_BUCKET
AWS_S3_REGION_NAME=$REGION

# Host Settings
ALLOWED_HOSTS=$PUBLIC_IP,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://$PUBLIC_IP,http://localhost:3000

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

print_status "Production environment file created: .env.production"

echo ""
print_status "=== AWS Infrastructure Setup Complete! ==="
echo ""
echo "Resources created:"
echo "  VPC: $VPC_ID"
echo "  Subnet: $SUBNET_ID"
echo "  Security Group: $SG_ID"
echo "  EC2 Instance: $INSTANCE_ID (IP: $PUBLIC_IP)"
echo "  RDS Database: $PROJECT_NAME-db.$REGION.rds.amazonaws.com"
echo "  S3 Static Bucket: $STATIC_BUCKET"
echo "  S3 Media Bucket: $MEDIA_BUCKET"
echo "  SSH Key: $KEY_NAME.pem"
echo ""
echo "Next steps:"
echo "1. Wait for RDS instance to be available (check AWS console)"
echo "2. Run the deployment script: ./deploy_to_aws.sh"
echo "3. Use EC2 IP: $PUBLIC_IP"
echo "4. SSH key file: $KEY_NAME.pem"
echo ""
echo "Important: Keep the SSH key file ($KEY_NAME.pem) secure!"
echo "Database password: $DB_PASSWORD"
echo ""
print_status "Note: RDS instance creation may take 5-10 minutes to complete."
