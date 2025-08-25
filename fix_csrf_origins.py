#!/usr/bin/env python3
"""
Script to fix CSRF origins issue by connecting to server and updating Django settings
"""

import subprocess
import sys
import os

def try_ssh_connection():
    """Try to connect via SSH and run the fix command"""
    
    server_ip = "51.21.246.24"
    ssh_keys = ["startlinker-key", "startlinker-key.pem"]
    
    # The Django settings fix command
    django_fix_command = '''
cd /var/www/startlinker && \
sudo tee -a startup_hub/settings.py > /dev/null << "EOF"

# CSRF Trusted Origins Fix
CSRF_TRUSTED_ORIGINS = [
    "https://startlinker.com",
    "http://startlinker.com", 
    "https://www.startlinker.com",
    "http://www.startlinker.com",
    "http://51.21.246.24",
]

# Additional CSRF settings
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

EOF
echo "Django settings updated" && \
sudo systemctl restart gunicorn 2>/dev/null || echo "Gunicorn not running as service" && \
curl -I http://localhost/api/auth/login/ && \
echo "Fix applied successfully"
'''
    
    print("Attempting to fix CSRF origins on server...")
    
    for key in ssh_keys:
        if os.path.exists(key):
            print(f"Trying SSH key: {key}")
            try:
                # Try SSH connection
                result = subprocess.run([
                    "ssh", "-o", "ConnectTimeout=10", 
                    "-o", "StrictHostKeyChecking=no",
                    "-i", key,
                    f"ubuntu@{server_ip}",
                    django_fix_command
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Successfully connected and applied fix!")
                    print("Output:", result.stdout)
                    return True
                else:
                    print(f"❌ SSH failed with key {key}")
                    print("Error:", result.stderr[:200])
            except Exception as e:
                print(f"❌ Exception with key {key}: {e}")
    
    print("❌ Could not connect via SSH")
    return False

def create_alternative_solution():
    """Create alternative solutions if SSH doesn't work"""
    
    print("\n" + "="*60)
    print("ALTERNATIVE SOLUTIONS")
    print("="*60)
    
    print("\n1. EC2 Instance Connect Commands:")
    print("If you can access via EC2 Instance Connect, run these commands:")
    print("""
# Navigate to Django project
cd /var/www/startlinker

# Add CSRF trusted origins
sudo tee -a startup_hub/settings.py << 'EOF'

# CSRF Trusted Origins Fix
CSRF_TRUSTED_ORIGINS = [
    "https://startlinker.com",
    "http://startlinker.com", 
    "https://www.startlinker.com",
    "http://www.startlinker.com",
    "http://51.21.246.24",
]

# Additional CSRF settings
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

EOF

# Restart Django
sudo systemctl restart gunicorn || python3 manage.py runserver 127.0.0.1:8000 &

# Test fix
curl -X POST http://localhost/api/auth/login/ -H "Content-Type: application/json" -d '{"email":"test@startlinker.com","password":"Test@123456"}'
""")
    
    print("\n2. Quick Test Commands:")
    print("After applying the fix, test with these:")
    print("- curl -I https://startlinker.com/api/auth/login/")
    print("- Try logging in again on the website")
    
    print("\n3. Create New SSH Key:")
    print("If you need a new SSH key:")
    print("- Go to EC2 → Key Pairs → Create Key Pair")
    print("- Stop instance → Actions → Instance Settings → Change Key Pair")
    print("- Download new key and use it")

def main():
    print("🔧 CSRF Origins Fix Script")
    print("="*40)
    
    # Try SSH connection first
    success = try_ssh_connection()
    
    if not success:
        create_alternative_solution()
        
        print(f"\n🎯 MANUAL FIX NEEDED:")
        print("The Django backend needs this added to its settings:")
        print("""
CSRF_TRUSTED_ORIGINS = [
    "https://startlinker.com",
    "http://startlinker.com", 
    "https://www.startlinker.com",
    "http://www.startlinker.com",
    "http://51.21.246.24",
]
""")
        
        print("Once you add this to Django settings and restart, login will work!")

if __name__ == "__main__":
    main()