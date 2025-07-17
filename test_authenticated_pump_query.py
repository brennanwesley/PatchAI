#!/usr/bin/env python3
"""
Test authenticated pump queries to reproduce 500 errors
"""

import requests
import json
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def get_test_user_token():
    """Get a valid JWT token for testing"""
    print("[AUTH] Getting test user token...")
    
    # Use Supabase auth to get a real token
    try:
        from supabase import create_client, Client
        
        supabase_url = "https://iyacqcylnunndcswaeri.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5YWNxY3lsbnVubmRjc3dhZXJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2NzI4NzEsImV4cCI6MjA2NzI0ODg3MX0.YQJWkhgHvsgRVucp3qXKhyFVdOdBgKMpkzfBgFQBiQs"
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Try to sign in with a test user
        test_users = [
            {"email": "testuserkit@email.com", "password": "testpassword123"},
            {"email": "quinton@ihoseandsupply.com", "password": "testpassword123"},
            {"email": "brennan.testuser4@email.com", "password": "testpassword123"}
        ]
        
        for user in test_users:
            try:
                print(f"[AUTH] Trying to authenticate: {user['email']}")
                response = supabase.auth.sign_in_with_password({
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if response.user and response.session:
                    print(f"[AUTH] Successfully authenticated: {user['email']}")
                    return response.session.access_token
                    
            except Exception as e:
                print(f"[AUTH] Failed to authenticate {user['email']}: {e}")
                continue
        
        print("[AUTH] All authentication attempts failed")
        return None
        
    except Exception as e:
        print(f"[AUTH] Error setting up Supabase client: {e}")
        return None

def test_authenticated_pump_query(token):
    """Test pump query with authentication"""
    print(f"\n[TEST] Testing authenticated pump query...")
    
    backend_url = "https://patchai-backend.onrender.com"
    
    # Test pump queries that are known to cause 500 errors
    pump_queries = [
        "What are the specs for a 4x6-13 transfer pump?",
        "4x6-13 pump performance data",
        "Show me transfer pump specifications",
        "What pumps do you have available?",
        "Pump flowrate and pressure information"
    ]
    
    for i, query in enumerate(pump_queries, 1):
        print(f"\n[QUERY {i}] Testing: {query}")
        
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": query}
                ]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            print(f"[REQUEST] Sending to {backend_url}/prompt")
            response = requests.post(
                f"{backend_url}/prompt",
                json=payload,
                headers=headers,
                timeout=60  # Longer timeout for OpenAI calls
            )
            
            print(f"[RESPONSE] Status: {response.status_code}")
            print(f"[RESPONSE] Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[SUCCESS] Response received ({len(response.text)} chars)")
                    print(f"[PREVIEW] {data.get('response', 'No response field')[:200]}...")
                except:
                    print(f"[SUCCESS] Response received but not JSON: {response.text[:200]}...")
                    
            elif response.status_code == 500:
                print(f"[ERROR] 500 Internal Server Error - THIS IS THE ISSUE!")
                print(f"[ERROR] Response: {response.text}")
                
                # Try to get more details
                try:
                    error_data = response.json()
                    print(f"[ERROR] Parsed error: {error_data}")
                except:
                    print(f"[ERROR] Raw error text: {response.text}")
                
                return False  # Found the 500 error
                
            else:
                print(f"[UNEXPECTED] Status {response.status_code}: {response.text}")
            
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] Request timed out after 60 seconds")
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
    
    return True

def check_backend_health_before_after():
    """Check backend health before and after tests"""
    backend_url = "https://patchai-backend.onrender.com"
    
    try:
        print("[HEALTH] Checking backend health...")
        response = requests.get(f"{backend_url}/health", timeout=10)
        data = response.json()
        
        print(f"Backend Status: {data['status']}")
        print(f"OpenAI Service: {data['services']['openai']}")
        print(f"OpenAI Requests: {data['application']['openai_requests']}")
        print(f"OpenAI Errors: {data['application']['openai_errors']}")
        print(f"Total Errors: {data['application']['errors_total']}")
        
        return data
        
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return None

def main():
    """Run authenticated pump query tests"""
    print("=== AUTHENTICATED PUMP QUERY TEST ===")
    print("This test reproduces the exact 500 error scenario\n")
    
    # Check initial health
    print("[STEP 1] Initial health check")
    initial_health = check_backend_health_before_after()
    
    # Get authentication token
    print("\n[STEP 2] Getting authentication token")
    token = get_test_user_token()
    
    if not token:
        print("[CRITICAL] Cannot proceed without authentication token")
        print("This suggests the test users may not exist or have different passwords")
        return
    
    print(f"[SUCCESS] Got token: {token[:50]}...")
    
    # Test authenticated pump queries
    print("\n[STEP 3] Testing authenticated pump queries")
    success = test_authenticated_pump_query(token)
    
    # Check final health
    print("\n[STEP 4] Final health check")
    final_health = check_backend_health_before_after()
    
    # Compare health metrics
    if initial_health and final_health:
        print("\n[ANALYSIS] Health metrics comparison:")
        print(f"OpenAI Requests: {initial_health['application']['openai_requests']} -> {final_health['application']['openai_requests']}")
        print(f"OpenAI Errors: {initial_health['application']['openai_errors']} -> {final_health['application']['openai_errors']}")
        print(f"Total Errors: {initial_health['application']['errors_total']} -> {final_health['application']['errors_total']}")
    
    if success:
        print("\n[RESULT] All tests completed successfully - no 500 errors found")
    else:
        print("\n[RESULT] 500 Internal Server Error reproduced!")

if __name__ == "__main__":
    main()
