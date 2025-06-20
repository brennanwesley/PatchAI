#!/usr/bin/env python3
"""
Test the /prompt endpoint with a sample message
"""

import requests
import json

def test_prompt_endpoint():
    url = "https://patchai-backend.onrender.com/prompt"
    
    print("Testing /prompt endpoint...")
    print(f"URL: {url}")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Hello! What is PatchAI?"
            }
        ]
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[SUCCESS] Response from OpenAI:")
            print(json.dumps(data, indent=2))
            print("\n[SUCCESS] Backend is fully operational with OpenAI integration!")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection Error: {e}")
        print("Please check if the backend service is running and accessible.")

if __name__ == "__main__":
    test_prompt_endpoint()
