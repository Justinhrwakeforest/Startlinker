# Backend Deployment Guide for StartLinker

## Current Status
✅ **Frontend**: Deployed and working at http://44.219.216.107  
❌ **Backend**: Not deployed (causing username validation issues)

## Quick Fix Applied
The frontend now includes **offline username validation** that works when the backend is unavailable:
- ✅ Length validation (3-20 characters)
- ✅ Character validation (letters, numbers, _, .)
- ✅ Format validation (no starting/ending with _ or .)
- ✅ No consecutive __ or ..
- ✅ Basic profanity filtering
- ⚠️ **Note**: Shows "(server verification disabled)" when backend is down

## To Deploy the Full Backend

### Option 1: Deploy to Current EC2 Instance

1. **SSH into EC2**:
   ```bash
   ssh -i startlinker-key ec2-user@44.219.216.107
   ```

2. **Upload your backend code** (choose one method):
   
   **Method A - Git Clone (if repository is public)**:
   ```bash
   sudo mkdir -p /opt/startlinker/backend
   sudo chown ec2-user:ec2-user /opt/startlinker/backend
   cd /opt/startlinker/backend
   git clone [your-repo-url] .
   ```
   
   **Method B - File Upload**:
   ```bash
   # On your local machine
   tar -czf backend.tar.gz --exclude=venv --exclude=*.pyc --exclude=__pycache__ apps startup_hub manage.py requirements.txt
   scp -i startlinker-key backend.tar.gz ec2-user@44.219.216.107:/tmp/
   
   # Then on EC2
   sudo mkdir -p /opt/startlinker/backend
   sudo chown ec2-user:ec2-user /opt/startlinker/backend
   cd /opt/startlinker/backend
   tar -xzf /tmp/backend.tar.gz
   ```

3. **Install Dependencies**:
   ```bash
   # Install Python packages
   pip3 install --user -r requirements.txt
   pip3 install --user gunicorn psycopg2-binary
   
   # Set up environment
   cat > .env << EOF
   DEBUG=False
   SECRET_KEY=$(openssl rand -hex 32)
   ALLOWED_HOSTS=44.219.216.107,localhost,127.0.0.1
   DATABASE_URL=sqlite:////opt/startlinker/backend/db.sqlite3
   CORS_ALLOWED_ORIGINS=http://44.219.216.107
   DJANGO_SETTINGS_MODULE=startup_hub.settings.aws_deploy
   EOF
   ```

4. **Run Migrations**:
   ```bash
   python3 manage.py migrate
   python3 manage.py collectstatic --noinput
   
   # Create superuser (optional)
   python3 manage.py createsuperuser
   ```

5. **Start Backend Service**:
   ```bash
   # Create systemd service
   sudo tee /etc/systemd/system/startlinker-backend.service > /dev/null << 'EOF'
   [Unit]
   Description=StartLinker Django Backend
   After=network.target
   
   [Service]
   Type=simple
   User=ec2-user
   WorkingDirectory=/opt/startlinker/backend
   ExecStart=/home/ec2-user/.local/bin/gunicorn --bind 127.0.0.1:8000 startup_hub.wsgi:application
   Restart=always
   Environment="PATH=/home/ec2-user/.local/bin:/usr/bin:/bin"
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Start service
   sudo systemctl daemon-reload
   sudo systemctl enable startlinker-backend
   sudo systemctl start startlinker-backend
   ```

6. **Update Nginx Configuration**:
   ```bash
   sudo tee /etc/nginx/conf.d/default.conf > /dev/null << 'EOF'
   server {
       listen 80;
       server_name _;
       root /var/www/html;
       index index.html;
       
       # Frontend routes
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       # Backend API
       location /api/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Django Admin
       location /admin/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       # Static files
       location /static/ {
           alias /opt/startlinker/backend/static/;
       }
   }
   EOF
   
   sudo nginx -t && sudo systemctl restart nginx
   ```

### Option 2: Use RDS PostgreSQL (Optional)

If you want to use the RDS PostgreSQL instance:

1. **Get RDS endpoint**:
   ```bash
   # On your local machine
   terraform output rds_endpoint
   ```

2. **Update .env file**:
   ```bash
   # On EC2, update the DATABASE_URL
   DATABASE_URL=postgresql://startlinker_admin:your-db-password@your-rds-endpoint:5432/startlinker_db
   ```

## Testing the Fix

After deployment, test the username validation:

1. Visit: http://44.219.216.107
2. Click "Sign Up"
3. Try entering usernames:
   - ✅ `testuser123` (should show green checkmark)
   - ❌ `te` (should show "Username must be at least 3 characters")
   - ❌ `_invalid` (should show "Username cannot start with underscores")
   - ❌ `test__user` (should show "Username cannot contain consecutive underscores")

## Health Check Commands

```bash
# Check backend service status
sudo systemctl status startlinker-backend

# Check nginx status
sudo systemctl status nginx

# View backend logs
sudo journalctl -u startlinker-backend -f

# Test API endpoint
curl http://localhost:8000/api/auth/check-username/?username=testuser
```

## Current Working Features (Frontend Only)
- ✅ User interface loads correctly
- ✅ Navigation works
- ✅ Client-side form validation
- ✅ Offline username validation with proper error messages

## Features That Need Backend
- ❌ User registration/login
- ❌ Server-side username availability check
- ❌ Data persistence
- ❌ API endpoints
- ❌ Admin panel

The username validation now works in offline mode with comprehensive client-side validation. Users will see proper error messages and can proceed with signup once the backend is deployed.