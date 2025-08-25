#!/usr/bin/env python3
"""
Create Render Deployment Guide
"""

def create_deployment_guide():
    """Create deployment guide"""
    print("Creating Render Deployment Guide")
    print("=" * 50)
    
    guide = '''# Render Deployment Guide

## Prerequisites
- Render account (free tier available)
- GitHub repository with your code

## Backend Deployment (Django)

### Step 1: Connect Repository
1. Go to Render Dashboard: https://dashboard.render.com/
2. Click "New" -> "Web Service"
3. Connect your GitHub repository
4. Select the repository containing your Django backend

### Step 2: Configure Backend Service
- Name: startup-hub-backend
- Environment: Python
- Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput
- Start Command: gunicorn startup_hub.wsgi:application
- Plan: Starter (Free)

### Step 3: Environment Variables
Add these environment variables:
- DJANGO_SETTINGS_MODULE: startup_hub.settings.render
- SECRET_KEY: (auto-generated)
- DEBUG: False
- ALLOWED_HOSTS: .onrender.com

### Step 4: Database
1. Create a new PostgreSQL service
2. Name it: startup-hub-db
3. Copy the DATABASE_URL to your backend service

## Frontend Deployment (React)

### Step 1: Connect Repository
1. Go to Render Dashboard: https://dashboard.render.com/
2. Click "New" -> "Static Site"
3. Connect your GitHub repository
4. Select the frontend directory

### Step 2: Configure Frontend Service
- Name: startup-hub-frontend
- Build Command: npm install && npm run build
- Publish Directory: build
- Plan: Starter (Free)

### Step 3: Environment Variables
Add these environment variables:
- REACT_APP_API_URL: https://startup-hub-backend.onrender.com
- REACT_APP_BACKEND_URL: https://startup-hub-backend.onrender.com

## Connect Services

### Update Frontend API Configuration
In your frontend code, update the API base URL to point to your Render backend:
```javascript
// In src/config/api.config.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://startup-hub-backend.onrender.com';
```

### Update CORS Settings
In your Django backend, ensure CORS allows your frontend domain:
```python
CORS_ALLOWED_ORIGINS = [
    "https://startup-hub-frontend.onrender.com",
]
```

## Deployment Complete!

Your services will be available at:
- Backend: https://startup-hub-backend.onrender.com
- Frontend: https://startup-hub-frontend.onrender.com

## Troubleshooting

### Backend Issues
- Check build logs in Render dashboard
- Verify environment variables are set correctly
- Ensure DATABASE_URL is properly configured

### Frontend Issues
- Check if API_URL is pointing to correct backend
- Verify build command completes successfully
- Check browser console for CORS errors

## Support
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com/
'''
    
    with open('RENDER_DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("Created RENDER_DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    create_deployment_guide()
