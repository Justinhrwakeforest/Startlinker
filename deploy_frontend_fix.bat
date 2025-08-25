@echo off
echo ========================================
echo    Deploy Frontend Username Fix to AWS
echo ========================================
echo.

echo Step 1: Checking if frontend build exists...
if not exist "frontend-username-fix.zip" (
    echo ERROR: frontend-username-fix.zip not found!
    echo Please run the build script first.
    pause
    exit /b 1
)

echo Step 2: Frontend build found!
echo.

echo Step 3: Instructions for AWS deployment
echo.
echo Please follow these steps:
echo.
echo 1. Go to AWS EC2 Console
echo 2. Find your instance (IP: 51.21.246.24)
echo 3. Click "Connect" → "Session Manager" → "Connect"
echo 4. In the browser terminal, run these commands:
echo.
echo    # Create upload directory
echo    sudo mkdir -p /tmp/frontend_upload
echo    sudo chown ubuntu:ubuntu /tmp/frontend_upload
echo.
echo 5. Upload the frontend-username-fix.zip file to your server
echo    (Use AWS Console → Connect → Upload file)
echo.
echo 6. In the AWS terminal, run:
echo.
echo    # Extract and deploy
echo    cd /tmp/frontend_upload
echo    unzip frontend-username-fix.zip
echo    sudo cp -r build/* /var/www/startlinker/frontend/
echo    sudo chown -R ubuntu:ubuntu /var/www/startlinker/frontend/
echo    sudo systemctl restart nginx
echo.
echo 7. Test the fix:
echo    curl http://51.21.246.24/
echo.
echo The username validation should now work correctly!
echo.
pause
