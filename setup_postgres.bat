@echo off
echo Creating PostgreSQL database for startup_hub...
echo.
echo Please enter the PostgreSQL password when prompted.
echo Default password is often 'postgres' or what you set during installation.
echo.

"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE startup_hub;"
if %errorlevel% neq 0 (
    echo.
    echo Database might already exist or there was an error.
    echo Trying to connect to existing database...
)

echo.
echo Testing connection to startup_hub database...
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d startup_hub -c "SELECT version();"

echo.
echo Setup complete! 
echo.
echo Now you need to:
echo 1. Update the DB_PASSWORD in .env file with your PostgreSQL password
echo 2. Run: python manage.py migrate
pause