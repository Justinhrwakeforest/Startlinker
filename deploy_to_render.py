#!/usr/bin/env python3
"""
Quick Render Deployment Preparation Script
This script prepares your project for Render deployment
"""
import os
import subprocess

def check_requirements():
    """Check if all requirements are met"""
    print("Checking deployment requirements...")
    
    checks = {
        'GitHub repo': check_git_repo(),
        'requirements.txt': os.path.exists('requirements.txt'),
        'Frontend package.json': os.path.exists('../frontend/package.json'),
        'Render settings': os.path.exists('startup_hub/settings/render.py'),
        'gunicorn in requirements': check_gunicorn(),
        'whitenoise in requirements': check_whitenoise(),
    }
    
    for check, status in checks.items():
        status_icon = "OK" if status else "FAIL"
        print(f"  [{status_icon}] {check}")
    
    return all(checks.values())

def check_git_repo():
    """Check if this is a git repository"""
    return os.path.exists('.git')

def check_gunicorn():
    """Check if gunicorn is in requirements"""
    try:
        with open('requirements.txt', 'r') as f:
            return 'gunicorn' in f.read()
    except FileNotFoundError:
        return False

def check_whitenoise():
    """Check if whitenoise is in requirements"""
    try:
        with open('requirements.txt', 'r') as f:
            return 'whitenoise' in f.read()
    except FileNotFoundError:
        return False

def create_render_yaml():
    """Create render.yaml for infrastructure as code deployment"""
    print("\nCreating render.yaml...")
    
    yaml_content = """services:
  - type: pserv
    name: startlinker-db
    env: postgresql
    plan: starter
    databaseName: startlinker_db
    user: startlinker_user

  - type: web
    name: startlinker-backend
    env: python
    plan: starter
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput --clear
    startCommand: python manage.py migrate --noinput && gunicorn startup_hub.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: DJANGO_SETTINGS_MODULE
        value: startup_hub.settings.render
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
      - key: CORS_ALLOWED_ORIGINS
        value: "https://startlinker-frontend.onrender.com"
      - key: DATABASE_URL
        fromService:
          type: pserv
          name: startlinker-db
          property: connectionString

  - type: web
    name: startlinker-frontend
    env: static
    plan: starter
    buildCommand: cd ../frontend && npm ci && npm run build
    staticPublishPath: ../frontend/build
    envVars:
      - key: NODE_VERSION
        value: "18"
      - key: REACT_APP_API_URL
        value: "https://startlinker-backend.onrender.com"
      - key: GENERATE_SOURCEMAP
        value: "false"
      - key: CI
        value: "false"
"""
    
    with open('render.yaml', 'w') as f:
        f.write(yaml_content)
    
    print("  render.yaml created successfully!")

def print_deployment_summary():
    """Print deployment summary and next steps"""
    print("\n" + "="*60)
    print("RENDER DEPLOYMENT READY!")
    print("="*60)
    
    print("\nNEXT STEPS:")
    print("1. Push your code to GitHub:")
    print("   git add .")
    print("   git commit -m 'Prepare for Render deployment'")
    print("   git push origin main")
    
    print("\n2. Go to https://dashboard.render.com")
    print("3. Choose deployment method:")
    print("   - Manual: Follow RENDER_DEPLOYMENT_GUIDE.md")
    print("   - Auto: New → Blueprint → Connect GitHub repo")
    
    print("\nESTIMATED COSTS:")
    print("   - PostgreSQL: $7/month")
    print("   - Backend: $7/month") 
    print("   - Frontend: FREE")
    print("   - Total: ~$14/month")
    
    print("\nYOUR URLS (after deployment):")
    print("   - Frontend: https://startlinker-frontend.onrender.com")
    print("   - Backend: https://startlinker-backend.onrender.com")
    print("   - Admin: https://startlinker-backend.onrender.com/admin/")

def main():
    """Main deployment preparation function"""
    print("StartLinker Render Deployment Preparation")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("Error: Please run this script from the project root directory")
        return
    
    # Run all checks
    if not check_requirements():
        print("\nSome requirements are not met. Please fix the issues above.")
        return
    
    # Create render.yaml
    create_render_yaml()
    
    # Print summary
    print_deployment_summary()

if __name__ == '__main__':
    main()