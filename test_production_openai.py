#!/usr/bin/env python3
"""
Test OpenAI integration in production environment
"""

import requests
import json
import time

def test_production_openai_with_pump_query():
    """Test production /prompt endpoint with pump query using valid auth"""
    print("=== TESTING PRODUCTION OPENAI WITH PUMP QUERY ===\n")
    
    backend_url = "https://patchai-backend.onrender.com"
    
    # First, let's test the health endpoint to see OpenAI status
    print("[STEP 1] Checking backend health...")
    try:
        health_response = requests.get(f"{backend_url}/health", timeout=10)
        health_data = health_response.json()
        
        print(f"Backend Status: {health_data['status']}")
        print(f"OpenAI Service: {health_data['services']['openai']}")
        print(f"OpenAI Requests: {health_data['application']['openai_requests']}")
        print(f"OpenAI Errors: {health_data['application']['openai_errors']}")
        
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False
    
    # Test the /prompt endpoint without auth to see the specific error
    print("\n[STEP 2] Testing /prompt endpoint without auth...")
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "What are the specs for a 4x6-13 transfer pump?"}
            ]
        }
        
        response = requests.post(
            f"{backend_url}/prompt",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 500:
            print("\n[CRITICAL] 500 Internal Server Error detected!")
            print("This confirms the production issue with pump queries.")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"Error Details: {error_data}")
            except:
                print("Could not parse error response as JSON")
                
        elif response.status_code == 403:
            print("\n[OK] Expected 403 - authentication working correctly")
        
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return False
    
    # Test with a non-pump query to see if it's pump-specific
    print("\n[STEP 3] Testing with non-pump query...")
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "Hello, how are you today?"}
            ]
        }
        
        response = requests.post(
            f"{backend_url}/prompt",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Non-pump query status: {response.status_code}")
        if response.status_code == 500:
            print("[CRITICAL] 500 error also occurs with non-pump queries!")
        elif response.status_code == 403:
            print("[OK] Expected 403 for non-pump query too")
            
    except Exception as e:
        print(f"[ERROR] Non-pump query failed: {e}")
    
    # Check health again to see if error count increased
    print("\n[STEP 4] Checking health after tests...")
    try:
        health_response = requests.get(f"{backend_url}/health", timeout=10)
        health_data = health_response.json()
        
        print(f"OpenAI Requests: {health_data['application']['openai_requests']}")
        print(f"OpenAI Errors: {health_data['application']['openai_errors']}")
        print(f"Total Errors: {health_data['application']['errors_total']}")
        
    except Exception as e:
        print(f"[ERROR] Final health check failed: {e}")
    
    return True

def test_openai_endpoint_directly():
    """Test if there's a direct OpenAI test endpoint"""
    print("\n=== TESTING DIRECT OPENAI ENDPOINT ===")
    
    backend_url = "https://patchai-backend.onrender.com"
    
    # Check if there's a test endpoint
    test_endpoints = [
        "/test-openai",
        "/openai/test", 
        "/debug/openai",
        "/api/test"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=10)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code != 404:
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    test_production_openai_with_pump_query()
    test_openai_endpoint_directly()
