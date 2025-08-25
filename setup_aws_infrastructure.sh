#!/bin/bash

# AWS Infrastructure Setup Script for Startup Hub
# This script creates the necessary AWS resources for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_NAME="startlinker"
REGION="eu-north-1"
VPC_CIDR="10.0.0.0/16"
SUBNET_CIDR="10.0.1.0/24"

# Get user input
echo "=== AWS Infrastructure Setup ==="
echo ""

read -p "Enter your AWS region [$REGION]: " input_region
REGION=${input_region:-$REGION}

read -p "Enter your project name [$PROJECT_NAME]: " input_project
PROJECT_NAME=${input_project:-$PROJECT_NAME}

read -p "Enter your domain name (optional): " DOMAIN

echo ""
print_status "Setting up AWS infrastructure for $PROJECT_NAME in $REGION..."

# Check AWS CLI and credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Create VPC
print_status "Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block $VPC_CIDR \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$PROJECT_NAME-vpc}]" \
    --query 'Vpc.VpcId' \
    --output text)

print_status "VPC created: $VPC_ID"

# Create Internet Gateway
print_status "Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=$PROJECT_NAME-igw}]" \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway \
    --vpc-id $VPC_ID \
    --internet-gateway-id $IGW_ID

print_status "Internet Gateway created and attached: $IGW_ID"

# Create Subnet
print_status "Creating Subnet..."
SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $SUBNET_CIDR \
    --availability-zone ${REGION}a \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT_NAME-subnet}]" \
    --query 'Subnet.SubnetId' \
    --output text)

print_status "Subnet created: $SUBNET_ID"

# Create Route Table
print_status "Creating Route Table..."
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PROJECT_NAME-rt}]" \
    --query 'RouteTable.RouteTableId' \
    --output text)

aws ec2 create-route \
    --route-table-id $ROUTE_TABLE_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID

aws ec2 associate-route-table \
    --subnet-id $SUBNET_ID \
    --route-table-id $ROUTE_TABLE_ID

print_status "Route Table created and configured: $ROUTE_TABLE_ID"

# Create Security Group
print_status "Creating Security Group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name $PROJECT_NAME-sg \
    --description "Security group for $PROJECT_NAME" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# Add security group rules
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

print_status "Security Group created: $SG_ID"

# Create S3 Buckets
print_status "Creating S3 buckets..."
STATIC_BUCKET="$(echo $PROJECT_NAME | tr '[:upper:]' '[:lower:]')-static-files-$(date +%s)"
MEDIA_BUCKET="$(echo $PROJECT_NAME | tr '[:upper:]' '[:lower:]')-media-files-$(date +%s)"

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
ALLOWED_HOSTS=$PUBLIC_IP${DOMAIN:+,$DOMAIN,www.$DOMAIN},localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://$PUBLIC_IP${DOMAIN:+,https://$DOMAIN,https://www.$DOMAIN},http://localhost:3000

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
print_warning "Note: RDS instance creation may take 5-10 minutes to complete."
