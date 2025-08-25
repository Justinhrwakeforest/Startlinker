"""
Continue debugging authentication with correct token format
"""

import requests
import json

API_URL = "http://localhost:8000/api"

def test_with_correct_token():
    session = requests.Session()
    
    # Use the token format discovered from debug
    token = "359189e083156d9d617d74c317bbf581d7feeed5"  # From previous test
    headers = {"Authorization": f"Token {token}"}  # Using Token, not Bearer
    
    print("TESTING WITH CORRECT TOKEN FORMAT")
    print("=" * 50)
    
    # Test profile endpoint
    print("\n1. TESTING PROFILE ENDPOINT")
    print("-" * 30)
    try:
        profile_response = session.get(f"{API_URL}/auth/profile/", headers=headers)
        print(f"Status: {profile_response.status_code}")
        if profile_response.status_code == 200:
            data = profile_response.json()
            print(f"User: {data.get('username')} ({data.get('email')})")
        else:
            print(f"Error: {profile_response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test job creation
    print("\n2. TESTING JOB CREATION")
    print("-" * 30)
    job_data = {
        "title": "Test Software Engineer Position",
        "company": "Test Company",
        "location": "Remote",
        "description": "Test job description",
        "requirements": "Python, Django",
        "salary_min": 50000,
        "salary_max": 80000,
        "job_type": "full-time",
        "is_remote": True
    }
    try:
        job_response = session.post(f"{API_URL}/jobs/", json=job_data, headers=headers)
        print(f"Status: {job_response.status_code}")
        if job_response.status_code == 201:
            job_data = job_response.json()
            print(f"Job created: {job_data.get('title')} (ID: {job_data.get('id')})")
        else:
            print(f"Error: {job_response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test startup creation
    print("\n3. TESTING STARTUP CREATION")
    print("-" * 30)
    startup_data = {
        "name": "Test Debug Startup",
        "description": "Test startup for debugging",
        "website": "https://test.com",
        "industry": "Technology", 
        "stage": "MVP",
        "location": "Remote",
        "team_size": 5
    }
    try:
        startup_response = session.post(f"{API_URL}/startups/", json=startup_data, headers=headers)
        print(f"Status: {startup_response.status_code}")
        if startup_response.status_code == 201:
            startup_data = startup_response.json()
            print(f"Startup created: {startup_data.get('name')} (ID: {startup_data.get('id')})")
        else:
            print(f"Error: {startup_response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test post creation
    print("\n4. TESTING POST CREATION")
    print("-" * 30)
    post_data = {
        "content": "Test post from debugging session",
        "is_public": True
    }
    try:
        post_response = session.post(f"{API_URL}/posts/", json=post_data, headers=headers)
        print(f"Status: {post_response.status_code}")
        if post_response.status_code == 201:
            post_data = post_response.json()
            print(f"Post created: ID {post_data.get('id')}")
        else:
            print(f"Error: {post_response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_with_correct_token()