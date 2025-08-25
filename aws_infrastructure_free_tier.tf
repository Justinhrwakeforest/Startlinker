# StartLinker AWS Infrastructure Configuration - FREE TIER VERSION
# This Terraform configuration sets up infrastructure using only AWS Free Tier eligible resources
# Note: Free tier includes 12-month free tier services and always-free services

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  # For free tier, we'll use local state instead of S3 to avoid costs
  # Uncomment below to use S3 backend (S3 is free but DynamoDB for locking may incur costs)
  # backend "s3" {
  #   bucket = "startlinker-terraform-state"
  #   key    = "infrastructure/terraform.tfstate"
  #   region = "us-east-1"
  #   encrypt = true
  # }
}

# Variables
variable "project_name" {
  description = "Project name"
  default     = "startlinker"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Single availability zone for free tier"
  default     = "us-east-1a"
}

variable "db_username" {
  description = "Database username"
  default     = "startlinker"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django secret key"
  sensitive   = true
}

variable "enable_free_tier_only" {
  description = "Enable only free tier resources"
  default     = true
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "domain_name" {
  description = "Domain name for the application"
  default     = "startlinker.com"
}

# Provider Configuration
provider "aws" {
  region = var.region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      FreeTier    = "true"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

# Get latest Amazon Linux 2 AMI (free tier eligible)
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Random resources for unique naming
resource "random_id" "suffix" {
  byte_length = 4
}

# VPC Configuration (VPC is free)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.project_name}-vpc-${var.environment}-free"
  }
}

# Internet Gateway (free)
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${var.project_name}-igw-${var.environment}-free"
  }
}

# Single Public Subnet (free)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.project_name}-public-subnet-${var.environment}-free"
    Type = "Public"
  }
}

# Private Subnet 1 (free, but no NAT Gateway)
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = var.availability_zone
  
  tags = {
    Name = "${var.project_name}-private-subnet-${var.environment}-free"
    Type = "Private"
  }
}

# Private Subnet 2 (required for RDS subnet group)
resource "aws_subnet" "private2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "us-east-1b"
  
  tags = {
    Name = "${var.project_name}-private-subnet2-${var.environment}-free"
    Type = "Private"
  }
}

# Route Table for Public Subnet (free)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "${var.project_name}-public-rt-${var.environment}-free"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Groups (free)
resource "aws_security_group" "web" {
  name_prefix = "startlinker-web-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for StartLinker web server"
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict this in production
    description = "SSH"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  tags = {
    Name = "${var.project_name}-web-sg-${var.environment}-free"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "startlinker-rds-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for StartLinker RDS database"
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
    description     = "PostgreSQL from web servers"
  }
  
  tags = {
    Name = "${var.project_name}-rds-sg-${var.environment}-free"
  }
}

# EC2 Key Pair (create locally and upload public key)
resource "aws_key_pair" "main" {
  key_name   = "${var.project_name}-key-${var.environment}"
  public_key = file("./startlinker-key.pub")
  
  tags = {
    Name = "${var.project_name}-key-${var.environment}-free"
  }
}

# EC2 Instance (t2.micro - 750 hours/month free)
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t2.micro"  # Free tier eligible
  key_name      = aws_key_pair.main.key_name
  
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  associate_public_ip_address = true
  
  # Free tier includes 30 GB of General Purpose (SSD) or Magnetic storage
  root_block_device {
    volume_type = "gp2"
    volume_size = 30  # Free tier limit
    encrypted   = true
  }
  
  user_data = <<-EOF
    #!/bin/bash
    # Update system
    yum update -y
    
    # Install Docker
    amazon-linux-extras install docker -y
    service docker start
    usermod -a -G docker ec2-user
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Install nginx
    amazon-linux-extras install nginx1 -y
    
    # Install Redis (local replacement for ElastiCache)
    amazon-linux-extras install redis6 -y
    systemctl start redis
    systemctl enable redis
    
    # Install git
    yum install git -y
    
    # Create app directory
    mkdir -p /opt/startlinker
    chown ec2-user:ec2-user /opt/startlinker
  EOF
  
  tags = {
    Name = "${var.project_name}-web-${var.environment}-free"
  }
}

# Elastic IP for EC2 (1 free EIP when attached to running instance)
resource "aws_eip" "web" {
  instance = aws_instance.web.id
  domain   = "vpc"
  
  tags = {
    Name = "${var.project_name}-eip-${var.environment}-free"
  }
}

# RDS Subnet Group (required for RDS, free)
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group-${var.environment}-free"
  subnet_ids = [aws_subnet.private.id, aws_subnet.private2.id]
  
  tags = {
    Name = "${var.project_name}-db-subnet-group-${var.environment}-free"
  }
}

