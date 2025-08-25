#!/usr/bin/env python3
"""
Quick status check for the AWS deployment
"""

import requests
import time

def check_server_status():
    """Check if the server is responding"""
    print("🔍 Checking AWS Server Status")
    print("=" * 50)
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Server: http://44.219.216.107/")
    
    try:
        # Test basic connectivity
        response = requests.get("http://44.219.216.107/", timeout=10)
        print(f"✅ Server Status: {response.status_code}")
        
        # Check if it's the fix page or the regular app
        if "Username Fix Deployed" in response.text:
            print("✅ Username fix page is deployed!")
            return True
        elif "StartLinker" in response.text or "React" in response.text:
            print("✅ Regular app is running")
            return True
        else:
            print("⚠️  Server responding but content unclear")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Server timeout - server might be down")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_username_validation():
    """Test the username validation endpoint"""
    print("\n👤 Testing Username Validation")
    print("=" * 50)
    
    try:
        url = "http://44.219.216.107/api/auth/check-username/?username=testuser"
        response = requests.get(url, timeout=10)
        
        print(f"📡 URL: {url}")
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Response: {data}")
            print("✅ Username validation is working!")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - Username validation not responding")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("🚀 Startup Hub - AWS Deployment Status Check")
    print("=" * 60)
    
    # Check server status
    server_ok = check_server_status()
    
    if server_ok:
        # Test username validation
        validation_ok = test_username_validation()
        
        print("\n" + "=" * 60)
        print("📋 SUMMARY:")
        print(f"🌐 Server: {'✅ Working' if server_ok else '❌ Down'}")
        print(f"👤 Username Validation: {'✅ Working' if validation_ok else '❌ Broken'}")
        
        if server_ok and validation_ok:
            print("\n🎉 Everything is working! Your fix is deployed successfully.")
            print("🌐 Visit: http://44.219.216.107/")
        elif server_ok and not validation_ok:
            print("\n⚠️  Server is up but username validation needs fixing.")
            print("📋 Next step: Deploy the username fix")
        else:
            print("\n❌ Server is down. Need to check AWS console.")
    else:
        print("\n❌ Server is not accessible. Check AWS console.")

if __name__ == "__main__":
    main()
