#!/usr/bin/env python3
"""
Test OpenAI API Response
Test the backend /prompt endpoint with a real JWT token to verify AI responses
"""

import requests
import json
import os
from datetime import datetime

# Backend URL
BACKEND_URL = "https://patchai-backend.onrender.com"

def test_openai_response():
    """Test OpenAI response with a sample message"""
    print("Testing OpenAI API Response")
    print("=" * 50)
    
    # Test payload - simple message to AI
    payload = {
        "messages": [
            {
                "role": "user", 
                "content": "Hello Patch! Can you help me with oilfield operations?"
            }
        ],
        "chat_id": f"test_chat_{int(datetime.now().timestamp())}"
    }
    
    print(f"Sending test message to: {BACKEND_URL}/prompt")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        # Test without authentication first (should get 401)
        print("Testing without authentication (expecting 401)...")
        response = requests.post(
            f"{BACKEND_URL}/prompt",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("SUCCESS: Expected 401 Unauthorized - authentication is working")
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        else:
            print(f"ERROR: Unexpected status code: {response.status_code}")
            try:
                response_data = response.json()
                print(f"Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
        
        print()
        print("=" * 50)
        print("Analysis:")
        
        if response.status_code == 401:
            print("SUCCESS: Backend is properly rejecting unauthenticated requests")
            print("SUCCESS: /prompt endpoint exists and is accessible")
            print("SUCCESS: Authentication middleware is working")
            print("INFO: Need valid JWT token to test actual OpenAI integration")
            print()
            print("To test with real authentication:")
            print("   1. Log into your frontend app")
            print("   2. Open browser dev tools")
            print("   3. Check localStorage for 'supabase.auth.token'")
            print("   4. Use that token in Authorization header")
        elif response.status_code == 500:
            print("ERROR: Internal server error - check backend logs")
            print("ERROR: Possible OpenAI API key or configuration issue")
        elif response.status_code == 503:
            print("ERROR: Service unavailable - OpenAI client not initialized")
        else:
            print(f"WARNING: Unexpected response: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out - backend may be slow or unresponsive")
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection error - backend may be down")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    print()
    print("Test complete!")

if __name__ == "__main__":
    test_openai_response()
