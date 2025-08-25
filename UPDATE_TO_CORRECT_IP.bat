@echo off
echo ==========================================
echo UPDATING TO CORRECT SERVER IP
echo ==========================================
echo.
echo Your DNS points to: 44.219.216.107
echo We were using: 13.50.234.250
echo.

set /p CORRECT_IP="Enter the CORRECT server IP [44.219.216.107]: "
if "%CORRECT_IP%"=="" set CORRECT_IP=44.219.216.107

echo.
echo Updating all configuration files to use %CORRECT_IP%...

REM Update frontend .env
echo REACT_APP_API_URL=http://%CORRECT_IP% > ..\frontend\.env
echo REACT_APP_BACKEND_URL=http://%CORRECT_IP% >> ..\frontend\.env

REM Update frontend API config
powershell -Command "(Get-Content ..\frontend\src\config\api.config.js) -replace '13.50.234.250', '%CORRECT_IP%' -replace '44.219.216.107', '%CORRECT_IP%' | Set-Content ..\frontend\src\config\api.config.js"

REM Update backend settings
powershell -Command "(Get-Content startup_hub\settings\production.py) -replace '13.50.234.250', '%CORRECT_IP%' -replace '44.219.216.107', '%CORRECT_IP%' | Set-Content startup_hub\settings\production.py"

REM Update .env.production
powershell -Command "(Get-Content .env.production) -replace '13.50.234.250', '%CORRECT_IP%' -replace '44.219.216.107', '%CORRECT_IP%' | Set-Content .env.production"

echo.
echo Building frontend with correct IP...
cd ..\frontend
call npm run build

echo.
echo ==========================================
echo CONFIGURATION UPDATED!
echo ==========================================
echo.
echo Next steps:
echo 1. Deploy to server at %CORRECT_IP%
echo 2. SSH into server: ssh -i startlinker-key ubuntu@%CORRECT_IP%
echo 3. Test API: curl http://%CORRECT_IP%/api/v1/
echo.
pause