#!/usr/bin/env python3
"""
AWS EC2 Instance Launch Script for StartLinker
This script creates a new EC2 instance optimized for hosting the StartLinker application
"""

import boto3
import time
import json
from botocore.exceptions import ClientError

# AWS Configuration
AWS_REGION = 'eu-north-1'  # Stockholm region (closest to your setup)
INSTANCE_TYPE = 't3.medium'  # Good balance of performance and cost
AMI_ID = 'ami-0014ce3e52359afbd'  # Ubuntu 22.04 LTS in eu-north-1
KEY_PAIR_NAME = 'startlinker-key'
SECURITY_GROUP_NAME = 'startlinker-sg'

def create_security_group(ec2_client):
    """Create security group with required ports"""
    try:
        # Check if security group already exists
        response = ec2_client.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': [SECURITY_GROUP_NAME]}]
        )
        
        if response['SecurityGroups']:
            sg_id = response['SecurityGroups'][0]['GroupId']
            print(f"✓ Security group '{SECURITY_GROUP_NAME}' already exists: {sg_id}")
            return sg_id
        
        # Create new security group
        response = ec2_client.create_security_group(
            GroupName=SECURITY_GROUP_NAME,
            Description='Security group for StartLinker application'
        )
        
        sg_id = response['GroupId']
        print(f"✓ Created security group: {sg_id}")
        
        # Add inbound rules
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS access'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Django backend'}]
                }
            ]
        )
        
        print("✓ Security group rules configured")
        return sg_id
        
    except ClientError as e:
        print(f"✗ Error creating security group: {e}")
        return None

def create_key_pair(ec2_client):
    """Create or check SSH key pair"""
    try:
        # Check if key pair exists
        response = ec2_client.describe_key_pairs(KeyNames=[KEY_PAIR_NAME])
        print(f"✓ Key pair '{KEY_PAIR_NAME}' already exists")
        return True
        
    except ClientError as e:
        if 'InvalidKeyPair.NotFound' in str(e):
            # Create new key pair
            try:
                response = ec2_client.create_key_pair(KeyName=KEY_PAIR_NAME)
                
                # Save private key to file
                private_key = response['KeyMaterial']
                key_file_path = f"{KEY_PAIR_NAME}.pem"
                
                with open(key_file_path, 'w') as f:
                    f.write(private_key)
                
                # Set correct permissions (Unix-like systems)
                import os, stat
                os.chmod(key_file_path, stat.S_IRUSR | stat.S_IWUSR)
                
                print(f"✓ Created new key pair: {KEY_PAIR_NAME}")
                print(f"✓ Private key saved to: {key_file_path}")
                print(f"  IMPORTANT: Move this file to ~/.ssh/ directory")
                return True
                
            except ClientError as create_error:
                print(f"✗ Error creating key pair: {create_error}")
                return False
        else:
            print(f"✗ Error checking key pair: {e}")
            return False

def launch_instance(ec2_client, security_group_id):
    """Launch EC2 instance"""
    
    # User data script to setup the instance
    user_data_script = """#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install basic dependencies
apt-get install -y curl wget git htop unzip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Nginx and Certbot
apt-get install -y nginx certbot python3-certbot-nginx

# Setup directories
mkdir -p /opt/startup_hub
mkdir -p /opt/frontend
chown -R ubuntu:ubuntu /opt/startup_hub
chown -R ubuntu:ubuntu /opt/frontend

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo 'y' | ufw enable

# Start and enable services
systemctl enable docker
systemctl start docker
systemctl enable nginx
systemctl start nginx

# Create a simple index page
echo '<h1>StartLinker Server Ready</h1><p>Server is ready for deployment.</p>' > /var/www/html/index.html

echo "Setup completed successfully" > /var/log/setup.log
"""
    
    try:
        response = ec2_client.run_instances(
            ImageId=AMI_ID,
            MinCount=1,
            MaxCount=1,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_PAIR_NAME,
            SecurityGroupIds=[security_group_id],
            UserData=user_data_script,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'startlinker-web-server'},
                        {'Key': 'Project', 'Value': 'StartLinker'},
                        {'Key': 'Environment', 'Value': 'Production'}
                    ]
                }
            ],
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'VolumeSize': 20,  # 20GB storage
                        'VolumeType': 'gp3',
                        'DeleteOnTermination': True
                    }
                }
            ]
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"✓ Launched EC2 instance: {instance_id}")
        
        return instance_id
        
    except ClientError as e:
        print(f"✗ Error launching instance: {e}")
        return None

