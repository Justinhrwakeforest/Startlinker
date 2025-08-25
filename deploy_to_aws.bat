@echo off
echo ========================================
echo Startup Hub AWS Deployment
echo ========================================
echo.

REM Check if Git Bash is available
where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git Bash is not installed or not in PATH
    echo Please install Git for Windows: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if AWS CLI is available
where aws >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS CLI is not installed or not in PATH
    echo Please install AWS CLI: https://aws.amazon.com/cli/
    pause
    exit /b 1
)

REM Check if Docker is available
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Prerequisites check passed!
echo.

REM Make the script executable and run it
bash deploy_to_aws.sh

echo.
echo Deployment script completed!
pause