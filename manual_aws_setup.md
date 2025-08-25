# Manual AWS Setup Guide

## Step 1: Install AWS CLI (if not installed)

### Option A: Download and Install
1. Go to: https://aws.amazon.com/cli/
2. Download AWS CLI for Windows
3. Run the installer
4. Restart your command prompt

### Option B: Use PowerShell (Windows 10/11)
```powershell
# Run as Administrator
winget install Amazon.AWSCLI
```

## Step 2: Get Your AWS Credentials

You need to get your AWS Access Keys from the AWS Console:

1. **Go to AWS Console**: https://console.aws.amazon.com/
2. **Click your name** (top right) → **Security Credentials**
3. **Scroll down** to "Access keys"
4. **Click "Create access key"**
5. **Choose "Command Line Interface (CLI)"**
6. **Add description**: "StartLinker Deployment"
7. **Click "Create access key"**
8. **IMPORTANT**: Copy both:
   - Access Key ID (starts with AKIA...)
   - Secret Access Key (long random string)

## Step 3: Configure AWS CLI

Run this command and enter your credentials:

```cmd
aws configure
```

Enter:
- **AWS Access Key ID**: [Your Access Key ID]
- **AWS Secret Access Key**: [Your Secret Access Key]  
- **Default region name**: `eu-north-1`
- **Default output format**: `json`

## Step 4: Test Configuration

```cmd
aws sts get-caller-identity
```

You should see output with your AWS account details.

## Step 5: Run Deployment

Now you can run the deployment script:

```cmd
quick_deploy.bat
```

## Alternative: Manual EC2 Launch

If you prefer to use the AWS Console instead:

### Launch Instance Manually:

1. **Go to EC2 Console**: https://eu-north-1.console.aws.amazon.com/ec2/
2. **Click "Launch Instance"**
3. **Configure**:
   - Name: `startlinker-web-server`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.medium
   - Key pair: Create new → Name: `startlinker-key`
   - Security Group: Allow SSH, HTTP, HTTPS
   - Storage: 20 GB

4. **In Advanced Details → User data**, paste:
```bash
#!/bin/bash
apt-get update && apt-get upgrade -y
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
apt-get install -y nginx certbot python3-certbot-nginx
mkdir -p /opt/startup_hub /opt/frontend
chown -R ubuntu:ubuntu /opt/startup_hub /opt/frontend
systemctl enable docker nginx && systemctl start docker nginx
```

5. **Launch Instance**
6. **Download the .pem key file** and save it to `~/.ssh/`

### Deploy Application:

1. **Get the Instance IP** from EC2 console
2. **Update deploy_to_aws.bat** with the new IP
3. **Run deployment**:
   ```cmd
   deploy_to_aws.bat
   ```

## Required AWS Permissions

Your IAM user needs these permissions:
- EC2FullAccess (or specific EC2 permissions)
- Ability to create/manage instances, security groups, key pairs

## Troubleshooting

### "Access Denied" errors:
- Check your IAM user has EC2 permissions
- Verify credentials are correct

### "Region not found":
- Make sure you're using a valid AWS region
- eu-north-1 (Stockholm) is recommended

### AWS CLI not found:
- Restart command prompt after installation
- Check PATH environment variable includes AWS CLI

## Security Best Practices

1. **Create dedicated IAM user** for deployment (don't use root)
2. **Use minimal required permissions**
3. **Store credentials securely**
4. **Rotate access keys regularly**
5. **Enable MFA on your AWS account**