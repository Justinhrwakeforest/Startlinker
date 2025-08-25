@echo off
echo ==========================================
echo SSH INTO AWS AND FIX SERVER
echo ==========================================

set SERVER_IP=13.50.234.250
set SSH_KEY=startlinker-key
set REMOTE_USER=ubuntu

echo.
echo Connecting to AWS server to diagnose and fix issues...
echo.

REM Create a script to run on the server
(
echo #!/bin/bash
echo echo "=========================================="
echo echo "DIAGNOSING STARTLINKER SERVER"
echo echo "=========================================="
echo echo ""
echo 
echo echo "1. Checking Django service..."
echo sudo systemctl status gunicorn --no-pager ^| head -10
echo 
echo echo ""
echo echo "2. Checking Nginx service..."
echo sudo systemctl status nginx --no-pager ^| head -10
echo 
echo echo ""
echo echo "3. Checking if Django is running on port 8000..."
echo sudo netstat -tlnp ^| grep 8000
echo 
echo echo ""
echo echo "4. Checking Django logs..."
echo sudo journalctl -u gunicorn -n 20 --no-pager
echo 
echo echo ""
echo echo "5. Starting/Restarting services..."
echo sudo systemctl restart gunicorn
echo sudo systemctl restart nginx
echo 
echo echo ""
echo echo "6. Testing local API..."
echo curl -I http://localhost:8000/api/v1/
echo 
echo echo ""
echo echo "7. Creating test user in Django..."
echo cd /var/www/startlinker
echo sudo python3 manage.py shell ^<^< 'EOF'
echo from django.contrib.auth import get_user_model
echo from rest_framework.authtoken.models import Token
echo User = get_user_model^(^)
echo try:
echo     user = User.objects.filter^(email='test@startlinker.com'^).first^(^)
echo     if not user:
echo         user = User.objects.create_user^(
echo             username='testuser',
echo             email='test@startlinker.com',
echo             password='Test@123456',
echo             first_name='Test',
echo             last_name='User'
echo         ^)
echo     else:
echo         user.set_password^('Test@123456'^)
echo         user.save^(^)
echo     token, created = Token.objects.get_or_create^(user=user^)
echo     print^(f'User: {user.email}'^)
echo     print^(f'Token: {token.key}'^)
echo except Exception as e:
echo     print^(f'Error: {e}'^)
echo EOF
echo 
echo echo ""
echo echo "8. Checking firewall rules..."
echo sudo ufw status
echo 
echo echo ""
echo echo "9. Checking AWS security group (if aws cli available)..."
echo aws ec2 describe-security-groups --region eu-north-1 2^>/dev/null ^| grep -A 5 "80\|443\|8000" ^|^| echo "AWS CLI not configured"
echo 
echo echo ""
echo echo "=========================================="
echo echo "FIX ATTEMPT COMPLETE"
echo echo "=========================================="
) > server_diagnosis.sh

echo Uploading diagnosis script...
scp -i %SSH_KEY% server_diagnosis.sh %REMOTE_USER%@%SERVER_IP%:/tmp/

echo Running diagnosis and fixes on server...
ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP% "chmod +x /tmp/server_diagnosis.sh && sudo /tmp/server_diagnosis.sh"

echo.
echo ==========================================
echo Manual SSH Session
echo ==========================================
echo.
echo Connecting you to the server for manual fixes...
echo Commands to try:
echo   cd /var/www/startlinker
echo   sudo python3 manage.py runserver 0.0.0.0:8000
echo   sudo systemctl restart gunicorn
echo   sudo systemctl restart nginx
echo   sudo tail -f /var/log/nginx/error.log
echo.

ssh -i %SSH_KEY% %REMOTE_USER%@%SERVER_IP%

del server_diagnosis.sh
pause