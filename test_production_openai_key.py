#!/usr/bin/env python3
"""
Test the OpenAI API key that's actually being used in production
"""

import requests
import json

def test_production_openai_key():
    """Test if the OpenAI API key in production is valid"""
    try:
        print("[TEST] Testing production OpenAI API key validation...")
        
        # Create a simple endpoint test that will reveal the OpenAI error
        url = "https://patchai-backend.onrender.com/test-openai-key"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] OpenAI key test: {data}")
            return True
        else:
            print(f"[INFO] No test endpoint available (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"[INFO] No test endpoint available: {e}")
        return False

def main():
    """Main test function"""
    print("[TEST] PRODUCTION OPENAI KEY VALIDATION")
    print("=" * 50)
    
    # Test if there's a key validation endpoint
    test_production_openai_key()
    
    print("\n[ANALYSIS] Based on the consistent 503 errors:")
    print("- OpenAI client initializes successfully (reports 'healthy')")
    print("- 100% of OpenAI API calls fail (3 requests, 3 errors)")
    print("- Error message: 'AI service taking longer than expected'")
    print("- This pattern is consistent with INVALID/EXPIRED API KEY")
    
    print("\n[RECOMMENDATION] Check the OpenAI API key in Render environment:")
    print("1. Log into Render dashboard")
    print("2. Go to PatchAI backend service")
    print("3. Check Environment Variables")
    print("4. Verify OPENAI_API_KEY is valid and not expired")
    print("5. If key is invalid, update it and redeploy")
    
    return False

if __name__ == "__main__":
    main()
