@echo off
REM Quick deployment script for StartLinker on AWS
REM This script will launch a new EC2 instance and deploy the application

echo ===============================================
echo StartLinker AWS Quick Deployment
echo ===============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if AWS CLI is configured
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI is not configured
    echo Please run 'aws configure' first with your credentials
    pause
    exit /b 1
)

echo Step 1: Installing required Python packages...
pip install boto3 >nul 2>&1
echo ✓ Python dependencies installed

echo.
echo Step 2: Launching new EC2 instance...
python launch_ec2_instance.py

if not exist "aws_instance_config.json" (
    echo ERROR: Failed to create EC2 instance
    pause
    exit /b 1
)

REM Read the new IP address from config file
for /f "tokens=*" %%i in ('python -c "import json; config=json.load(open('aws_instance_config.json')); print(config['public_ip'])"') do set NEW_IP=%%i

echo.
echo Step 3: Updating deployment configuration...

REM Update the deployment script with new IP
powershell -Command "(Get-Content deploy_to_aws.bat) -replace '13\.50\.234\.250', '%NEW_IP%' | Set-Content deploy_to_aws_updated.bat"

echo ✓ Updated deployment script with new IP: %NEW_IP%

echo.
echo Step 4: Waiting for instance to be ready...
echo Please wait 3 minutes for the instance to fully initialize...
timeout /t 180 /nobreak

echo.
echo Step 5: Testing SSH connection...
ssh -i "%USERPROFILE%\.ssh\startlinker-key.pem" -o ConnectTimeout=10 -o BatchMode=yes ubuntu@%NEW_IP% "echo 'SSH connection successful'" 2>nul
if errorlevel 1 (
    echo WARNING: SSH connection failed. Instance might still be initializing.
    echo Please wait a few more minutes and try manual deployment.
)

echo.
echo Step 6: Starting application deployment...
call deploy_to_aws_updated.bat

echo.
echo ===============================================
echo Deployment Summary
echo ===============================================
echo Instance IP: %NEW_IP%
echo Domain: startlinker.com
echo.
echo IMPORTANT: Update your Cloudflare DNS records:
echo 1. Go to Cloudflare Dashboard
echo 2. Select startlinker.com domain
echo 3. Update A record: startlinker.com -> %NEW_IP%
echo 4. Update A record: www.startlinker.com -> %NEW_IP%
echo.
echo Your application will be available at:
echo - IP: http://%NEW_IP%
echo - Domain: https://startlinker.com (after DNS update)
echo.
pause