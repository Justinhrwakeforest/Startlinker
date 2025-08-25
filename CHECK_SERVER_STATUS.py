#!/usr/bin/env python
"""
Check current server status and what's running
"""

import requests
import json

SERVER_IP = "44.219.216.107"

def test_endpoints():
    """Test various endpoints to see what's working"""
    
    endpoints = [
        ("Homepage", f"http://{SERVER_IP}/", "GET"),
        ("API Root", f"http://{SERVER_IP}/api/", "GET"),
        ("API v1", f"http://{SERVER_IP}/api/v1/", "GET"),
        ("Auth Login", f"http://{SERVER_IP}/api/v1/auth/login/", "POST"),
        ("Posts", f"http://{SERVER_IP}/api/v1/posts/", "GET"),
        ("Django Admin", f"http://{SERVER_IP}/admin/", "GET"),
        ("Static Files", f"http://{SERVER_IP}/static/", "GET"),
        ("CORS Test", f"http://{SERVER_IP}/api/v1/auth/login/", "OPTIONS"),
    ]
    
    print("="*60)
    print("SERVER STATUS CHECK")
    print("="*60)
    print(f"Testing server: {SERVER_IP}")
    print()
    
    working_endpoints = []
    
    for name, url, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={"test": "data"}, timeout=5)
            elif method == "OPTIONS":
                response = requests.options(url, headers={"Origin": "http://startlinker.com"}, timeout=5)
            
            status = response.status_code
            
            if status < 400:
                working_endpoints.append((name, url, status))
                print(f"[OK] {name:15} - {status} - {response.headers.get('content-type', 'unknown')[:30]}")
            else:
                print(f"[FAIL] {name:15} - {status} - {response.reason}")
                
            # Check for CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            if cors_origin:
                print(f"       CORS: {cors_origin}")
                
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] {name:15} - No response")
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] {name:15} - Connection failed")
        except Exception as e:
            print(f"[ERROR] {name:15} - {str(e)[:50]}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if working_endpoints:
        print(f"\nWorking endpoints ({len(working_endpoints)}):")
        for name, url, status in working_endpoints:
            print(f"  - {name}: {status}")
    
    # Check what type of response we get from homepage
    try:
        response = requests.get(f"http://{SERVER_IP}/", timeout=5)
        content = response.text[:200]
        
        if "<!doctype html>" in content.lower():
            print(f"\n[INFO] Frontend is deployed (React/HTML)")
        elif "django" in content.lower():
            print(f"\n[INFO] Django is running")
        elif "nginx" in content.lower():
            print(f"\n[INFO] Nginx default page")
            
    except:
        pass
    
    # Test login specifically
    print(f"\n" + "="*40)
    print("LOGIN TEST")
    print("="*40)
    
    try:
        login_data = {
            "email": "test@startlinker.com",
            "password": "Test@123456"
        }
        
        response = requests.post(
            f"http://{SERVER_IP}/api/v1/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("[OK] Login works!")
            if 'token' in data:
                print(f"Token: {data['token'][:20]}...")
        else:
            print(f"Login Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Login Error: {e}")
    
    print(f"\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if len(working_endpoints) == 0:
        print("- Server appears to be down or unreachable")
        print("- Check AWS EC2 instance status")
        print("- Check security group settings")
    elif any("API" in name for name, _, _ in working_endpoints):
        print("- API endpoints are responding")
        print("- Check Django logs for specific errors")
    else:
        print("- Frontend is working but API is not configured")
        print("- Need to start Django backend")
        print("- Use AWS Session Manager to access server")

if __name__ == "__main__":
    test_endpoints()