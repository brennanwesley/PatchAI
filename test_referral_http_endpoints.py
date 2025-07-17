#!/usr/bin/env python3
"""
Test script to verify referral HTTP endpoints are working correctly
"""

import requests
import json
import sys

def test_referral_endpoints():
    """Test referral HTTP endpoints without authentication first"""
    
    # Backend URL
    backend_url = "https://patchai-backend.onrender.com"
    
    print("[INFO] Testing referral HTTP endpoints...")
    print(f"[INFO] Backend URL: {backend_url}")
    
    # Test 1: Health check first
    print("\n[TEST] Testing backend health...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health Data: {json.dumps(health_data, indent=2)}")
        else:
            print(f"Health check failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return
    
    # Test 2: Test referral code validation (public endpoint)
    print("\n[TEST] Testing POST /referrals/validate-code (public endpoint)...")
    try:
        payload = {"referral_code": "14CYUY"}
        response = requests.post(
            f"{backend_url}/referrals/validate-code", 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            print("[SUCCESS] Validate code endpoint working")
        else:
            print(f"[ERROR] Validate code endpoint failed")
    except Exception as e:
        print(f"[ERROR] Validate code endpoint error: {e}")
    
    # Test 3: Test protected endpoints without auth (should get 401/403)
    print("\n[TEST] Testing GET /referrals/profile (protected endpoint, no auth)...")
    try:
        response = requests.get(f"{backend_url}/referrals/profile", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code in [401, 403]:
            print("[SUCCESS] Protected endpoint properly requires authentication")
        elif response.status_code == 404:
            print("[ERROR] Endpoint not found - routing issue")
        elif response.status_code == 500:
            print("[ERROR] Internal server error - backend issue")
        else:
            print(f"[UNEXPECTED] Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Profile endpoint error: {e}")
    
    # Test 4: Test generate code endpoint without auth
    print("\n[TEST] Testing POST /referrals/generate-code (protected endpoint, no auth)...")
    try:
        response = requests.post(f"{backend_url}/referrals/generate-code", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code in [401, 403]:
            print("[SUCCESS] Protected endpoint properly requires authentication")
        elif response.status_code == 404:
            print("[ERROR] Endpoint not found - routing issue")
        elif response.status_code == 500:
            print("[ERROR] Internal server error - backend issue")
        else:
            print(f"[UNEXPECTED] Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Generate code endpoint error: {e}")
    
    # Test 5: Test with invalid auth token
    print("\n[TEST] Testing with invalid auth token...")
    try:
        headers = {
            'Authorization': 'Bearer invalid_token_12345',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{backend_url}/referrals/profile", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code in [401, 403]:
            print("[SUCCESS] Invalid token properly rejected")
        elif response.status_code == 500:
            print("[ERROR] Internal server error with invalid token")
        else:
            print(f"[UNEXPECTED] Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Invalid token test error: {e}")

if __name__ == "__main__":
    test_referral_endpoints()
