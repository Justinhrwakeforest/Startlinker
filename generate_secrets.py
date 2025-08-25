#!/usr/bin/env python3
"""Generate secure secrets for deployment"""

import secrets
import string
import os

def generate_password(length=20):
    """Generate a secure password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Avoid problematic characters in passwords
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '')
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_django_secret(length=50):
    """Generate a Django secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("=" * 60)
    print("StartLinker Deployment Secrets Generator")
    print("=" * 60)
    print()
    
    db_password = generate_password(20)
    django_secret = generate_django_secret(50)
    
    print("Generated secure secrets:")
    print("-" * 40)
    print(f"Database Password: {db_password}")
    print(f"Django Secret Key: {django_secret}")
    print()
    
    # Create terraform.tfvars if it doesn't exist
    if not os.path.exists("terraform.tfvars"):
        with open("terraform.tfvars", "w") as f:
            f.write(f"""# Auto-generated Terraform Variables for StartLinker
# Generated secrets - keep these secure!

# Database Configuration
db_username = "startlinker_admin"
db_password = "{db_password}"

# Django Configuration  
django_secret_key = "{django_secret}"

# AWS Configuration
region = "us-east-1"
environment = "production"
project_name = "startlinker"

# Domain (optional)
domain_name = "startlinker.com"
""")
        print("✅ terraform.tfvars created successfully!")
        print("   File: terraform.tfvars")
    else:
        print("⚠️  terraform.tfvars already exists")
        print("   Copy the values above and update manually if needed")
    
    print()
    print("IMPORTANT: Keep these secrets secure and never commit to git!")
    print("=" * 60)