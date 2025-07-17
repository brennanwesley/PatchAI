#!/usr/bin/env python3
"""
Test OpenAI API key directly to verify if it's working
"""

import os
import sys
from openai import OpenAI

def test_openai_key(api_key):
    """Test if OpenAI API key is valid and working"""
    try:
        print(f"[TEST] Testing OpenAI API key: {api_key[:20]}...{api_key[-10:]}")
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Make a simple test request
        print("[REQUEST] Making test request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Say 'API key is working correctly'"}
            ],
            max_tokens=50,
            timeout=30
        )
        
        if response and response.choices:
            ai_response = response.choices[0].message.content
            print(f"[SUCCESS] OpenAI API Response: {ai_response}")
            return True
        else:
            print("[ERROR] Empty response from OpenAI API")
            return False
            
    except Exception as e:
        error_type = type(e).__name__
        print(f"[ERROR] OpenAI API test failed: {error_type}: {str(e)}")
        return False

def main():
    """Main test function"""
    print("[TEST] OPENAI API KEY VALIDATION TEST")
    print("=" * 50)
    
    # Get API key from command line or environment
    if len(sys.argv) >= 2:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key = input("Enter OpenAI API key: ")
    
    if not api_key:
        print("[ERROR] No OpenAI API key provided")
        return False
    
    # Test the API key
    success = test_openai_key(api_key)
    
    if success:
        print("\n[PASSED] OpenAI API key is valid and working!")
        return True
    else:
        print("\n[FAILED] OpenAI API key test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
