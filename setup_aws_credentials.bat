@echo off
echo ===============================================
echo AWS CLI Setup for StartLinker Deployment
echo ===============================================
echo.

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if errorlevel 1 (
    echo AWS CLI is not installed. Installing now...
    echo.
    echo Downloading AWS CLI installer...
    curl "https://awscli.amazonaws.com/AWSCLIV2.msi" -o "AWSCLIV2.msi"
    
    echo Installing AWS CLI...
    msiexec /i AWSCLIV2.msi /quiet
    
    echo Cleaning up...
    del AWSCLIV2.msi
    
    echo.
    echo AWS CLI installed successfully!
    echo Please restart your command prompt and run this script again.
    pause
    exit /b 0
)

echo AWS CLI is installed. Version:
aws --version
echo.

echo ===============================================
echo AWS Credentials Configuration
echo ===============================================
echo.
echo You need to provide your AWS credentials to deploy to EC2.
echo These should be from your AWS IAM user with EC2 permissions.
echo.

REM Get AWS credentials from user
set /p ACCESS_KEY_ID="Enter your AWS Access Key ID: "
set /p SECRET_ACCESS_KEY="Enter your AWS Secret Access Key: "
set /p REGION="Enter your preferred AWS region [eu-north-1]: "

REM Set default region if not provided
if "%REGION%"=="" set REGION=eu-north-1

echo.
echo Configuring AWS CLI...

REM Configure AWS CLI
aws configure set aws_access_key_id "%ACCESS_KEY_ID%"
aws configure set aws_secret_access_key "%SECRET_ACCESS_KEY%"
aws configure set default.region "%REGION%"
aws configure set default.output "json"

echo.
echo Testing AWS configuration...
aws sts get-caller-identity

if errorlevel 1 (
    echo.
    echo ERROR: AWS configuration failed!
    echo Please check your credentials and try again.
    pause
    exit /b 1
) else (
    echo.
    echo ✓ AWS CLI configured successfully!
    echo.
    echo Your configuration:
    echo Region: %REGION%
    echo.
    echo You can now run the deployment script:
    echo   quick_deploy.bat
    echo.
)

pause