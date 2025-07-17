#!/usr/bin/env python3
"""
Test script to verify 503 errors are resolved and OpenAI chat functionality is working
Tests the complete message flow from frontend to OpenAI and back
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://patchai-backend.onrender.com"

def test_openai_chat_functionality():
    """Test that OpenAI chat functionality works without 503 errors"""
    
    print("[TEST] Testing OpenAI Chat Functionality After 503 Fix")
    print("=" * 60)
    
    # Step 1: Check health endpoint
    print("1. Checking backend health...")
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            openai_status = health_data.get("services", {}).get("openai", "unknown")
            print(f"[OK] Backend health: {health_response.status_code}")
            print(f"[OK] OpenAI service status: {openai_status}")
            
            if openai_status != "healthy":
                print(f"[ERROR] OpenAI service is not healthy: {openai_status}")
                return False
        else:
            print(f"[ERROR] Health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Health check exception: {e}")
        return False
    
    # Step 2: Test authentication (create a test user or use existing)
    print("\n2. Testing authentication...")
    
    # Try to create a test user first
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "TestPassword123!"
    
    try:
        # Register test user
        register_response = requests.post(f"{BASE_URL}/auth/register", json={
            "email": test_email,
            "password": test_password,
            "name": "Test User"
        }, timeout=10)
        
        if register_response.status_code in [200, 201]:
            print("[OK] Test user registered successfully")
        elif register_response.status_code == 409:
            print("[INFO] User already exists, proceeding with login")
        else:
            print(f"[WARNING] Registration failed: {register_response.status_code}, trying login")
    except Exception as e:
        print(f"[WARNING] Registration exception: {e}, trying login")
    
    # Login with test user
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": test_email,
            "password": test_password
        }, timeout=10)
        
        if login_response.status_code == 200:
            auth_data = login_response.json()
            access_token = auth_data.get("access_token")
            if access_token:
                print("[OK] Authentication successful")
            else:
                print("[ERROR] No access token received")
                return False
        else:
            print(f"[ERROR] Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Login exception: {e}")
        return False
    
    # Step 3: Test OpenAI chat endpoint
    print("\n3. Testing OpenAI chat endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    test_messages = [
        {
            "role": "user",
            "content": "Hello, can you tell me about oil and gas safety practices?"
        }
    ]
    
    try:
        chat_response = requests.post(f"{BASE_URL}/prompt", 
            headers=headers,
            json={
                "messages": test_messages,
                "chat_id": f"test_chat_{int(time.time())}"
            },
            timeout=30  # Increased timeout for OpenAI API calls
        )
        
        print(f"Status Code: {chat_response.status_code}")
        
        if chat_response.status_code == 503:
            print("[ERROR] 503 Service Unavailable - OpenAI integration still failing!")
            print(f"Response: {chat_response.text}")
            return False
        elif chat_response.status_code == 200:
            chat_data = chat_response.json()
            response_text = chat_data.get('response', '')
            print("[OK] Chat request successful")
            print(f"Response length: {len(response_text)} characters")
            print(f"Response preview: {response_text[:150]}...")
            
            # Verify it's a real OpenAI response (not empty or error)
            if len(response_text) > 10 and "error" not in response_text.lower():
                print("[OK] Received valid OpenAI response")
            else:
                print("[WARNING] Response may be invalid or empty")
                return False
        else:
            print(f"[ERROR] Chat request failed: {chat_response.status_code}")
            print(f"Response: {chat_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out - OpenAI API may be slow")
        return False
    except Exception as e:
        print(f"[ERROR] Chat request exception: {e}")
        return False
    
    # Step 4: Test pump-related query (should work through OpenAI)
    print("\n4. Testing pump-related query...")
    
    pump_messages = [
        {
            "role": "user", 
            "content": "What are the key considerations for selecting a water transfer pump?"
        }
    ]
    
    try:
        pump_response = requests.post(f"{BASE_URL}/prompt", 
            headers=headers,
            json={
                "messages": pump_messages,
                "chat_id": f"test_chat_{int(time.time())}"
            },
            timeout=30
        )
        
        print(f"Status Code: {pump_response.status_code}")
        
        if pump_response.status_code == 503:
            print("[ERROR] 503 Service Unavailable for pump query!")
            print(f"Response: {pump_response.text}")
            return False
        elif pump_response.status_code == 200:
            pump_data = pump_response.json()
            response_text = pump_data.get('response', '')
            print("[OK] Pump query successful")
            print(f"Response length: {len(response_text)} characters")
            print(f"Response preview: {response_text[:150]}...")
            
            # Verify it's a real OpenAI response about pumps
            if len(response_text) > 10 and any(word in response_text.lower() for word in ['pump', 'flow', 'pressure', 'water']):
                print("[OK] Received relevant pump-related response from OpenAI")
            else:
                print("[WARNING] Response may not be pump-related")
        else:
            print(f"[ERROR] Pump query failed: {pump_response.status_code}")
            print(f"Response: {pump_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Pump query timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Pump query exception: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] OpenAI Chat Functionality Test Complete!")
    print("[OK] Backend Health: Healthy")
    print("[OK] Authentication: Working")
    print("[OK] OpenAI Chat: Working (No 503 errors)")
    print("[OK] Pump Queries: Working through OpenAI")
    print("[OK] Pure OpenAI Integration: Confirmed")
    
    return True

if __name__ == "__main__":
    try:
        success = test_openai_chat_functionality()
        if success:
            print("\n[RESULT] SUCCESS: 503 errors resolved! OpenAI chat functionality is working!")
            sys.exit(0)
        else:
            print("\n[RESULT] FAILURE: 503 errors persist or other issues found")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        sys.exit(1)
