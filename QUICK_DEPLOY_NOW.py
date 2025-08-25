#!/usr/bin/env python3
"""
Quick Deploy Now - AWS Console Method
"""

import os
import zipfile
import time

def create_final_packages():
    """Create the final deployment packages"""
    print("🚀 Creating Final Deployment Packages")
    print("=" * 50)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Create frontend package
    frontend_package = f"frontend-final-{timestamp}.zip"
    print(f"📦 Creating: {frontend_package}")
    
    # Check if frontend build exists
    frontend_build = "../frontend/build"
    if os.path.exists(frontend_build):
        with zipfile.ZipFile(frontend_package, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(frontend_build):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, frontend_build)
                    zipf.write(file_path, arcname)
        print(f"✅ Frontend package created: {frontend_package}")
    else:
        print("❌ Frontend build not found")
        return None, None
    
    # Create backend package
    backend_package = f"backend-final-{timestamp}.zip"
    print(f"📦 Creating: {backend_package}")
    
    include_items = ["apps", "startup_hub", "manage.py", "requirements.txt"]
    
    with zipfile.ZipFile(backend_package, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in include_items:
            if os.path.exists(item):
                if os.path.isdir(item):
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            if not file.endswith('.pyc') and '__pycache__' not in root:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, ".")
                                zipf.write(file_path, arcname)
                else:
                    zipf.write(item, item)
    
    print(f"✅ Backend package created: {backend_package}")
    return frontend_package, backend_package

def generate_deployment_commands(frontend_pkg, backend_pkg):
    """Generate the deployment commands"""
    print("\n📋 DEPLOYMENT COMMANDS")
    print("=" * 60)
    print("Copy and paste these commands in AWS Console Session Manager:")
    print()
    
    print("STEP 1: Prepare directories")
    print("sudo mkdir -p /tmp/frontend_upload")
    print("sudo mkdir -p /tmp/backend_upload")
    print("sudo chown ubuntu:ubuntu /tmp/frontend_upload")
    print("sudo chown ubuntu:ubuntu /tmp/backend_upload")
    print()
    
    print("STEP 2: After uploading files, deploy frontend")
    print(f"cd /tmp/frontend_upload")
    print(f"unzip {frontend_pkg}")
    print("sudo cp -r * /var/www/startlinker/frontend/")
    print("sudo chown -R ubuntu:ubuntu /var/www/startlinker/frontend/")
    print("sudo chmod -R 755 /var/www/startlinker/frontend/")
    print()
    
    print("STEP 3: Deploy backend")
    print(f"cd /tmp/backend_upload")
    print(f"unzip {backend_pkg}")
    print("cd /var/www/startlinker")
    print("sudo pip3 install -r requirements.txt")
    print("sudo python3 manage.py migrate --noinput")
    print("sudo python3 manage.py collectstatic --noinput")
    print()
    
    print("STEP 4: Restart services")
    print("sudo systemctl restart gunicorn")
    print("sudo systemctl restart nginx")
    print("sudo systemctl status gunicorn")
    print("sudo systemctl status nginx")
    print()

def main():
    print("🚀 QUICK DEPLOY NOW")
    print("=" * 50)
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create packages
    frontend_pkg, backend_pkg = create_final_packages()
    
    if frontend_pkg and backend_pkg:
        print("\n🎉 PACKAGES READY!")
        print("=" * 50)
        print(f"🌐 Frontend: {frontend_pkg}")
        print(f"🔧 Backend: {backend_pkg}")
        print()
        
        # Generate commands
        generate_deployment_commands(frontend_pkg, backend_pkg)
        
        print("🚀 DEPLOYMENT STEPS:")
        print("=" * 50)
        print("1. Go to AWS Console: https://console.aws.amazon.com/")
        print("2. Navigate to EC2 → Instances")
        print("3. Find instance: 13.62.96.192")
        print("4. Click 'Connect' → 'Session Manager' → 'Connect'")
        print("5. Upload both packages using 'Upload file'")
        print("6. Run the commands above")
        print()
        print("🌐 After deployment, visit: http://13.62.96.192/")
        
    else:
        print("❌ Failed to create deployment packages")

if __name__ == "__main__":
    main()
