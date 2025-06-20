#!/usr/bin/env python3
"""
Test the debug endpoint to check environment variables
"""

import requests
import json
import time

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
                print("\n❌ ISSUE: OpenAI API key is not set or is None")
            elif data.get("openai_key_length", 0) < 10:
                print(f"\n❌ ISSUE: OpenAI API key seems too short (length: {data.get('openai_key_length')})")
            elif not data.get("openai_client_initialized"):
                print("\n❌ ISSUE: OpenAI client failed to initialize despite key being present")
            else:
                print("\n✅ OpenAI configuration looks good!")
                
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")
        print("The service might still be deploying. Wait a minute and try again.")

if __name__ == "__main__":
    test_debug_endpoint()
