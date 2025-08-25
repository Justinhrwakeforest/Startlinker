@echo off
echo =====================================
echo StartLinker Local Development Server
echo =====================================
echo.

:: Start Django backend
echo Starting Django backend server...
start cmd /k "cd /d %CD% && python manage.py runserver 0.0.0.0:8000"

:: Wait a moment for backend to start
timeout /t 5

:: Start frontend
echo Starting React frontend server...
start cmd /k "cd /d %CD%\..\frontend && npm start"

echo.
echo =====================================
echo Servers are starting...
echo =====================================
echo.
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:3000
echo.
echo Press any key to stop all servers...
pause

:: Kill the servers
taskkill /F /IM python.exe
taskkill /F /IM node.exe

echo Servers stopped.
pause