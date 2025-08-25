# Launch New EC2 Instance for StartLinker

## Option 1: Automated Launch (Recommended)

Run the quick deployment script:

```cmd
cd C:\Users\hruth\startup_hub
quick_deploy.bat
```

This will:
1. Launch a new EC2 instance
2. Configure security groups and networking
3. Deploy your application automatically
4. Provide the new IP address for DNS configuration

## Option 2: Manual AWS Console Launch

### Step 1: Launch Instance via AWS Console

1. **Go to EC2 Dashboard**: https://eu-north-1.console.aws.amazon.com/ec2/
2. **Click "Launch Instance"**
3. **Configure Instance**:
   - **Name**: `startlinker-web-server`
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance Type**: t3.medium (or t2.micro for free tier)
   - **Key Pair**: Select `startlinker-key` (or create new)
   - **Network Settings**:
     - Allow SSH traffic (port 22)
     - Allow HTTP traffic (port 80)
     - Allow HTTPS traffic (port 443)
   - **Storage**: 20 GB gp3
   - **Advanced Details → User Data**:

```bash
#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y curl wget git htop unzip python3-pip

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

# Start services
systemctl enable docker nginx
systemctl start docker nginx

# Simple ready page
echo '<h1>StartLinker Server Ready</h1>' > /var/www/html/index.html
```

4. **Launch Instance**

### Step 2: Get Instance IP Address

1. Go to **Instances** in EC2 Dashboard
2. Select your new instance
3. Copy the **Public IPv4 address**

### Step 3: Update DNS (Cloudflare)

1. Go to **Cloudflare Dashboard**
2. Select **startlinker.com** domain
3. Go to **DNS** section
4. Update A records:
   - `startlinker.com` → `[NEW_IP_ADDRESS]`
   - `www.startlinker.com` → `[NEW_IP_ADDRESS]`

### Step 4: Deploy Application

1. **Update deployment script** with new IP:
   ```cmd
   # Edit deploy_to_aws.bat
   # Replace "13.50.234.250" with your new IP address
   ```

2. **Run deployment**:
   ```cmd
   deploy_to_aws.bat
   ```

## Option 3: Using AWS CLI

If you have AWS CLI configured:

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0014ce3e52359afbd \
  --count 1 \
  --instance-type t3.medium \
  --key-name startlinker-key \
  --security-group-ids sg-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=startlinker-web-server}]' \
  --user-data file://user-data.sh

# Get instance IP
aws ec2 describe-instances --instance-ids i-xxxxxxxxx --query 'Reservations[0].Instances[0].PublicIpAddress'
```

## Post-Launch Checklist

- [ ] Instance is running
- [ ] SSH connection works: `ssh -i ~/.ssh/startlinker-key.pem ubuntu@[NEW_IP]`
- [ ] Cloudflare DNS updated
- [ ] Application deployed successfully
- [ ] Website accessible at https://startlinker.com
- [ ] SSL certificate configured

## Troubleshooting

### Instance won't start
- Check security group allows SSH (port 22)
- Verify key pair exists and is correct
- Check AWS service status

### Can't connect via SSH
- Wait 2-3 minutes after launch
- Check security group inbound rules
- Verify key file permissions: `chmod 400 ~/.ssh/startlinker-key.pem`

### Website not accessible
- Check if Nginx is running: `sudo systemctl status nginx`
- Verify DNS propagation: `nslookup startlinker.com`
- Check application logs: `docker-compose logs`

## Instance Specifications

- **Region**: eu-north-1 (Stockholm)
- **OS**: Ubuntu 22.04 LTS
- **Instance Type**: t3.medium
- **Storage**: 20GB SSD
- **Network**: VPC with public subnet
- **Ports**: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (Django)

## Security Features

- Firewall (UFW) configured
- Security groups with minimal required ports
- SSH key authentication
- SSL certificate via Let's Encrypt
- Cloudflare proxy protection

## Cost Estimation

- **t3.medium**: ~$30/month
- **20GB Storage**: ~$2/month
- **Data Transfer**: ~$5-10/month
- **Total**: ~$37-42/month

For development/testing, you can use t2.micro (free tier) to reduce costs.