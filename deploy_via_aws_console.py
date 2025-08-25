#!/usr/bin/env python3
"""
Deploy via AWS Console - No SSH Required
This script prepares everything for manual deployment through AWS Console
"""

import os
import zipfile
import shutil
import time
from pathlib import Path

def create_frontend_package():
    """Create a frontend deployment package"""
    print("🚀 Creating Frontend Deployment Package")
    print("=" * 50)
    
    # Check if frontend build exists
    frontend_build = Path("../frontend/build")
    if not frontend_build.exists():
        print("❌ Frontend build not found. Please run 'npm run build' in the frontend directory first.")
        return None
    
    # Create package name with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    package_name = f"frontend-latest-{timestamp}.zip"
    
    print(f"📦 Creating package: {package_name}")
    
    # Create zip file
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(frontend_build):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, frontend_build)
                zipf.write(file_path, arcname)
                print(f"  📄 Added: {arcname}")
    
    print(f"✅ Frontend package created: {package_name}")
    return package_name

def create_backend_package():
    """Create a backend deployment package"""
    print("\n🔧 Creating Backend Deployment Package")
    print("=" * 50)
    
    # Create package name with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    package_name = f"backend-latest-{timestamp}.zip"
    
    print(f"📦 Creating package: {package_name}")
    
    # Files and directories to include
    include_items = [
        "apps",
        "startup_hub", 
        "manage.py",
        "requirements.txt",
        "db.sqlite3"
    ]
    
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in include_items:
            if os.path.exists(item):
                if os.path.isdir(item):
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, ".")
                            zipf.write(file_path, arcname)
                            print(f"  📄 Added: {arcname}")
                else:
                    zipf.write(item, item)
                    print(f"  📄 Added: {item}")
    
    print(f"✅ Backend package created: {package_name}")
    return package_name

def generate_deployment_instructions(frontend_package, backend_package):
    """Generate step-by-step deployment instructions"""
    print("\n📋 AWS CONSOLE DEPLOYMENT INSTRUCTIONS")
    print("=" * 60)
    print("Follow these steps to deploy via AWS Console:")
    print()
    
    print("STEP 1: Access AWS Console")
    print("  🌐 Go to: https://console.aws.amazon.com/")
    print("  📍 Navigate to: EC2 → Instances")
    print("  🔍 Find instance: 44.219.216.107")
    print("  🔗 Click: 'Connect' → 'Session Manager' → 'Connect'")
    print()
    
    print("STEP 2: Prepare Server Directories")
    print("  💻 In AWS terminal, run:")
    print("  sudo mkdir -p /tmp/frontend_upload")
    print("  sudo mkdir -p /tmp/backend_upload")
    print("  sudo chown ubuntu:ubuntu /tmp/frontend_upload")
    print("  sudo chown ubuntu:ubuntu /tmp/backend_upload")
    print()
    
    print("STEP 3: Upload Frontend Package")
    print("  📤 In AWS Console:")
    print("  - Click 'Connect' → 'Upload file'")
    print(f"  - Select file: {frontend_package}")
    print("  - Set destination: /tmp/frontend_upload/")
    print("  - Click 'Upload'")
    print()
    
    print("STEP 4: Upload Backend Package")
    print("  📤 In AWS Console:")
    print("  - Click 'Connect' → 'Upload file'")
    print(f"  - Select file: {backend_package}")
    print("  - Set destination: /tmp/backend_upload/")
    print("  - Click 'Upload'")
    print()
    
    print("STEP 5: Deploy Frontend")
    print("  💻 In AWS terminal, run:")
    print("  cd /tmp/frontend_upload")
    print(f"  unzip {frontend_package}")
    print("  sudo cp -r * /var/www/startlinker/frontend/")
    print("  sudo chown -R ubuntu:ubuntu /var/www/startlinker/frontend/")
    print("  sudo chmod -R 755 /var/www/startlinker/frontend/")
    print()
    
    print("STEP 6: Deploy Backend")
    print("  💻 In AWS terminal, run:")
    print("  cd /tmp/backend_upload")
    print(f"  unzip {backend_package}")
    print("  cd /var/www/startlinker")
    print("  sudo pip3 install -r requirements.txt")
    print("  sudo python3 manage.py migrate --noinput")
    print("  sudo python3 manage.py collectstatic --noinput")
    print()
    
    print("STEP 7: Restart Services")
    print("  💻 In AWS terminal, run:")
    print("  sudo systemctl restart gunicorn")
    print("  sudo systemctl restart nginx")
    print("  sudo systemctl status gunicorn")
    print("  sudo systemctl status nginx")
    print()
    
    print("STEP 8: Test the Deployment")
    print("  🌐 Open: http://44.219.216.107/")
    print("  ✅ Verify the latest version is deployed")
    print("  🔧 Test API: http://44.219.216.107/api/")
    print()
    
    print("🎉 DEPLOYMENT COMPLETE!")
    print("=" * 60)

def main():
    print("🚀 Startup Hub - AWS Console Deployment")
    print("=" * 50)
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create frontend package
    frontend_package = create_frontend_package()
    
    # Create backend package
    backend_package = create_backend_package()
    
    if frontend_package and backend_package:
        # Generate instructions
        generate_deployment_instructions(frontend_package, backend_package)
        
        print(f"\n📁 Your deployment packages are ready:")
        print(f"  🌐 Frontend: {frontend_package}")
        print(f"  🔧 Backend: {backend_package}")
        print("\n📋 Follow the instructions above to deploy via AWS Console")
        print("🔐 No SSH keys required - uses AWS Console Session Manager")
        
    else:
        print("❌ Failed to create deployment packages")

if __name__ == "__main__":
    main()
