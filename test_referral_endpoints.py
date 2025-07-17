#!/usr/bin/env python3
"""
Test script to verify referral endpoints are working correctly
"""

import os
import sys
import asyncio
import requests
import json
from supabase import create_client, Client

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configuration
BACKEND_URL = "https://patchai-backend.onrender.com"
SUPABASE_URL = "https://fqfgqxgbpgxdxqxqxqxq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZxZmdxeGdicGd4ZHhxeHF4cXhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjAzMTc0NzIsImV4cCI6MjAzNTg5MzQ3Mn0.Iq-_Zt2wUiOKNzYcCjhzOSGjZfXHPVhJQmOhLmZhZfE"

def get_auth_token(email: str, password: str) -> str:
    """Get authentication token from Supabase"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Sign in user
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.session:
            return auth_response.session.access_token
        else:
            raise Exception("Failed to get session")
            
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        return None

def test_referral_endpoints():
    """Test referral endpoints with authentication"""
    print("[INFO] Testing referral endpoints...")
    
    # Test credentials - use a known working user
    test_email = input("Enter test email: ").strip()
    test_password = input("Enter test password: ").strip()
    
    # Get auth token
    print("[AUTH] Getting authentication token...")
    token = get_auth_token(test_email, test_password)
    
    if not token:
        print("[ERROR] Failed to get authentication token")
        return
    
    print(f"[SUCCESS] Got auth token: {token[:50]}...")
    
    # Test headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Get profile
    print("\n[TEST] Testing GET /referrals/profile...")
    try:
        response = requests.get(f"{BACKEND_URL}/referrals/profile", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("[SUCCESS] Profile endpoint working")
            profile_data = response.json()
            print(f"Profile data: {json.dumps(profile_data, indent=2)}")
        else:
            print(f"[ERROR] Profile endpoint failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Profile endpoint error: {e}")
    
    # Test 2: Generate referral code
    print("\n[TEST] Testing POST /referrals/generate-code...")
    try:
        response = requests.post(f"{BACKEND_URL}/referrals/generate-code", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("[SUCCESS] Generate code endpoint working")
            code_data = response.json()
            print(f"Code data: {json.dumps(code_data, indent=2)}")
        else:
            print(f"[ERROR] Generate code endpoint failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Generate code endpoint error: {e}")
    
    # Test 3: Get referral info
    print("\n[TEST] Testing GET /referrals/info...")
    try:
        response = requests.get(f"{BACKEND_URL}/referrals/info", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("[SUCCESS] Referral info endpoint working")
            info_data = response.json()
            print(f"Referral info: {json.dumps(info_data, indent=2)}")
        else:
            print(f"[ERROR] Referral info endpoint failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Referral info endpoint error: {e}")

if __name__ == "__main__":
    test_referral_endpoints()
