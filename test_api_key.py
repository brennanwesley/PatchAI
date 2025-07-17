#!/usr/bin/env python3
"""
Simple script to test if an OpenAI API key is valid
"""

import requests
import sys

def test_openai_key(api_key):
    """Test if OpenAI API key is valid"""
    try:
        print(f"Testing OpenAI API key: {api_key[:20]}...{api_key[-10:]}")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API KEY IS VALID!")
            print("OpenAI API is accessible and working")
            return True
        elif response.status_code == 401:
            print("❌ API KEY IS INVALID!")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            except:
                print("Error: Invalid API key")
            return False
        else:
            print(f"❌ UNEXPECTED ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ REQUEST FAILED: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_api_key.py YOUR_API_KEY")
        print("Example: python test_api_key.py sk-1234567890abcdef...")
        return
    
    api_key = sys.argv[1]
    test_openai_key(api_key)

if __name__ == "__main__":
    main()
