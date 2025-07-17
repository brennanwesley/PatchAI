#!/usr/bin/env python3
"""
Direct test of OpenAI integration using a valid JWT token
Tests the /prompt endpoint to verify if OpenAI is working
"""

import requests
import json
import sys

# Production backend URL
BACKEND_URL = "https://patchai-backend.onrender.com"

def test_with_jwt_token(jwt_token, message="Hello, this is a test message. Please respond with 'OpenAI is working correctly'."):
    """Test the /prompt endpoint with a JWT token"""
    try:
        print(f"[CHAT] Testing chat endpoint with message: '{message}'")
        
        # Prepare request
        url = f"{BACKEND_URL}/prompt"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
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

def test_health_endpoint():
    """Test the health endpoint to see current OpenAI status"""
    try:
        print("[HEALTH] Testing health endpoint...")
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[HEALTH] OpenAI Status: {data.get('services', {}).get('openai', 'unknown')}")
            print(f"[HEALTH] OpenAI Requests: {data.get('application', {}).get('openai_requests', 'unknown')}")
            print(f"[HEALTH] OpenAI Errors: {data.get('application', {}).get('openai_errors', 'unknown')}")
            return data
        else:
            print(f"[HEALTH] Health check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"[HEALTH] Health check error: {e}")
        return None

def main():
    """Main test function"""
    print("[TEST] DIRECT OPENAI INTEGRATION TEST")
    print("=" * 50)
    
    # Test health endpoint first
    health_data = test_health_endpoint()
    
    # Get JWT token from command line
    if len(sys.argv) >= 2:
        jwt_token = sys.argv[1]
    else:
        jwt_token = input("Enter JWT token: ")
    
    if not jwt_token:
        print("[ERROR] No JWT token provided")
        return False
    
    # Test chat endpoint
    success = test_with_jwt_token(jwt_token)
    
    if success:
        print("\n[PASSED] OPENAI INTEGRATION TEST PASSED!")
        print("[SUCCESS] OpenAI is working correctly")
        return True
    else:
        print("\n[FAILED] OPENAI INTEGRATION TEST FAILED!")
        print("[ERROR] OpenAI integration is not working")
        
        # Show health data for debugging
        if health_data:
            print(f"[DEBUG] Health data: {json.dumps(health_data.get('application', {}), indent=2)}")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
