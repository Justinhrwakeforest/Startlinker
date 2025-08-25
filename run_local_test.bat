@echo off
echo ==========================================
echo TESTING STARTLINKER LOCALLY
echo ==========================================

echo.
echo Step 1: Starting Django development server...
start /B cmd /c "python manage.py runserver 0.0.0.0:8000"

timeout /t 5 >nul

echo Step 2: Testing API endpoints...
echo.

echo Testing connection...
curl -I http://localhost:8000/api/v1/

echo.
echo Testing auth endpoint...
curl -X OPTIONS http://localhost:8000/api/v1/auth/login/ -H "Origin: http://localhost:3000" -I

echo.
echo Step 3: Starting frontend development server...
cd ..\frontend
start /B cmd /c "npm start"

echo.
echo Waiting for frontend to start...
timeout /t 10 >nul

echo.
echo ==========================================
echo LOCAL TEST ENVIRONMENT READY!
echo ==========================================
echo.
echo Backend running at: http://localhost:8000
echo Frontend running at: http://localhost:3000
echo.
echo Test the following:
echo 1. Open http://localhost:3000 in your browser
echo 2. Try to register/login
echo 3. Try to create a post
echo 4. Try to submit a startup
echo 5. Try to post a job
echo.
echo Press any key to stop all servers...
pause >nul

taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul

echo Servers stopped.
pause