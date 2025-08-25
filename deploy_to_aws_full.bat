@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo    StartLinker Full AWS Deployment Script
echo    Deploying: Frontend + Backend + PostgreSQL
echo ========================================================
echo.

:: Check for required files
echo [1/7] Checking prerequisites...
echo --------------------------------

if not exist terraform.exe (
    echo ERROR: terraform.exe not found!
    echo Please ensure terraform.exe is in the current directory
    pause
    exit /b 1
)

if not exist terraform.tfvars (
    echo.
    echo terraform.tfvars not found. Generating secure secrets...
    python generate_secrets.py
    if errorlevel 1 (
        echo ERROR: Failed to generate secrets!
        echo Please create terraform.tfvars manually using terraform.tfvars.example
        pause
        exit /b 1
    )
)

if not exist startlinker-key (
    echo.
    echo Generating SSH key pair for EC2 access...
    ssh-keygen -t rsa -b 4096 -f startlinker-key -N ""
    echo SSH key pair generated: startlinker-key and startlinker-key.pub
)

:: Initialize Terraform
echo.
echo [2/7] Initializing Terraform...
echo --------------------------------
terraform.exe init
if errorlevel 1 (
    echo ERROR: Terraform initialization failed!
    pause
    exit /b 1
)

:: Plan infrastructure
echo.
echo [3/7] Planning AWS infrastructure...
echo --------------------------------
terraform.exe plan -out=tfplan
if errorlevel 1 (
    echo ERROR: Terraform planning failed!
    pause
    exit /b 1
)

:: Confirm deployment
echo.
echo ========================================================
echo REVIEW THE PLAN ABOVE CAREFULLY!
echo.
echo This will create:
echo   - 1 EC2 instance (t2.micro - Free Tier)
echo   - 1 RDS PostgreSQL database (db.t3.micro - Free Tier)
echo   - VPC, Subnets, Security Groups
echo   - S3 buckets for static/media files
echo.
echo Estimated monthly cost after free tier: ~$20-30
echo ========================================================
echo.
set /p confirm="Do you want to proceed with deployment? (yes/no): "
if /i not "!confirm!"=="yes" (
    echo Deployment cancelled.
    exit /b 0
)

:: Apply infrastructure
echo.
echo [4/7] Creating AWS infrastructure...
echo --------------------------------
terraform.exe apply tfplan
if errorlevel 1 (
    echo ERROR: Infrastructure deployment failed!
    pause
    exit /b 1
)

:: Get outputs
echo.
echo [5/7] Retrieving infrastructure details...
echo -------------------------------------------
for /f "tokens=*" %%i in ('terraform.exe output -raw ec2_public_ip') do set EC2_IP=%%i
for /f "tokens=*" %%i in ('terraform.exe output -raw rds_endpoint') do set RDS_ENDPOINT=%%i
for /f "tokens=*" %%i in ('terraform.exe output -raw static_bucket_name') do set STATIC_BUCKET=%%i
for /f "tokens=*" %%i in ('terraform.exe output -raw media_bucket_name') do set MEDIA_BUCKET=%%i

echo EC2 Public IP: !EC2_IP!
echo RDS Endpoint: !RDS_ENDPOINT!
echo Static Bucket: !STATIC_BUCKET!
echo Media Bucket: !MEDIA_BUCKET!

:: Update frontend configuration
echo.
echo [6/7] Preparing deployment packages...
echo ---------------------------------------

:: Update frontend API URL
echo Updating frontend API configuration...
powershell -Command "(Get-Content ..\frontend\src\config\api.config.js) -replace 'http://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', 'http://!EC2_IP!' | Set-Content ..\frontend\src\config\api.config.js"

:: Build frontend
echo Building frontend application...
cd ..\frontend
call npm install
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    cd ..\startup_hub
    pause
    exit /b 1
)

:: Create deployment archive
echo Creating frontend archive...
tar -czf ..\startup_hub\frontend-deploy.tar.gz build
cd ..\startup_hub

:: Prepare backend
echo Preparing backend files...
tar -czf backend-deploy.tar.gz ^
    --exclude=*.pyc ^
    --exclude=__pycache__ ^
    --exclude=db.sqlite3 ^
    --exclude=venv ^
    --exclude=.env ^
    --exclude=terraform* ^
    --exclude=*.tar.gz ^
    --exclude=*.bat ^
    --exclude=*.sh ^
    apps startup_hub static media manage.py requirements.txt

:: Create deployment configuration
echo Creating deployment configuration...
echo !EC2_IP! > deploy_config.txt
echo !RDS_ENDPOINT! >> deploy_config.txt
echo !STATIC_BUCKET! >> deploy_config.txt
echo !MEDIA_BUCKET! >> deploy_config.txt

:: Wait for EC2 to be ready
echo.
echo Waiting for EC2 instance to initialize (2 minutes)...
timeout /t 120 /nobreak

:: Deploy to EC2
echo.
echo [7/7] Deploying application to EC2...
echo --------------------------------------

:: Copy files to EC2
echo Uploading files to EC2...
scp -i startlinker-key -o StrictHostKeyChecking=no ^
    backend-deploy.tar.gz ^
    frontend-deploy.tar.gz ^
    deploy_config.txt ^
    setup_server.sh ^
    ec2-user@!EC2_IP!:/tmp/

if errorlevel 1 (
    echo ERROR: Failed to upload files to EC2!
    echo Please check your SSH key and network connection
    pause
    exit /b 1
)

:: Execute setup on EC2
echo Configuring server...
ssh -i startlinker-key -o StrictHostKeyChecking=no ec2-user@!EC2_IP! "chmod +x /tmp/setup_server.sh && sudo /tmp/setup_server.sh"

if errorlevel 1 (
    echo WARNING: Server setup had issues. You may need to SSH in and debug.
)

:: Final output
echo.
echo ========================================================
echo    DEPLOYMENT COMPLETE!
echo ========================================================
echo.
echo Your application is now available at:
echo   🌐 Website: http://!EC2_IP!
echo   📊 Admin Panel: http://!EC2_IP!/admin/
echo   🔌 API Endpoint: http://!EC2_IP!/api/
echo.
echo SSH Access:
echo   ssh -i startlinker-key ec2-user@!EC2_IP!
echo.
echo Database:
echo   Host: !RDS_ENDPOINT!
echo   Database: startlinker_db
echo   Username: startlinker_admin
echo.
echo Default Admin Credentials:
echo   Email: admin@startlinker.com
echo   Password: AdminPass123!
echo.
echo IMPORTANT:
echo   1. Change the admin password immediately
echo   2. Configure a domain name and SSL certificate
echo   3. Set up regular backups
echo   4. Monitor AWS billing
echo.
echo ========================================================

pause