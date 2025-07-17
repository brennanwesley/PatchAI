#!/usr/bin/env python3
"""
Direct test of PatchAI production chat functionality
Tests the /prompt endpoint with real authentication to verify OpenAI integration
"""

import requests
import json
import sys
import os
from supabase import create_client, Client

# Production backend URL
BACKEND_URL = "https://patchai-backend.onrender.com"

# Supabase configuration (from frontend)
SUPABASE_URL = "https://iyacqcylnunndcswaeri.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5YWNxY3lsbnVubmRjc3dhZXJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ0NzI4MTAsImV4cCI6MjA1MDA0ODgxMH0.Ky3zUuJYJUE2JwJJKWLNzYJJjGnqcQNBJUVfKJJKJJI"

def authenticate_user(email, password):
    """Authenticate user with Supabase and get JWT token"""
    try:
        print(f"[AUTH] Authenticating user: {email}")
        
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Sign in user
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user and response.session:
            token = response.session.access_token
            print(f"[SUCCESS] Authentication successful")
            print(f"[TOKEN] Token: {token[:20]}...{token[-10:]}")
            return token
        else:
            print("[ERROR] Authentication failed: No user or session returned")
            return None
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {e}")
        return None

def test_chat_endpoint(token, message="Hello, can you help me with a simple test?"):
    """Test the /prompt endpoint with authenticated request"""
    try:
        print(f"\n[CHAT] Testing chat endpoint with message: '{message}'")
        
        # Prepare request
        url = f"{BACKEND_URL}/prompt"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }
        
        print(f"[REQUEST] Sending request to: {url}")
        print(f"[PAYLOAD] Payload: {json.dumps(payload, indent=2)}")
        
        # Make request with timeout
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"[STATUS] Response Status: {response.status_code}")
        print(f"[HEADERS] Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"[SUCCESS] Chat response received:")
                print(f"[AI_RESPONSE] AI Response: {data.get('response', 'No response field')}")
                print(f"[CHAT_ID] Chat ID: {data.get('chat_id', 'No chat_id field')}")
                return True
            except json.JSONDecodeError:
                print(f"[ERROR] JSON decode error. Raw response: {response.text}")
                return False
        else:
            print(f"[FAILED] Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"[ERROR_DATA] Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"[RAW_ERROR] Raw Error Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[TIMEOUT] Request timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"[ERROR] Request error: {e}")
        return False

def main():
    """Main test function"""
    print("[TEST] PRODUCTION CHAT FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Get credentials from command line or prompt
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = input("Enter email: ")
        password = input("Enter password: ")
    
    # Test authentication
    token = authenticate_user(email, password)
    if not token:
        print("[ERROR] Authentication failed. Cannot proceed with chat test.")
        return False
    
    # Test chat endpoint
    success = test_chat_endpoint(token)
    
    if success:
        print("\n[PASSED] CHAT FUNCTIONALITY TEST PASSED!")
        print("[SUCCESS] OpenAI integration is working correctly")
        return True
    else:
        print("\n[FAILED] CHAT FUNCTIONALITY TEST FAILED!")
        print("[ERROR] OpenAI integration is not working")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
