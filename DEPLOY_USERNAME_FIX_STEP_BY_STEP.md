# 🚀 Deploy Username Fix to AWS - Step by Step

## ✅ Prerequisites
- AWS Console access
- Your frontend build: `frontend-username-fix.zip` (1.4MB) - ✅ READY

## 📋 Step-by-Step Instructions

### Step 1: Access AWS Console
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **EC2** → **Instances**
3. Find your instance with IP: `51.21.246.24`
4. Click **"Connect"** → **"Session Manager"** → **"Connect"**

### Step 2: Prepare Server Directory
In the AWS browser terminal, run:
```bash
# Create upload directory
sudo mkdir -p /tmp/frontend_upload
sudo chown ubuntu:ubuntu /tmp/frontend_upload
ls -la /tmp/frontend_upload
```

### Step 3: Upload Frontend File
1. In the AWS Console, click **"Connect"** → **"Upload file"**
2. Click **"Choose file"** and select `frontend-username-fix.zip`
3. Set destination: `/tmp/frontend_upload/`
4. Click **"Upload"**

### Step 4: Deploy the Fix
In the AWS terminal, run:
```bash
# Navigate to upload directory
cd /tmp/frontend_upload

# List files to confirm upload
ls -la

# Extract the frontend
unzip frontend-username-fix.zip

# Check extracted files
ls -la build/

# Deploy to web directory
sudo cp -r build/* /var/www/startlinker/frontend/

# Set proper permissions
sudo chown -R ubuntu:ubuntu /var/www/startlinker/frontend/

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

### Step 5: Test the Fix
```bash
# Test the website
curl -I http://51.21.246.24/

# Check if frontend files are deployed
ls -la /var/www/startlinker/frontend/
```

## 🎯 What This Fixes

### Before (Broken):
- ❌ API calls to `/api/api/auth/check-username/` (double /api/)
- ❌ 30-second timeouts
- ❌ Connection aborted errors
- ❌ Username validation not working

### After (Fixed):
- ✅ API calls to `/api/auth/check-username/` (correct)
- ✅ 10-second timeouts for faster feedback
- ✅ Enhanced error handling with fallbacks
- ✅ Username validation working properly

## 🧪 Testing Instructions

1. **Open your website**: `http://51.21.246.24/`
2. **Go to signup page**
3. **Try entering a username**
4. **Check browser console** - should see:
   - ✅ No more double `/api/` URLs
   - ✅ Successful API responses
   - ✅ No timeout errors

## 🔧 Troubleshooting

### If nginx fails to restart:
```bash
# Check nginx configuration
sudo nginx -t

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### If frontend doesn't load:
```bash
# Check file permissions
ls -la /var/www/startlinker/frontend/

# Check nginx configuration
sudo cat /etc/nginx/sites-enabled/startlinker
```

### If API calls still fail:
```bash
# Check if Django backend is running
sudo systemctl status gunicorn
sudo systemctl status django

# Check backend logs
sudo journalctl -u gunicorn -f
```

## 📞 Need Help?

If you encounter any issues:
1. Copy the exact error message
2. Note which step failed
3. Check the troubleshooting section above

## 🎉 Success Indicators

You'll know the fix worked when:
- ✅ Website loads without errors
- ✅ Username validation responds quickly
- ✅ No timeout errors in browser console
- ✅ API calls show correct URLs (no double /api/)

---

**Ready to deploy? Follow the steps above and let me know if you need help with any specific step!**
