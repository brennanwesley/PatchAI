#!/usr/bin/env python3
"""
Simple API test script - no interactive input required
"""

import requests
import json

def test_openai_endpoint(base_url):
    """Test the OpenAI integration endpoint"""
    url = f"{base_url}/prompt"
    
    test_message = {
        "messages": [
            {
                "role": "user", 
                "content": "Hello! Can you explain what PatchAI does in one sentence?"
            }
        ]
    }
    
    print(f"Testing: {url}")
    print(f"Payload: {json.dumps(test_message, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=test_message, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS!")
            print(f"Response: {data['response']}")
            return True
        else:
            print(f"ERROR!")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"CONNECTION ERROR: {e}")
        return False

def test_health_check(base_url):
    """Test the health check endpoint"""
    url = f"{base_url}/"
    
    print(f"Testing health check: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Health Check OK: {data}")
            return True
        else:
            print(f"Health Check Failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Health Check Error: {e}")
        return False

if __name__ == "__main__":
    print("=== PatchAI API Test ===\n")
    
    # Test with a common Render URL pattern
    # You'll need to replace this with your actual URL
    render_url = "https://patchai-backend.onrender.com"  # Update this with your actual URL
    
    print("1. Testing Health Check...")
    health_ok = test_health_check(render_url)
    print()
    
    print("2. Testing OpenAI Integration...")
    api_ok = test_openai_endpoint(render_url)
    print()
    
    if health_ok and api_ok:
        print("All tests passed! Your API is working correctly.")
    else:
        print("Some tests failed. Check the output above for details.")
        print("\nTroubleshooting:")
        print("1. Make sure your Render service URL is correct")
        print("2. Verify your OPENAI_API_KEY is set in Render environment variables")
        print("3. Check the Render logs for any error messages")
