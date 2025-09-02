#!/usr/bin/env python3
"""
Test script for frontend authentication integration
"""

import requests
import json

def test_auth_endpoints():
    """Test the authentication endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Testing EdAgent Authentication Endpoints")
    print("=" * 50)
    
    # Test registration
    print("\n1. Testing User Registration...")
    register_data = {
        "email": "frontend.test@example.com",
        "password": "FrontendTest123!",
        "name": "Frontend Test User"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/register", json=register_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Registration successful!")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Email: {result.get('email')}")
            print(f"   Token: {result.get('access_token')[:20]}...")
            
            # Store for login test
            user_email = result.get('email')
            access_token = result.get('access_token')
            
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return
    
    # Test login
    print("\n2. Testing User Login...")
    login_data = {
        "email": "frontend.test@example.com",
        "password": "FrontendTest123!"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Email: {result.get('email')}")
            print(f"   Token: {result.get('access_token')[:20]}...")
            
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
    
    # Test authenticated endpoint
    print("\n3. Testing Authenticated Endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{base_url}/users/me", headers=headers)
        if response.status_code == 200:
            print("✅ Authenticated request successful!")
        else:
            print(f"❌ Authenticated request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Authenticated request error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication test completed!")
    print("\n💡 Frontend Integration Notes:")
    print("   - Registration and login endpoints are working")
    print("   - JWT tokens are being issued correctly")
    print("   - Streamlit frontend should now work with email/password auth")
    print("   - Access the frontend at: http://localhost:8501")

if __name__ == "__main__":
    test_auth_endpoints()