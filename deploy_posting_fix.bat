@echo off
REM Batch file to deploy posting fixes to AWS from Windows

echo ==========================================
echo DEPLOYING POSTING FIXES TO AWS
echo ==========================================

REM Configuration
set SERVER_IP=13.50.234.250
set SSH_KEY=startlinker-key
set REMOTE_USER=ubuntu

echo.
echo Step 1: Creating deployment package...

REM Clean up old files
if exist deploy_temp rmdir /s /q deploy_temp
if exist backend_fix.tar.gz del backend_fix.tar.gz

REM Create deployment directory
mkdir deploy_temp

REM Copy backend files
echo Copying backend files...
xcopy /E /I /Y startup_hub deploy_temp\startup_hub
copy requirements.txt deploy_temp\
copy manage.py deploy_temp\

REM Create tar archive using PowerShell
echo Creating deployment archive...
powershell -Command "Compress-Archive -Path deploy_temp\* -DestinationPath backend_fix.zip -Force"

echo Step 2: Uploading to server...

REM Upload using SCP
scp -i %SSH_KEY% backend_fix.zip %REMOTE_USER%@%SERVER_IP%:/tmp/

echo Step 3: Connecting to server and applying fixes...

REM Create remote script
echo Creating remote deployment script...
(
echo #!/bin/bash
echo echo "Extracting backend files..."
echo cd /var/www/startlinker
echo sudo unzip -o /tmp/backend_fix.zip
echo.
echo echo "Installing dependencies..."
echo sudo pip3 install -r requirements.txt
echo.
echo echo "Running database migrations..."
echo sudo python3 manage.py migrate --noinput
echo.
echo echo "Collecting static files..."
echo sudo python3 manage.py collectstatic --noinput
echo.
echo echo "Restarting services..."
echo sudo systemctl restart gunicorn
echo sudo systemctl restart nginx
echo.
echo echo "Testing API..."
echo curl -I http://localhost:8000/api/v1/
) > remote_deploy.sh

REM Upload and execute remote script
scp -i %SSH_KEY% remote_deploy.sh %REMOTE_USER%@%SERVER_IP%:/tmp/
ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP% "chmod +x /tmp/remote_deploy.sh && sudo /tmp/remote_deploy.sh"

echo.
echo Step 4: Updating frontend...

cd ..\frontend

REM Update API configuration
echo Creating updated API configuration...
(
echo // API Configuration for Production
echo const API_BASE_URL = window.location.hostname === 'startlinker.com' ? 
echo   'https://startlinker.com/api/v1' : 'http://13.50.234.250/api/v1';
echo.
echo export default API_BASE_URL;
) > src\config\api.production.js

REM Install dependencies and build
echo Installing frontend dependencies...
call npm install

echo Building frontend...
call npm run build

REM Create frontend deployment archive
echo Creating frontend archive...
powershell -Command "Compress-Archive -Path build\* -DestinationPath ..\startup_hub\frontend_build.zip -Force"

cd ..\startup_hub

echo Uploading frontend build...
scp -i %SSH_KEY% frontend_build.zip %REMOTE_USER%@%SERVER_IP%:/tmp/

echo Deploying frontend on server...
ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP% "cd /var/www/startlinker && sudo rm -rf frontend/build && sudo mkdir -p frontend && cd frontend && sudo unzip /tmp/frontend_build.zip -d build"

echo.
echo ==========================================
echo DEPLOYMENT COMPLETE!
echo ==========================================
echo.
echo Please test the following:
echo 1. Visit http://startlinker.com
echo 2. Try to create a post
echo 3. Try to submit a startup
echo 4. Try to post a job
echo 5. Try to create a story
echo.
echo If issues persist, check logs:
echo ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP% "sudo journalctl -u gunicorn -n 50"
echo.

REM Cleanup
if exist deploy_temp rmdir /s /q deploy_temp
if exist backend_fix.zip del backend_fix.zip
if exist frontend_build.zip del frontend_build.zip
if exist remote_deploy.sh del remote_deploy.sh

pause