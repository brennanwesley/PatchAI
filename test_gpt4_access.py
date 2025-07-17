#!/usr/bin/env python3
"""
Test if the OpenAI API key has access to GPT-4 specifically
"""

import requests
import json
import sys

def test_gpt4_access(api_key):
    """Test if API key can access GPT-4 model"""
    try:
        print(f"Testing GPT-4 access with API key: {api_key[:20]}...{api_key[-10:]}")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Test the exact same request the backend makes
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'GPT-4 is working correctly'."}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        print("Making GPT-4 chat completion request...")
        response = requests.post(
            'https://api.openai.com/v1/chat/completions', 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[SUCCESS] GPT-4 access is working!")
            try:
                data = response.json()
                ai_response = data['choices'][0]['message']['content']
                print(f"AI Response: {ai_response}")
            except:
                print("Response received but couldn't parse content")
            return True
        else:
            print(f"[FAILED] GPT-4 access failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_gpt4_access.py YOUR_API_KEY")
        return
    
    api_key = sys.argv[1]
    test_gpt4_access(api_key)

if __name__ == "__main__":
    main()
