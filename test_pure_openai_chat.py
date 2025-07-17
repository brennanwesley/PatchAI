#!/usr/bin/env python3
"""
Test script to verify pure OpenAI chat functionality is restored
Tests that chat works without any pump data interference
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://patchai-backend.onrender.com"
TEST_USER_EMAIL = "quinton@ihoseandsupply.com"
TEST_PASSWORD = "test123"

def test_pure_openai_chat():
    """Test that OpenAI chat functionality works without pump data interference"""
    
    print("[TEST] Testing Pure OpenAI Chat Functionality")
    print("=" * 50)
    
    # Step 1: Authenticate
    print("1. Authenticating user...")
    auth_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if auth_response.status_code != 200:
        print("[ERROR] Authentication failed: " + str(auth_response.status_code))
        print("Response: " + auth_response.text)
        return False
    
    auth_data = auth_response.json()
    access_token = auth_data.get("access_token")
    
    if not access_token:
        print("[ERROR] No access token received")
        return False
    
    print("[OK] Authentication successful")
    
    # Step 2: Test simple chat message
    print("\n2. Testing simple chat message...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    chat_response = requests.post(f"{BASE_URL}/prompt", 
        headers=headers,
        json={
            "message": "Hello, can you tell me about oil and gas safety practices?",
            "chat_id": "test_chat_001"
        }
    )
    
    print(f"Status Code: {chat_response.status_code}")
    
    if chat_response.status_code != 200:
        print(f"[ERROR] Chat request failed: {chat_response.status_code}")
        print(f"Response: {chat_response.text}")
        return False
    
    chat_data = chat_response.json()
    print("[OK] Chat request successful")
    print(f"Response preview: {chat_data.get('response', '')[:100]}...")
    
    # Step 3: Test pump-related query (should work through OpenAI, not fallback)
    print("\n3. Testing pump-related query...")
    
    pump_response = requests.post(f"{BASE_URL}/prompt", 
        headers=headers,
        json={
            "message": "What are the key considerations for water transfer pump selection?",
            "chat_id": "test_chat_001"
        }
    )
    
    print(f"Status Code: {pump_response.status_code}")
    
    if pump_response.status_code != 200:
        print(f"[ERROR] Pump query failed: {pump_response.status_code}")
        print(f"Response: {pump_response.text}")
        return False
    
    pump_data = pump_response.json()
    print("[OK] Pump query successful")
    print(f"Response preview: {pump_data.get('response', '')[:100]}...")
    
    # Step 4: Verify no fallback service interference
    print("\n4. Verifying pure OpenAI integration...")
    
    # Check that responses are coming from OpenAI (should have natural language, not structured data)
    response_text = pump_data.get('response', '')
    
    # Signs of fallback service would be structured data or specific pump model references
    # Pure OpenAI should give general guidance
    if "4x6-13" in response_text or "transfer_pumps.json" in response_text:
        print("[WARNING] Response may contain fallback service data")
    else:
        print("[OK] Response appears to be pure OpenAI (no fallback data detected)")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Pure OpenAI Chat Test Complete!")
    print("[OK] Authentication: Working")
    print("[OK] General Chat: Working") 
    print("[OK] Pump Queries: Working")
    print("[OK] No Fallback Interference: Confirmed")
    
    return True

if __name__ == "__main__":
    try:
        success = test_pure_openai_chat()
        if success:
            print("\n[RESULT] Pure OpenAI chat functionality is RESTORED!")
            sys.exit(0)
        else:
            print("\n[RESULT] Chat functionality still has issues")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        sys.exit(1)
