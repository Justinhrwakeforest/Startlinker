#!/usr/bin/env python3
"""
Secure AWS Deployment Setup
This script helps you configure AWS CLI and deploy securely
"""

import os
import subprocess
import sys
import time

def check_aws_cli():
    """Check if AWS CLI is installed"""
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ AWS CLI found: {result.stdout.strip()}")
            return True
        else:
            print("❌ AWS CLI not found or not working")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        return False

def configure_aws_credentials():
    """Guide user through AWS credentials configuration"""
    print("\n🔐 AWS Credentials Configuration")
    print("=" * 50)
    print("To configure AWS CLI securely, run these commands:")
    print()
    print("1. Configure AWS CLI:")
    print("   aws configure")
    print()
    print("2. Enter your credentials when prompted:")
    print("   - AWS Access Key ID: [Your access key]")
    print("   - AWS Secret Access Key: [Your secret key]")
    print("   - Default region name: us-east-1")
    print("   - Default output format: json")
    print()
    print("3. Test your configuration:")
    print("   aws sts get-caller-identity")
    print()

def create_secure_deployment_script():
    """Create a secure deployment script"""
    script_content = '''#!/bin/bash
# Secure AWS Deployment Script
# This script uses AWS CLI for secure deployment

set -e

echo "🚀 Starting secure AWS deployment..."

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity

# Get EC2 instance details
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=ip-address,Values=44.219.216.107" --query "Reservations[0].Instances[0].InstanceId" --output text)
echo "📦 Found instance: $INSTANCE_ID"

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf deployment.tar.gz --exclude='node_modules' --exclude='.git' --exclude='venv' .

# Upload to S3 (if you have S3 bucket)
# aws s3 cp deployment.tar.gz s3://your-bucket/deployment.tar.gz

# Use AWS Systems Manager to run commands on EC2
echo "🚀 Deploying to EC2..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "cd /var/www/startlinker",
        "sudo systemctl stop gunicorn",
        "sudo systemctl stop nginx",
        "sudo tar -xzf /tmp/deployment.tar.gz",
        "sudo pip3 install -r requirements.txt",
        "sudo python3 manage.py migrate --noinput",
        "sudo python3 manage.py collectstatic --noinput",
        "sudo systemctl start gunicorn",
        "sudo systemctl start nginx",
        "echo \"Deployment complete!\""]'

echo "✅ Deployment initiated successfully!"
'''
    
    with open('secure_deploy.sh', 'w') as f:
        f.write(script_content)
    
    print("✅ Created secure deployment script: secure_deploy.sh")

def main():
    print("🔐 Secure AWS Deployment Setup")
    print("=" * 50)
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check AWS CLI
    if not check_aws_cli():
        print("\n📥 To install AWS CLI:")
        print("   Windows: Download from https://aws.amazon.com/cli/")
        print("   Or run: pip install awscli")
        return
    
    # Configure credentials
    configure_aws_credentials()
    
    # Create deployment script
    create_secure_deployment_script()
    
    print("\n📋 Next Steps:")
    print("1. Configure AWS CLI with your credentials")
    print("2. Test with: aws sts get-caller-identity")
    print("3. Run: ./secure_deploy.sh")
    print()
    print("🔒 Your credentials will be stored securely in ~/.aws/credentials")

if __name__ == "__main__":
    main()
