# StartLinker Deployment Instructions

## Quick Deployment on Render

### Step 1: Deploy Backend (This Repository)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect this GitHub repository: `https://github.com/Justinhrwakeforest/Startlinker`
4. Click **"Apply"** - This will deploy:
   - PostgreSQL database
   - Django backend

### Step 2: Deploy Frontend (Separate Repository)

1. Create a new **Static Site** on Render
2. Connect the frontend repository (to be created)
3. Configure:
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `build`
   - **Environment Variables**:
     - `NODE_VERSION`: `18`
     - `REACT_APP_API_URL`: `https://startlinker-backend.onrender.com`

## Manual Deployment Alternative

### Backend Service

1. **New Web Service**
   - Name: `startlinker-backend`
   - Environment: Python
   - Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start: `python manage.py migrate && gunicorn startup_hub.wsgi:application`
   - Environment Variables:
     - `DJANGO_SETTINGS_MODULE`: `startup_hub.settings.render`
     - `SECRET_KEY`: Auto-generate
     - `DATABASE_URL`: From PostgreSQL service

### Database Service

1. **New PostgreSQL Database**
   - Name: `startlinker-db`
   - Plan: Free

### Frontend Service

1. **New Static Site**
   - Build: `npm ci && npm run build`
   - Publish: `build`
   - Environment: `REACT_APP_API_URL=https://startlinker-backend.onrender.com`

## Final URLs

- **Backend**: https://startlinker-backend.onrender.com
- **Frontend**: https://startlinker-frontend.onrender.com
- **Admin**: https://startlinker-backend.onrender.com/admin/

## Cost

- Database: Free
- Backend: Free (with limitations)
- Frontend: Free
- **Total: $0/month** (with free tier limitations)

Upgrade to paid plans for production use.