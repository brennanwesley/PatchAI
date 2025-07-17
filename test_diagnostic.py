#!/usr/bin/env python3
"""
Test the diagnostic endpoint to get detailed OpenAI error information
"""

import requests
import json

def test_diagnostic_endpoint():
    """Test the diagnostic endpoint"""
    try:
        print("[TEST] Testing diagnostic endpoint...")
        
        url = "https://patchai-backend.onrender.com/diagnostic/openai"
        response = requests.get(url, timeout=60)
        
        print(f"[STATUS] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print(f"[SUCCESS] OpenAI diagnostic test passed!")
                print(f"[RESPONSE] {data.get('response', 'No response')}")
            else:
                print(f"[FAILED] OpenAI diagnostic test failed!")
                print(f"[ERROR_CATEGORY] {data.get('error_category', 'Unknown')}")
                print(f"[ERROR_TYPE] {data.get('error_type', 'Unknown')}")
                print(f"[ERROR_MESSAGE] {data.get('error_message', 'Unknown')}")
                print(f"[TRACEBACK] {data.get('traceback', 'No traceback')}")
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    test_diagnostic_endpoint()
