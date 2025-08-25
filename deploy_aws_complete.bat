@echo off
echo =====================================
echo StartLinker AWS Deployment Script
echo =====================================
echo.

:: Check for Terraform variables
if not exist terraform.tfvars (
    echo ERROR: terraform.tfvars not found!
    echo Please create terraform.tfvars with:
    echo   db_password = "your-secure-password"
    echo   django_secret_key = "your-django-secret-key"
    pause
    exit /b 1
)

:: Step 1: Initialize and deploy infrastructure
echo Step 1: Deploying AWS Infrastructure...
echo ----------------------------------------
terraform.exe init
if errorlevel 1 (
    echo ERROR: Terraform init failed!
    pause
    exit /b 1
)

terraform.exe plan -out=tfplan
if errorlevel 1 (
    echo ERROR: Terraform plan failed!
    pause
    exit /b 1
)

echo.
echo Review the plan above. Continue with deployment? (Ctrl+C to cancel)
pause

terraform.exe apply tfplan
if errorlevel 1 (
    echo ERROR: Terraform apply failed!
    pause
    exit /b 1
)

:: Get outputs
echo.
echo Step 2: Getting Infrastructure Details...
echo ----------------------------------------
terraform.exe output -json > terraform_outputs.json

:: Extract EC2 IP
for /f "tokens=*" %%i in ('terraform.exe output -raw ec2_public_ip') do set EC2_IP=%%i
echo EC2 Public IP: %EC2_IP%

:: Step 3: Update frontend configuration
echo.
echo Step 3: Updating Frontend Configuration...
echo ----------------------------------------
powershell -Command "(Get-Content ..\frontend\src\config\api.config.js) -replace 'http://13.50.234.250', 'http://%EC2_IP%' | Set-Content ..\frontend\src\config\api.config.js"
echo Frontend updated with new EC2 IP: %EC2_IP%

:: Step 4: Wait for EC2 to be ready
echo.
echo Step 4: Waiting for EC2 instance to be ready...
echo ----------------------------------------
echo This may take 2-3 minutes...
timeout /t 120

:: Step 5: Create deployment package
echo.
echo Step 5: Creating Deployment Package...
echo ----------------------------------------
echo Preparing backend files...
tar -czf backend.tar.gz --exclude=*.pyc --exclude=__pycache__ --exclude=db.sqlite3 --exclude=venv --exclude=.env *.py *.txt *.md apps startup_hub static media

echo Preparing frontend files...
cd ..\frontend
call npm run build
tar -czf ..\startup_hub\frontend.tar.gz build
cd ..\startup_hub

:: Step 6: Deploy to EC2
echo.
echo Step 6: Deploying to EC2...
echo ----------------------------------------
echo Copying files to EC2...
scp -i startlinker-key -o StrictHostKeyChecking=no backend.tar.gz ec2-user@%EC2_IP%:/tmp/
scp -i startlinker-key -o StrictHostKeyChecking=no frontend.tar.gz ec2-user@%EC2_IP%:/tmp/

echo.
echo Setting up application on EC2...
ssh -i startlinker-key -o StrictHostKeyChecking=no ec2-user@%EC2_IP% "bash -s" < deploy_on_ec2.sh

echo.
echo =====================================
echo Deployment Complete!
echo =====================================
echo.
echo Your application is now available at:
echo   http://%EC2_IP%
echo.
echo Backend API: http://%EC2_IP%/api/
echo Admin Panel: http://%EC2_IP%/admin/
echo.
echo Note: It may take a few minutes for all services to start.
echo.
pause