# Startlinker.com - Fix Posting Issues Deployment Guide

## Problem Summary
Users are unable to post content (posts, stories, startups, jobs) on startlinker.com

## Root Causes Identified
1. CORS configuration blocking frontend requests
2. API endpoint misconfiguration
3. Authentication token handling issues
4. CSRF protection interfering with API calls

## Fixes Applied

### 1. Backend Changes (Django)

#### Updated CORS Settings (startup_hub/settings/production.py)
- Added all necessary domains to CORS_ALLOWED_ORIGINS
- Enabled CORS credentials for authentication
- Added required headers to CORS_ALLOW_HEADERS
- Configured CSRF_TRUSTED_ORIGINS

#### Updated REST Framework Settings (startup_hub/settings/base.py)
- Changed default permissions to IsAuthenticatedOrReadOnly
- Ensured Token authentication is properly configured

### 2. Frontend Changes (React)

#### Updated API Configuration (frontend/src/config/api.config.js)
- Fixed API base URL to use correct AWS IP (13.50.234.250)
- Proper protocol handling (HTTP vs HTTPS)

#### Updated API Service (frontend/src/services/api.js)
- Added proper request interceptors for authentication
- Fixed URL construction issues
- Added proper error handling

### 3. Test Credentials Created
```
Email: test@startlinker.com
Password: Test@123456
Token: 1d403318fefbbfa7d39e73cde9fdc1eca01efd82
```

## Deployment Steps

### Option 1: Automated Deployment (Windows)

1. **Run the deployment script:**
   ```batch
   cd C:\Users\hruth\startup_hub
   deploy_posting_fix.bat
   ```

### Option 2: Manual Deployment

1. **SSH into the AWS server:**
   ```bash
   ssh -i startlinker-key ubuntu@13.50.234.250
   ```

2. **Update backend code:**
   ```bash
   cd /var/www/startlinker
   # Upload the updated files via SCP or git pull
   sudo pip3 install -r requirements.txt
   sudo python3 manage.py migrate
   sudo python3 manage.py collectstatic --noinput
   ```

3. **Update nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/startlinker
   ```
   
   Add CORS headers to the API location block:
   ```nginx
   location /api/ {
       if ($request_method = 'OPTIONS') {
           add_header 'Access-Control-Allow-Origin' '$http_origin' always;
           add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
           add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With, X-CSRFToken' always;
           add_header 'Access-Control-Allow-Credentials' 'true' always;
           return 204;
       }
       
       proxy_pass http://127.0.0.1:8000;
       # ... rest of proxy configuration
   }
   ```

4. **Build and deploy frontend:**
   ```bash
   # On local machine
   cd C:\Users\hruth\frontend
   npm install
   npm run build
   
   # Upload build folder to server
   scp -r build/* ubuntu@13.50.234.250:/var/www/startlinker/frontend/
   ```

5. **Restart services:**
   ```bash
   sudo systemctl restart gunicorn
   sudo systemctl restart nginx
   ```

## Testing

### 1. Test API Directly
```bash
# Test login
curl -X POST http://13.50.234.250/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@startlinker.com","password":"Test@123456"}'

# Test post creation (replace TOKEN with actual token)
curl -X POST http://13.50.234.250/api/v1/posts/ \
  -H "Authorization: Token 1d403318fefbbfa7d39e73cde9fdc1eca01efd82" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test post","is_public":true}'
```

### 2. Test via Browser
1. Visit http://startlinker.com
2. Login with test credentials
3. Try to:
   - Create a post
   - Submit a startup
   - Post a job
   - Create a story

## Monitoring

Check logs if issues persist:
```bash
# Django logs
sudo journalctl -u gunicorn -n 100

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Django debug (if enabled)
sudo tail -f /var/www/startlinker/logs/django.log
```

## Rollback Plan

If issues occur after deployment:

1. **Restore previous settings:**
   ```bash
   cd /var/www/startlinker
   git checkout HEAD~1 startup_hub/settings/
   sudo systemctl restart gunicorn
   ```

2. **Restore previous frontend:**
   ```bash
   # Keep backup of current build before deploying new one
   sudo mv /var/www/startlinker/frontend/build /var/www/startlinker/frontend/build.backup
   ```

## Additional Notes

- Ensure the Django environment variable is set to 'production' on the server
- The test user created has full permissions for testing
- CORS is configured to allow requests from both the domain name and IP address
- Token authentication is used for API endpoints, so CSRF can be disabled for API calls

## Contact

If issues persist after following these steps, check:
1. Server firewall rules (port 80, 443 should be open)
2. AWS Security Group settings
3. Django DEBUG mode (should be False in production)
4. Database connectivity
5. Redis service status (for caching and channels)