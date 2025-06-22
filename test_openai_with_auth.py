#!/usr/bin/env python3
"""
Test OpenAI API Response with Authentication
Instructions for testing with real JWT token
"""

import requests
import json
from datetime import datetime

# Backend URL
BACKEND_URL = "https://patchai-backend.onrender.com"

def test_openai_with_auth(jwt_token):
    """Test OpenAI response with authentication"""
    print("Testing OpenAI API Response with Authentication")
    print("=" * 60)
    
    # Test payload
    payload = {
        "messages": [
            {
                "role": "user", 
                "content": "Hello Patch! Can you help me with oilfield operations? Please give me a brief response."
            }
        ],
        "chat_id": f"test_chat_{int(datetime.now().timestamp())}"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    print(f"Sending authenticated request to: {BACKEND_URL}/prompt")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Using JWT token: {jwt_token[:50]}...")
    print()
    
    try:
        print("Sending request to OpenAI via backend...")
        response = requests.post(
            f"{BACKEND_URL}/prompt",
            json=payload,
            headers=headers,
            timeout=60  # Longer timeout for OpenAI
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
        
        if response.status_code == 200:
            print("SUCCESS: OpenAI API is working!")
            response_data = response.json()
            print(f"AI Response: {response_data.get('response', 'No response field')}")
            print(f"Chat ID: {response_data.get('chat_id', 'No chat_id field')}")
            return True
            
        elif response.status_code == 401:
            print("ERROR: Invalid JWT token")
            response_data = response.json()
            print(f"Error: {response_data.get('detail', 'Unknown auth error')}")
            
        elif response.status_code == 500:
            print("ERROR: Internal server error")
            try:
                response_data = response.json()
                print(f"Error: {response_data.get('detail', 'Unknown server error')}")
            except:
                print(f"Raw response: {response.text}")
                
        elif response.status_code == 503:
            print("ERROR: Service unavailable - OpenAI client not initialized")
            
        else:
            print(f"ERROR: Unexpected status: {response.status_code}")
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
                
        return False
        
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out - OpenAI may be slow")
        return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection error - backend may be down")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    print("OpenAI Integration Test")
    print("=" * 60)
    print()
    print("To test with authentication:")
    print("1. Open your PatchAI frontend in browser")
    print("2. Log in with your account")
    print("3. Open browser dev tools (F12)")
    print("4. Go to Application/Storage tab")
    print("5. Find localStorage -> supabase.auth.token")
    print("6. Copy the access_token value")
    print("7. Paste it when prompted below")
    print()
    
    jwt_token = input("Enter your JWT token (or 'skip' to skip): ").strip()
    
    if jwt_token.lower() == 'skip':
        print("Skipping authenticated test")
        return
    
    if not jwt_token:
        print("No token provided")
        return
    
    print()
    success = test_openai_with_auth(jwt_token)
    
    print()
    print("=" * 60)
    if success:
        print("RESULT: OpenAI integration is working correctly!")
        print("Your frontend should be able to get AI responses.")
    else:
        print("RESULT: OpenAI integration has issues.")
        print("Check backend logs and OpenAI API key configuration.")

if __name__ == "__main__":
    main()
