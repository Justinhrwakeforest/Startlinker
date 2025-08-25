@echo off
echo ==========================================
echo DEPLOYING TO CORRECT SERVER: 44.219.216.107
echo ==========================================
echo.

REM The correct server IP from DNS
set SERVER_IP=44.219.216.107
set SSH_KEY=startlinker-key
set REMOTE_USER=ubuntu

echo Your DNS correctly points to: %SERVER_IP%
echo.

echo Step 1: Updating all configurations...

REM Update frontend .env
(
echo REACT_APP_API_URL=http://44.219.216.107
echo REACT_APP_BACKEND_URL=http://44.219.216.107
echo REACT_APP_STRIPE_PUBLIC_KEY=pk_test_51RlsxWIJmKIYZW7D6gLm4r1XxOOnfjlfWBh5wf02ReMD6kOqDTvgCeHspAuN7uoRtGvzLZn4pPMQvDqLxsW4n1pM00PoDRSldp
echo HTTPS=false
echo HOST=localhost
echo PORT=3000
) > ..\frontend\.env

REM Update production settings
echo Updating backend production settings...
powershell -Command "(Get-Content startup_hub\settings\production.py) -replace '13.50.234.250', '44.219.216.107' | Set-Content startup_hub\settings\production.py"

echo.
echo Step 2: Creating deployment package...

REM Clean old files
if exist deploy rmdir /s /q deploy
mkdir deploy

REM Copy backend files
xcopy /E /I /Y apps deploy\apps
xcopy /E /I /Y startup_hub deploy\startup_hub
copy manage.py deploy\
copy requirements.txt deploy\
copy complete_server_fix.sh deploy\

REM Create backend archive
cd deploy
tar -czf ..\backend_deploy.tar.gz *
cd ..

echo.
echo Step 3: Building frontend...
cd ..\frontend

REM Install and build
call npm install
call npm run build

REM Create frontend archive
tar -czf ..\startup_hub\frontend_deploy.tar.gz build\*

cd ..\startup_hub

echo.
echo Step 4: Uploading to server...

scp -i %SSH_KEY% backend_deploy.tar.gz %REMOTE_USER%@%SERVER_IP%:/tmp/
scp -i %SSH_KEY% frontend_deploy.tar.gz %REMOTE_USER%@%SERVER_IP%:/tmp/
scp -i %SSH_KEY% complete_server_fix.sh %REMOTE_USER%@%SERVER_IP%:/tmp/

echo.
echo Step 5: Deploying on server...

ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP% "cd /var/www/startlinker && sudo tar -xzf /tmp/backend_deploy.tar.gz && sudo mkdir -p frontend && sudo tar -xzf /tmp/frontend_deploy.tar.gz -C frontend/ && chmod +x /tmp/complete_server_fix.sh && sudo /tmp/complete_server_fix.sh"

echo.
echo ==========================================
echo DEPLOYMENT COMPLETE!
echo ==========================================
echo.
echo Server is at: http://44.219.216.107
echo Domain: http://startlinker.com
echo.
echo Test the API:
curl -X POST http://44.219.216.107/api/v1/auth/login/ -H "Content-Type: application/json" -d "{\"email\":\"test@startlinker.com\",\"password\":\"Test@123456\"}"
echo.

REM Cleanup
if exist deploy rmdir /s /q deploy
del backend_deploy.tar.gz 2>nul
del frontend_deploy.tar.gz 2>nul

pause