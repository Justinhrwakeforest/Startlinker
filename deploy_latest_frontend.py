#!/usr/bin/env python3
"""
Deploy Latest Frontend Build to AWS
This script will help you deploy the latest frontend build to your AWS server
"""

import os
import zipfile
import shutil
import time

def create_deployment_package():
    """Create a deployment package with the latest frontend build"""
    print("🚀 Creating Deployment Package")
    print("=" * 50)
    
    # Check if build directory exists
    build_dir = "build"
    if not os.path.exists(build_dir):
        print("❌ Build directory not found. Please run 'npm run build' first.")
        return None
    
    # Create deployment package name with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    package_name = f"frontend-latest-{timestamp}.zip"
    
    print(f"📦 Creating package: {package_name}")
    
    # Create zip file
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)
                print(f"  📄 Added: {arcname}")
    
    print(f"✅ Package created: {package_name}")
    return package_name

def generate_deployment_instructions(package_name):
    """Generate step-by-step deployment instructions"""
    print("\n📋 DEPLOYMENT INSTRUCTIONS")
    print("=" * 60)
    print("Follow these steps to deploy to your AWS server:")
    print()
    
    print("STEP 1: Access AWS Console")
    print("  🌐 Go to: https://console.aws.amazon.com/")
    print("  📍 Navigate to: EC2 → Instances")
    print("  🔍 Find instance: 44.219.216.107")
    print("  🔗 Click: 'Connect' → 'Session Manager' → 'Connect'")
    print()
    
    print("STEP 2: Prepare Server Directory")
    print("  💻 In AWS terminal, run:")
    print("  sudo mkdir -p /tmp/frontend_upload")
    print("  sudo chown ubuntu:ubuntu /tmp/frontend_upload")
    print("  ls -la /tmp/frontend_upload")
    print()
    
    print("STEP 3: Upload Frontend Package")
    print("  📤 In AWS Console:")
    print("  - Click 'Connect' → 'Upload file'")
    print(f"  - Select file: {package_name}")
    print("  - Set destination: /tmp/frontend_upload/")
    print("  - Click 'Upload'")
    print()
    
    print("STEP 4: Deploy the Frontend")
    print("  💻 In AWS terminal, run:")
    print("  cd /tmp/frontend_upload")
    print("  ls -la")
    print(f"  unzip {package_name}")
    print("  ls -la")
    print("  sudo cp -r * /var/www/startlinker/frontend/")
    print("  sudo chown -R ubuntu:ubuntu /var/www/startlinker/frontend/")
    print("  sudo chmod -R 755 /var/www/startlinker/frontend/")
    print()
    
    print("STEP 5: Restart Services")
    print("  💻 In AWS terminal, run:")
    print("  sudo systemctl restart nginx")
    print("  sudo systemctl status nginx")
    print()
    
    print("STEP 6: Test the Deployment")
    print("  🌐 Open: http://44.219.216.107/")
    print("  ✅ Verify the latest version is deployed")
    print()
    
    print("🎉 DEPLOYMENT COMPLETE!")
    print("=" * 60)

def main():
    print("🚀 Startup Hub - Frontend Deployment")
    print("=" * 50)
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create deployment package
    package_name = create_deployment_package()
    
    if package_name:
        # Generate instructions
        generate_deployment_instructions(package_name)
        
        print(f"\n📁 Your deployment package is ready: {package_name}")
        print("📋 Follow the instructions above to deploy to AWS")
        print("🔐 You'll need to use your AWS credentials in the console")
        
    else:
        print("❌ Failed to create deployment package")

if __name__ == "__main__":
    main()
