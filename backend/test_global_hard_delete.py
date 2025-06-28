#!/usr/bin/env python3
"""
Test script to execute global hard delete of all chat messages for all users
CRITICAL: This will permanently delete ALL chat history for ALL users
"""

import requests
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_global_hard_delete():
    """Execute global hard delete via API endpoint"""
    
    # Get backend URL
    backend_url = os.getenv('BACKEND_URL', 'https://patchai-backend.onrender.com')
    
    # Test JWT token (you'll need to replace this with a valid token)
    # For testing, we can use the test endpoint or get a token from the frontend
    test_token = os.getenv('TEST_JWT_TOKEN')
    
    if not test_token:
        print("❌ ERROR: TEST_JWT_TOKEN environment variable not set")
        print("Please set a valid JWT token in your .env file or environment")
        return False
    
    # Prepare request
    url = f"{backend_url}/admin/global-hard-delete"
    headers = {
        'Authorization': f'Bearer {test_token}',
        'Content-Type': 'application/json'
    }
    
    print("🚨 WARNING: This will permanently delete ALL chat history for ALL users!")
    print("🚨 This action cannot be undone!")
    print(f"🚨 Target: {url}")
    
    # Ask for confirmation
    confirmation = input("\nType 'DELETE ALL MESSAGES' to confirm: ")
    if confirmation != 'DELETE ALL MESSAGES':
        print("❌ Operation cancelled - confirmation not provided")
        return False
    
    try:
        print("\n🔄 Executing global hard delete...")
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Global hard delete completed')}")
            print(f"📊 Status: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚨 GLOBAL HARD DELETE TEST SCRIPT")
    print("=" * 50)
    
    success = test_global_hard_delete()
    
    if success:
        print("\n✅ Global hard delete completed successfully")
        print("🔄 All users will now start with fresh chat sessions")
    else:
        print("\n❌ Global hard delete failed")
        
    sys.exit(0 if success else 1)
