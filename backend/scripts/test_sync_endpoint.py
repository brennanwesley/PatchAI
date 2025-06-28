#!/usr/bin/env python3
"""
Test the /payments/sync-subscription endpoint to debug frontend Sync button issues
"""

import os
import sys
import asyncio
import requests
import json
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv('BACKEND_URL', 'https://patchai-backend.onrender.com')

async def test_sync_endpoint():
    """Test the sync subscription endpoint with proper authentication"""
    print("TESTING SYNC SUBSCRIPTION ENDPOINT")
    print("=" * 40)
    
    # Test with testuser3@email.com (we just fixed their sync)
    test_email = "testuser3@email.com"
    
    print(f"[TEST] Testing sync endpoint for: {test_email}")
    print(f"[TEST] Backend URL: {API_BASE_URL}")
    
    # Get user auth token (simulate frontend auth)
    try:
        # For testing, we'll simulate the request format that frontend sends
        test_data = {
            "email": None  # Frontend sends null for current user
        }
        
        print(f"[TEST] Request payload: {json.dumps(test_data, indent=2)}")
        print(f"[TEST] Endpoint: {API_BASE_URL}/payments/sync-subscription")
        
        # Test without auth first to see the error
        print(f"\n[TEST 1] Testing without authentication...")
        response = requests.post(
            f"{API_BASE_URL}/payments/sync-subscription",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"[TEST 1] Status Code: {response.status_code}")
        print(f"[TEST 1] Response: {response.text}")
        
        # Test the endpoint structure
        print(f"\n[TEST 2] Testing endpoint availability...")
        health_response = requests.get(f"{API_BASE_URL}/health")
        print(f"[TEST 2] Health check: {health_response.status_code}")
        
        # Test with different request formats
        print(f"\n[TEST 3] Testing with empty body...")
        empty_response = requests.post(
            f"{API_BASE_URL}/payments/sync-subscription",
            json={},
            headers={'Content-Type': 'application/json'}
        )
        print(f"[TEST 3] Status Code: {empty_response.status_code}")
        print(f"[TEST 3] Response: {empty_response.text}")
        
        # Check if the endpoint exists in routes
        print(f"\n[TEST 4] Testing endpoint discovery...")
        try:
            routes_response = requests.get(f"{API_BASE_URL}/docs")
            print(f"[TEST 4] Docs endpoint: {routes_response.status_code}")
        except:
            print(f"[TEST 4] Docs endpoint not available")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
    
    print(f"\n[ANALYSIS] Frontend Sync Button Issues:")
    print(f"  1. Authentication: Frontend must pass valid JWT token")
    print(f"  2. Request Format: Must match SyncSubscriptionRequest model")
    print(f"  3. Error Handling: Frontend needs better error messages")
    print(f"  4. Backend Response: Check if sync actually works")

if __name__ == "__main__":
    asyncio.run(test_sync_endpoint())