# RDS PostgreSQL Instance (db.t2.micro - 750 hours/month free)
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db-${var.environment}-free"
  
  engine         = "postgres"
  engine_version = "13.16"  # Use a stable version
  instance_class = "db.t3.micro"  # Free tier eligible
  
  allocated_storage     = 20  # Free tier includes 20 GB
  storage_type          = "gp2"
  storage_encrypted     = false  # Encryption not available on t2.micro
  
  db_name  = "startlinker_db"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  # Free tier considerations
  backup_retention_period = 7  # Free automated backups
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Single AZ for free tier
  multi_az = false
  
  # Free tier protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.project_name}-db-final-snapshot-${random_id.suffix.hex}"
  
  # No performance insights on free tier
  enabled_cloudwatch_logs_exports = []
  
  tags = {
    Name = "${var.project_name}-db-${var.environment}-free"
  }
}

# S3 Buckets (5 GB free for 12 months, then pay as you go)
resource "aws_s3_bucket" "static" {
  bucket = "startlinker-static-${var.environment}-free-${random_id.suffix.hex}"
  
  tags = {
    Name = "startlinker-static-${var.environment}-free"
    Project = "StartLinker"
  }
}

resource "aws_s3_bucket" "media" {
  bucket = "startlinker-media-${var.environment}-free-${random_id.suffix.hex}"
  
  tags = {
    Name = "startlinker-media-${var.environment}-free"
    Project = "StartLinker"
  }
}

# S3 Bucket Versioning (optional, may incur additional storage costs)
resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id
  versioning_configuration {
    status = "Disabled"  # Disabled to minimize storage costs
  }
}

# S3 Bucket Public Access Settings
resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id
  
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Policy for Static Files
resource "aws_s3_bucket_policy" "static" {
  bucket = aws_s3_bucket.static.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.static.arn}/*"
      }
    ]
  })
  
  depends_on = [aws_s3_bucket_public_access_block.static]
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# CloudWatch Log Group (free tier includes 5GB ingestion and 5GB storage)
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/ec2/startlinker/${var.environment}"
  retention_in_days = 7  # Minimize retention to stay within free tier
  
  tags = {
    Name = "startlinker-logs-${var.environment}-free"
    Project = "StartLinker"
  }
}

# IAM Role for EC2
resource "aws_iam_role" "ec2" {
  name = "startlinker-ec2-role-${var.environment}-free"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role Policy for S3 Access
resource "aws_iam_role_policy" "ec2_s3" {
  name = "startlinker-ec2-s3-policy-${var.environment}-free"
  role = aws_iam_role.ec2.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.media.arn}/*",
          "${aws_s3_bucket.static.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.media.arn,
          aws_s3_bucket.static.arn
        ]
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2" {
  name = "startlinker-ec2-profile-${var.environment}-free"
  role = aws_iam_role.ec2.name
}

# Attach instance profile to EC2
resource "aws_instance" "web_with_profile" {
  ami                    = aws_instance.web.ami
  instance_type          = aws_instance.web.instance_type
  key_name              = aws_instance.web.key_name
  subnet_id             = aws_instance.web.subnet_id
  vpc_security_group_ids = aws_instance.web.vpc_security_group_ids
  iam_instance_profile  = aws_iam_instance_profile.ec2.name
  
  lifecycle {
    ignore_changes = [ami, user_data]
  }
  
  depends_on = [aws_instance.web]
}

# Outputs
output "ec2_public_ip" {
  value       = aws_eip.web.public_ip
  description = "Public IP address of the EC2 instance"
}

output "ec2_public_dns" {
  value       = aws_instance.web.public_dns
  description = "Public DNS of the EC2 instance"
}

output "rds_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "RDS instance endpoint"
}

output "rds_port" {
  value       = aws_db_instance.main.port
  description = "RDS instance port"
}

output "static_bucket_name" {
  value       = aws_s3_bucket.static.id
  description = "Static files S3 bucket name"
}

output "static_bucket_url" {
  value       = "https://${aws_s3_bucket.static.bucket_regional_domain_name}"
  description = "Static files S3 bucket URL"
}

output "media_bucket_name" {
  value       = aws_s3_bucket.media.id
  description = "Media files S3 bucket name"
}

output "redis_endpoint" {
  value       = "localhost"
  description = "Redis endpoint (local on EC2)"
}

output "free_tier_notes" {
  value = <<-EOT
    FREE TIER DEPLOYMENT NOTES:
    - EC2: t2.micro instance (750 hours/month for 12 months)
    - RDS: db.t2.micro PostgreSQL (750 hours/month for 12 months)
    - S3: 5GB storage, 20,000 GET requests, 2,000 PUT requests (12 months)
    - Data Transfer: 15 GB/month (always free)
    - Redis: Running locally on EC2 (no ElastiCache)
    - No NAT Gateway, ELB, or CloudFront to avoid costs
    - Single AZ deployment (no high availability)
    
    LIMITATIONS:
    - No auto-scaling
    - No load balancing
    - Limited redundancy
    - Manual SSL certificate management required
    
    MONITOR USAGE:
    - Check AWS Free Tier usage dashboard regularly
    - Set up billing alerts
    - Consider upgrading after 12 months or if usage exceeds limits
  EOT
}