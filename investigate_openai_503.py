#!/usr/bin/env python3
"""
Investigate OpenAI 503 errors in production
This script will help identify the root cause of persistent OpenAI unavailability
"""

import requests
import json
import sys

def test_backend_health():
    """Test backend health and OpenAI service status"""
    print("=== BACKEND HEALTH STATUS ===")
    try:
        response = requests.get('https://patchai-backend.onrender.com/health')
        health_data = response.json()
        
        print(f"Overall Status: {health_data.get('status', 'unknown')}")
        print(f"OpenAI Service: {health_data.get('services', {}).get('openai', 'unknown')}")
        print(f"OpenAI Requests: {health_data.get('application', {}).get('openai_requests', 0)}")
        print(f"OpenAI Errors: {health_data.get('application', {}).get('openai_errors', 0)}")
        print(f"Total Errors: {health_data.get('application', {}).get('errors_total', 0)}")
        print(f"Uptime: {health_data.get('uptime_seconds', 0)} seconds")
        
        return health_data
        
    except Exception as e:
        print(f"ERROR: Failed to get health status: {e}")
        return None

def test_simple_query():
    """Test a simple query without authentication to see OpenAI response"""
    print("\n=== TESTING SIMPLE QUERY (NO AUTH) ===")
    try:
        test_response = requests.post('https://patchai-backend.onrender.com/prompt', 
                                    json={'messages': [{'role': 'user', 'content': 'Hello'}]})
        print(f"Status Code: {test_response.status_code}")
        print(f"Response Headers: {dict(test_response.headers)}")
        print(f"Response Body: {test_response.text}")
        
        return test_response
        
    except Exception as e:
        print(f"ERROR: Failed to test simple query: {e}")
        return None

def test_pump_query():
    """Test a pump-specific query without authentication"""
    print("\n=== TESTING PUMP QUERY (NO AUTH) ===")
    try:
        pump_response = requests.post('https://patchai-backend.onrender.com/prompt', 
                                    json={'messages': [{'role': 'user', 'content': 'Tell me about 4x6-13 transfer pumps'}]})
        print(f"Status Code: {pump_response.status_code}")
        print(f"Response Headers: {dict(pump_response.headers)}")
        print(f"Response Body: {pump_response.text}")
        
        return pump_response
        
    except Exception as e:
        print(f"ERROR: Failed to test pump query: {e}")
        return None

def analyze_503_error():
    """Analyze the specific 503 error pattern"""
    print("\n=== ANALYZING 503 ERROR PATTERN ===")
    
    # Test multiple requests to see if it's consistent
    for i in range(3):
        print(f"\nTest {i+1}/3:")
        try:
            response = requests.post('https://patchai-backend.onrender.com/prompt', 
                                   json={'messages': [{'role': 'user', 'content': f'Test message {i+1}'}]})
            print(f"  Status: {response.status_code}")
            if response.status_code == 503:
                try:
                    error_data = response.json()
                    print(f"  Error Detail: {error_data.get('detail', 'No detail')}")
                except:
                    print(f"  Raw Response: {response.text}")
        except Exception as e:
            print(f"  ERROR: {e}")

def main():
    """Main investigation function"""
    print("INVESTIGATING OPENAI 503 ERRORS")
    print("=" * 50)
    
    # Step 1: Check backend health
    health_data = test_backend_health()
    
    # Step 2: Test simple query
    simple_response = test_simple_query()
    
    # Step 3: Test pump query
    pump_response = test_pump_query()
    
    # Step 4: Analyze 503 error pattern
    analyze_503_error()
    
    # Step 5: Summary and recommendations
    print("\n=== INVESTIGATION SUMMARY ===")
    if health_data:
        openai_service = health_data.get('services', {}).get('openai', 'unknown')
        openai_errors = health_data.get('application', {}).get('openai_errors', 0)
        
        print(f"OpenAI Service Status: {openai_service}")
        print(f"OpenAI Error Count: {openai_errors}")
        
        if openai_service == 'healthy' and openai_errors > 0:
            print("FINDING: OpenAI service marked healthy but has recorded errors")
            print("RECOMMENDATION: Check OpenAI API key configuration and permissions")
        elif openai_service != 'healthy':
            print("FINDING: OpenAI service not healthy")
            print("RECOMMENDATION: OpenAI client initialization failed")
    
    print("\nNEXT STEPS:")
    print("1. Check OpenAI API key in production environment")
    print("2. Verify OpenAI client initialization in backend logs")
    print("3. Test OpenAI API key directly with OpenAI API")
    print("4. Consider fallback solutions if OpenAI integration cannot be fixed")

if __name__ == "__main__":
    main()
