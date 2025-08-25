#!/usr/bin/env python3
"""
Deploy with SCP - Direct File Upload
"""

import os
import subprocess
import time
import zipfile

def create_deployment_package():
    """Create a deployment package"""
    print("📦 Creating deployment package...")
    
    # Create package name with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    package_name = f"deployment-{timestamp}.zip"
    
    # Files to include
    include_items = [
        "apps",
        "startup_hub", 
        "manage.py",
        "requirements.txt"
    ]
    
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
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
    
    print(f"✅ Created package: {package_name}")
    return package_name

def deploy_with_scp(package_name):
    """Deploy using SCP"""
    print("\n🚀 Deploying with SCP...")
    print("=" * 40)
    
    # Check if SSH key exists
    ssh_key = "startlinker-key"
    if not os.path.exists(ssh_key):
        print(f"❌ SSH key not found: {ssh_key}")
        print("Please ensure the SSH key is in the current directory")
        return False
    
    # Upload package
    print("📤 Uploading deployment package...")
    scp_command = [
        'scp', '-o', 'StrictHostKeyChecking=no',
        '-i', ssh_key,
        package_name,
        f'ubuntu@13.62.96.192:/tmp/'
    ]
    
    result = subprocess.run(scp_command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Upload failed: {result.stderr}")
        return False
    
    print("✅ Package uploaded successfully!")
    
    # Execute deployment commands
    print("🔧 Executing deployment commands...")
    ssh_commands = f"""
    cd /var/www/startlinker
    sudo systemctl stop gunicorn
    sudo systemctl stop nginx
    cd /tmp
    sudo unzip -o {package_name}
    sudo cp -r * /var/www/startlinker/
    cd /var/www/startlinker
    sudo pip3 install -r requirements.txt
    sudo python3 manage.py migrate --noinput
    sudo python3 manage.py collectstatic --noinput
    sudo systemctl start gunicorn
    sudo systemctl start nginx
    echo "Deployment complete!"
    """
    
    ssh_command = [
        'ssh', '-o', 'StrictHostKeyChecking=no',
        '-i', ssh_key,
        'ubuntu@13.62.96.192',
        ssh_commands
    ]
    
    result = subprocess.run(ssh_command, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Deployment completed successfully!")
        print(f"🌐 Your site is available at: http://13.62.96.192/")
        return True
    else:
        print(f"❌ Deployment failed: {result.stderr}")
        return False

def main():
    print("🚀 SCP Deployment")
    print("=" * 40)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create deployment package
    package_name = create_deployment_package()
    
    # Deploy
    success = deploy_with_scp(package_name)
    
    if success:
        print("\n🎉 Deployment successful!")
    else:
        print("\n❌ Deployment failed. Check the error messages above.")

if __name__ == "__main__":
    main()
