#!/usr/bin/env python3
"""
Simple debug test without Unicode characters
"""

import requests
import json

def test_debug_endpoint():
    url = "https://patchai-backend.onrender.com/debug"
    
    print("Testing debug endpoint...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Debug Information:")
            print(json.dumps(data, indent=2))
            
            # Check specific issues
            if not data.get("openai_key_exists"):
                print("\nISSUE: OpenAI API key is not set or is None")
            elif data.get("openai_key_length", 0) < 10:
                print(f"\nISSUE: OpenAI API key seems too short (length: {data.get('openai_key_length')})")
            elif not data.get("openai_client_initialized"):
                error = data.get("initialization_error", "Unknown error")
                print(f"\nISSUE: OpenAI client failed to initialize: {error}")
            else:
                print("\nSUCCESS: OpenAI configuration looks good!")
                
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_debug_endpoint()
