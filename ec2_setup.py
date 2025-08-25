#!/usr/bin/env python3
"""
Quick setup script for EC2 Django backend
Run this on the EC2 instance to get the complete Django backend running
"""

import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and return the output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {command}: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    """Main setup function"""
    print("Starting Django backend setup on EC2...")
    
    # Install system dependencies
    run_command("sudo apt update")
    run_command("sudo apt install -y python3 python3-pip python3-venv git")
    
    # Create and activate virtual environment
    run_command("python3 -m venv ~/django_env")
    
    # Install Python packages
    pip_packages = [
        "django==4.2.23",
        "djangorestframework",
        "django-cors-headers",
        "channels",
        "whitenoise",
        "python-dotenv",
        "pillow",
        "stripe",
        "requests",
        "cryptography"
    ]
    
    for package in pip_packages:
        run_command(f"~/django_env/bin/pip install {package}")
    
    print("Setup complete! Now manually copy your Django project files to ~/")
    print("Then run: ~/django_env/bin/python manage.py runserver 0.0.0.0:8000")

if __name__ == "__main__":
    main()