#!/usr/bin/env python3
"""
Test script to debug the 500 error in chat creation
"""

import requests
import json

# Test data that mimics what the frontend sends
test_payload = {
    "chat_id": "chat_1750564188_abc123def",
    "title": "hey patch ready to work?",
    "messages": [
        {
            "role": "user",
            "content": "hey patch ready to work?"
        }
    ]
}

# Backend URL
backend_url = "https://patchai-backend.onrender.com"

def test_chat_creation():
    """Test the /history endpoint that's failing"""
    try:
        print("Testing chat creation endpoint...")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        # Make the request
        response = requests.post(
            f"{backend_url}/history",
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token"  # This will fail auth but we want to see the error
            }
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def test_health():
    """Test the health endpoint"""
    try:
        print("Testing health endpoint...")
        response = requests.get(f"{backend_url}/health")
        
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health Data: {json.dumps(health_data, indent=2)}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Health test failed: {e}")
        return False

if __name__ == "__main__":
    print("Backend API Test")
    print("=" * 50)
    
    # Test health first
    if test_health():
        print("\n" + "=" * 50)
        print("Testing Chat Creation")
        test_chat_creation()
    else:
        print("Backend health check failed")
    
    print("\n" + "=" * 50)
    print("Test complete!")
