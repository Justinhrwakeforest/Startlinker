#!/usr/bin/env python3
"""
Deploy with AWS CLI - Secure Method
"""

import os
import subprocess
import time

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AWS credentials configured successfully!")
            print(f"Account: {result.stdout}")
            return True
        else:
            print("❌ AWS credentials not configured or invalid")
            return False
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False

def configure_aws():
    """Guide user through AWS configuration"""
    print("\n🔐 AWS Configuration Required")
    print("=" * 40)
    print("Please configure AWS CLI with your credentials:")
    print()
    print("Run this command:")
    print("aws configure")
    print()
    print("When prompted, enter:")
    print("- AWS Access Key ID: AKIASFTGWXHCZPFBTO4M")
    print("- AWS Secret Access Key: [Your secret key]")
    print("- Default region: us-east-1")
    print("- Default output format: json")
    print()

def deploy_to_aws():
    """Deploy using AWS CLI"""
    print("\n🚀 Deploying to AWS...")
    print("=" * 40)
    
    # Use the correct instance ID
    instance_id = "i-0dd546be42c21eb62"
    print(f"📦 Using instance: {instance_id}")
    
    try:
        # Deploy using AWS Systems Manager
        print("🚀 Starting deployment...")
        deploy_commands = [
            "cd /var/www/startlinker",
            "sudo systemctl stop gunicorn",
            "sudo systemctl stop nginx",
            "sudo git pull origin main || echo 'Git pull failed, continuing...'",
            "sudo pip3 install -r requirements.txt",
            "sudo python3 manage.py migrate --noinput",
            "sudo python3 manage.py collectstatic --noinput",
            "sudo systemctl start gunicorn",
            "sudo systemctl start nginx",
            "echo 'Deployment complete!'"
        ]
        
        ssm_command = [
            'aws', 'ssm', 'send-command',
            '--instance-ids', instance_id,
            '--document-name', 'AWS-RunShellScript',
            '--parameters', f'commands={deploy_commands}'
        ]
        
        result = subprocess.run(ssm_command, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Deployment command sent successfully!")
            print("Check AWS Console for deployment status")
            print(f"🌐 Your site should be available at: http://13.62.96.192/")
        else:
            print(f"❌ Deployment failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error during deployment: {e}")

def main():
    print("🚀 AWS CLI Deployment")
    print("=" * 40)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check AWS credentials
    if not check_aws_credentials():
        configure_aws()
        print("Please configure AWS CLI and run this script again")
        return
    
    # Deploy
    deploy_to_aws()

if __name__ == "__main__":
    main()
