@echo off
echo ==========================================
echo FINAL FIX FOR STARTLINKER.COM
echo ==========================================
echo.

set SERVER_IP=13.50.234.250
set SSH_KEY=startlinker-key
set REMOTE_USER=ubuntu

echo Step 1: Uploading backend fixes...

REM Create a deployment package
if exist deploy_package rmdir /s /q deploy_package
mkdir deploy_package

REM Copy all Python files
xcopy /E /I /Y apps deploy_package\apps
xcopy /E /I /Y startup_hub deploy_package\startup_hub
copy manage.py deploy_package\
copy requirements.txt deploy_package\

REM Create tar file
cd deploy_package
tar -czf ../backend_final.tar.gz *
cd ..

echo Uploading backend package...
scp -i %SSH_KEY% backend_final.tar.gz %REMOTE_USER%@%SERVER_IP%:/tmp/
scp -i %SSH_KEY% complete_server_fix.sh %REMOTE_USER%@%SERVER_IP%:/tmp/

echo.
echo Step 2: Building frontend with correct API URL...

cd ..\frontend

REM Update .env for production
echo REACT_APP_API_URL=http://13.50.234.250 > .env.production
echo REACT_APP_BACKEND_URL=http://13.50.234.250 >> .env.production

REM Build frontend
call npm install
call npm run build

REM Create frontend package
tar -czf ..\startup_hub\frontend_final.tar.gz build\*

cd ..\startup_hub

echo Uploading frontend build...
scp -i %SSH_KEY% frontend_final.tar.gz %REMOTE_USER%@%SERVER_IP%:/tmp/

echo.
echo Step 3: Executing fixes on server...

ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP% "cd /var/www/startlinker && sudo tar -xzf /tmp/backend_final.tar.gz && sudo tar -xzf /tmp/frontend_final.tar.gz -C frontend/ && chmod +x /tmp/complete_server_fix.sh && sudo /tmp/complete_server_fix.sh"

echo.
echo ==========================================
echo DEPLOYMENT COMPLETE!
echo ==========================================
echo.
echo Please test at: http://startlinker.com
echo.
echo Test login with:
echo   Email: test@startlinker.com
echo   Password: Test@123456
echo.

REM Cleanup
if exist deploy_package rmdir /s /q deploy_package
del backend_final.tar.gz 2>nul
del frontend_final.tar.gz 2>nul

pause