def wait_for_instance(ec2_client, instance_id):
    """Wait for instance to be running and get IP address"""
    print("⏳ Waiting for instance to start...")
    
    waiter = ec2_client.get_waiter('instance_running')
    
    try:
        waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
        
        # Get instance details
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        public_ip = instance.get('PublicIpAddress')
        private_ip = instance.get('PrivateIpAddress')
        
        print(f"✓ Instance is running!")
        print(f"  Instance ID: {instance_id}")
        print(f"  Public IP: {public_ip}")
        print(f"  Private IP: {private_ip}")
        
        return public_ip
        
    except Exception as e:
        print(f"✗ Error waiting for instance: {e}")
        return None

def create_elastic_ip(ec2_client, instance_id):
    """Create and associate Elastic IP"""
    try:
        # Allocate Elastic IP
        response = ec2_client.allocate_address(Domain='vpc')
        allocation_id = response['AllocationId']
        elastic_ip = response['PublicIp']
        
        print(f"✓ Allocated Elastic IP: {elastic_ip}")
        
        # Associate with instance
        ec2_client.associate_address(
            InstanceId=instance_id,
            AllocationId=allocation_id
        )
        
        print(f"✓ Associated Elastic IP with instance")
        return elastic_ip
        
    except ClientError as e:
        print(f"✗ Error creating Elastic IP: {e}")
        return None

def main():
    """Main execution function"""
    print("🚀 Starting AWS EC2 Instance Launch for StartLinker")
    print("=" * 50)
    
    try:
        # Initialize EC2 client
        ec2_client = boto3.client('ec2', region_name=AWS_REGION)
        print(f"✓ Connected to AWS region: {AWS_REGION}")
        
        # Step 1: Create/check key pair
        print("\n📋 Step 1: Setting up SSH key pair...")
        if not create_key_pair(ec2_client):
            return
        
        # Step 2: Create/check security group
        print("\n🔒 Step 2: Setting up security group...")
        security_group_id = create_security_group(ec2_client)
        if not security_group_id:
            return
        
        # Step 3: Launch instance
        print("\n🖥️  Step 3: Launching EC2 instance...")
        instance_id = launch_instance(ec2_client, security_group_id)
        if not instance_id:
            return
        
        # Step 4: Wait for instance to start
        print("\n⏳ Step 4: Waiting for instance to start...")
        public_ip = wait_for_instance(ec2_client, instance_id)
        if not public_ip:
            return
        
        # Step 5: Create Elastic IP (optional)
        print("\n🌐 Step 5: Setting up Elastic IP...")
        elastic_ip = create_elastic_ip(ec2_client, instance_id)
        final_ip = elastic_ip if elastic_ip else public_ip
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 EC2 Instance Successfully Launched!")
        print("=" * 50)
        print(f"Instance ID: {instance_id}")
        print(f"Public IP: {final_ip}")
        print(f"Region: {AWS_REGION}")
        print(f"Instance Type: {INSTANCE_TYPE}")
        print(f"Key Pair: {KEY_PAIR_NAME}")
        
        print("\n📝 Next Steps:")
        print("1. Wait 2-3 minutes for the instance to fully initialize")
        print(f"2. Test SSH connection: ssh -i ~/.ssh/{KEY_PAIR_NAME}.pem ubuntu@{final_ip}")
        print("3. Update your deployment script with the new IP address")
        print("4. Update your Cloudflare DNS A record to point to this IP")
        print("5. Run the deployment script to deploy your application")
        
        print(f"\n🔗 You can now update your Cloudflare DNS:")
        print(f"   A record: startlinker.com -> {final_ip}")
        print(f"   A record: www.startlinker.com -> {final_ip}")
        
        # Save configuration for deployment script
        config = {
            'instance_id': instance_id,
            'public_ip': final_ip,
            'region': AWS_REGION,
            'key_pair': KEY_PAIR_NAME,
            'security_group': security_group_id
        }
        
        with open('aws_instance_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Instance configuration saved to: aws_instance_config.json")
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print("Please check your AWS credentials and try again.")

if __name__ == "__main__":
    main()