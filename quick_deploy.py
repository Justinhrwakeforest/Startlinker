#!/usr/bin/env python
"""
Quick deployment script for Startlinker
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command"""
    if description:
        print(f"\n>>> {description}")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Command successful")
            if result.stdout:
                print(result.stdout[:500])
        else:
            print(f"[ERROR] Command failed with code {result.returncode}")
            if result.stderr:
                print(result.stderr[:500])
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def main():
    print("="*60)
    print("QUICK DEPLOYMENT TO CORRECT SERVER")
    print("="*60)
    
    SERVER_IP = "44.219.216.107"
    SSH_KEY = "startlinker-key"
    REMOTE_USER = "ubuntu"
    
    print(f"\nServer IP: {SERVER_IP}")
    print(f"SSH Key: {SSH_KEY}")
    
    # Check if SSH key exists
    if not os.path.exists(SSH_KEY):
        print(f"\n[ERROR] SSH key not found: {SSH_KEY}")
        print("Please ensure the SSH key is in the current directory")
        return
    
    print("\nStep 1: Creating deployment package...")
    
    # Clean and create deploy directory
    deploy_dir = Path("deploy")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Copy backend files
    for item in ["apps", "startup_hub"]:
        if Path(item).exists():
            shutil.copytree(item, deploy_dir / item)
    
    for file in ["manage.py", "requirements.txt"]:
        if Path(file).exists():
            shutil.copy2(file, deploy_dir / file)
    
    print("[OK] Deployment package created")
    
    print("\nStep 2: Creating tar archive...")
    run_command("tar -czf backend_deploy.tar.gz -C deploy .")
    
    print("\nStep 3: Uploading to server...")
    
    # Upload backend
    upload_cmd = f'scp -o StrictHostKeyChecking=no -i {SSH_KEY} backend_deploy.tar.gz {REMOTE_USER}@{SERVER_IP}:/tmp/'
    if not run_command(upload_cmd, "Uploading backend"):
        print("\n[ERROR] Failed to upload backend. Check your SSH key and connection.")
        return
    
    # Upload fix script
    if Path("complete_server_fix.sh").exists():
        run_command(f'scp -o StrictHostKeyChecking=no -i {SSH_KEY} complete_server_fix.sh {REMOTE_USER}@{SERVER_IP}:/tmp/')
    
    print("\nStep 4: Deploying on server...")
    
    # SSH commands to run on server
    ssh_commands = """
    cd /var/www/startlinker
    sudo tar -xzf /tmp/backend_deploy.tar.gz
    sudo pip3 install -r requirements.txt
    sudo python3 manage.py migrate --noinput
    sudo python3 manage.py collectstatic --noinput
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
    echo "Deployment complete!"
    """
    
    ssh_cmd = f'ssh -o StrictHostKeyChecking=no -i {SSH_KEY} {REMOTE_USER}@{SERVER_IP} "{ssh_commands}"'
    run_command(ssh_cmd, "Running deployment on server")
    
    print("\nStep 5: Testing API...")
    
    # Test the API
    import requests
    try:
        response = requests.get(f"http://{SERVER_IP}/api/v1/", timeout=5)
        print(f"API Status: {response.status_code}")
        
        # Test login
        login_data = {
            "email": "test@startlinker.com",
            "password": "Test@123456"
        }
        login_response = requests.post(
            f"http://{SERVER_IP}/api/v1/auth/login/",
            json=login_data,
            timeout=5
        )
        if login_response.status_code == 200:
            print("[OK] Login endpoint working!")
        else:
            print(f"[INFO] Login returned: {login_response.status_code}")
            print(f"Response: {login_response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] API test failed: {e}")
    
    # Cleanup
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    if Path("backend_deploy.tar.gz").exists():
        os.remove("backend_deploy.tar.gz")
    
    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"\nServer: http://{SERVER_IP}")
    print(f"Domain: http://startlinker.com")
    print("\nTest with:")
    print(f"  Email: test@startlinker.com")
    print(f"  Password: Test@123456")

if __name__ == "__main__":
    main()