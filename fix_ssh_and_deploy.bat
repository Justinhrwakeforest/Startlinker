@echo off
echo ================================================
echo StartLinker - Fix SSH and Restart Services
echo ================================================

REM Find the correct SSH key location
set SSH_KEY=""
if exist "C:\Users\hruth\.ssh\startlinker-key" set SSH_KEY=C:\Users\hruth\.ssh\startlinker-key
if exist "C:\Users\hruth\.ssh\startlinker-key.pem" set SSH_KEY=C:\Users\hruth\.ssh\startlinker-key.pem
if exist "C:\Users\hruth\startup_hub\startlinker-key" set SSH_KEY=C:\Users\hruth\startup_hub\startlinker-key
if exist "C:\Users\hruth\startlinker-key" set SSH_KEY=C:\Users\hruth\startlinker-key

if %SSH_KEY%=="" (
    echo ERROR: SSH key not found. Looking for key files...
    dir /s /b C:\Users\hruth\*startlinker-key*
    echo.
    echo Please check the locations above and update the SSH_KEY variable
    pause
    exit /b 1
)

echo Using SSH key: %SSH_KEY%
echo.

REM Set correct permissions (Windows equivalent)
icacls "%SSH_KEY%" /inheritance:r
icacls "%SSH_KEY%" /grant:r "%USERNAME%":F

echo Testing SSH connection...
ssh -i "%SSH_KEY%" -o ConnectTimeout=10 ubuntu@51.21.246.24 "echo 'SSH connection successful!'"

if %errorlevel% neq 0 (
    echo SSH connection failed. Try using AWS Session Manager instead.
    echo Go to AWS Console → EC2 → Instances → Connect → Session Manager
    pause
    exit /b 1
)

echo.
echo ================================================
echo SSH connection works! Now fixing the server...
echo ================================================
echo.

REM Check what's running
echo Checking current processes...
ssh -i "%SSH_KEY%" ubuntu@51.21.246.24 "ps aux | grep -E '(gunicorn|python|django)'"

echo.
echo Checking if Gunicorn is running on port 8000...
ssh -i "%SSH_KEY%" ubuntu@51.21.246.24 "sudo netstat -tlnp | grep :8000"

echo.
echo Checking Django project structure...
ssh -i "%SSH_KEY%" ubuntu@51.21.246.24 "ls -la /opt/startup_hub/backend/ || ls -la /opt/startup_hub/"

echo.
echo ================================================
echo Server diagnosis complete. Now run commands manually:
echo ================================================
echo.
echo 1. Connect to server:
echo    ssh -i "%SSH_KEY%" ubuntu@51.21.246.24
echo.
echo 2. Navigate to project directory:
echo    cd /opt/startup_hub/backend
echo.
echo 3. Activate virtual environment:
echo    source venv/bin/activate
echo.
echo 4. Check Django settings:
echo    python manage.py check
echo.
echo 5. Run migrations:
echo    python manage.py migrate
echo.
echo 6. Start Gunicorn:
echo    gunicorn --bind 0.0.0.0:8000 startup_hub.wsgi:application --log-level debug
echo.
pause