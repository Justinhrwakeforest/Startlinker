# 🔐 Production Admin Setup Guide

## Quick Commands for Production Server

### Method 1: Using Django Management Command (Recommended)
```bash
# SSH into your production server
ssh your-server

# Navigate to your Django project
cd /path/to/startup_hub

# Activate virtual environment
source venv/bin/activate

# Set production environment
export DJANGO_SETTINGS_MODULE=startup_hub.settings.production

# Create superuser interactively
python manage.py createsuperuser

# Follow prompts:
# Email: admin@startlinker.com
# Username: admin (or leave blank to use email)
# Password: [secure password]
# Password (again): [confirm password]
```

### Method 2: Using the Custom Script
```bash
# Upload the script to your server
scp create_admin_production.py your-server:/path/to/startup_hub/

# SSH into server and run
ssh your-server
cd /path/to/startup_hub
python create_admin_production.py
```

### Method 3: Programmatic Creation
```bash
# Create admin via Python shell
python manage.py shell --settings=startup_hub.settings.production

# Then in Python shell:
from django.contrib.auth import get_user_model
User = get_user_model()

admin = User.objects.create_user(
    username='admin',
    email='admin@startlinker.com', 
    password='your_secure_password',
    first_name='Admin',
    last_name='User',
    is_staff=True,
    is_superuser=True,
    is_active=True,
    email_verified=True
)
print(f"Admin created: {admin.email}")
```

## Environment Variables Required

Make sure these are set on your production server:

```bash
# Required for production
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="postgresql://user:pass@host:port/db"
export ALLOWED_HOSTS="startlinker.com,www.startlinker.com"
export SENDGRID_API_KEY="SG.your-sendgrid-key"

# Optional but recommended
export DEFAULT_FROM_EMAIL="noreply@startlinker.com"
export REDIS_URL="redis://localhost:6379/0"
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export AWS_STORAGE_BUCKET_NAME="your-s3-bucket"
```

## Admin Access URLs

Once created, admin can access:

- **Django Admin Panel**: `https://startlinker.com/admin/`
- **API Admin Views**: `https://startlinker.com/api/admin/`

## Admin Permissions

The admin user will have:

- ✅ `is_staff = True` - Can access Django admin
- ✅ `is_superuser = True` - Full permissions  
- ✅ `is_active = True` - Account is active
- ✅ `email_verified = True` - Email verified

## Security Best Practices

1. **Strong Password**: Use 12+ characters with mixed case, numbers, symbols
2. **Secure Email**: Use a dedicated admin email address  
3. **2FA**: Enable two-factor authentication if available
4. **Limited Access**: Only create admin accounts for trusted users
5. **Regular Review**: Periodically review admin user list

## Testing Admin Access

```bash
# Test login via Django shell
python manage.py shell --settings=startup_hub.settings.production

from django.contrib.auth import authenticate
user = authenticate(username='admin@startlinker.com', password='your_password')
print(f"Login successful: {user is not None}")
print(f"Is admin: {user.is_staff and user.is_superuser}")
```

## Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python manage.py dbshell --settings=startup_hub.settings.production
```

### Missing Environment Variables
```bash
# Check what's set
env | grep -E "(SECRET_KEY|DATABASE_URL|ALLOWED_HOSTS)"
```

### Permission Errors
```bash
# Make sure user has admin permissions
python manage.py shell --settings=startup_hub.settings.production

from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='admin@startlinker.com')
user.is_staff = True
user.is_superuser = True
user.save()
```

## Production-Specific Features

Your production setup includes:

- 🔒 **Security Headers** - XSS protection, HSTS, etc.
- 📧 **SendGrid Email** - Production email delivery
- 🗄️ **PostgreSQL Database** - Production database
- 📦 **AWS S3 Storage** - Static/media file storage  
- 🚨 **Error Logging** - Comprehensive error tracking
- ⚡ **Redis Caching** - Performance optimization
- 🛡️ **Rate Limiting** - API protection

## Next Steps After Creating Admin

1. **Login to Admin Panel**: Visit `/admin/` and test login
2. **Review User Settings**: Check existing users and permissions  
3. **Configure Email Templates**: Customize verification email templates
4. **Set Up Monitoring**: Configure error tracking and monitoring
5. **Backup Strategy**: Implement regular database backups