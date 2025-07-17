#!/usr/bin/env python3
"""
Test authenticated pump queries to reproduce 503 errors
This will help identify the exact cause of OpenAI 503 errors with authenticated requests
"""

import requests
import json
import os
from supabase import create_client, Client

def get_supabase_client():
    """Initialize Supabase client for authentication"""
    url = "https://ksqcmhqpzjkqgxpqfmwt.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzcWNtaHFwemprcWd4cHFmbXd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYyMzE2NzYsImV4cCI6MjA1MTgwNzY3Nn0.Oj1-Xz8cFJoHqQKJjUqRXjXFfKbGnJqKqCBqjLNJKqY"
    return create_client(url, key)

def authenticate_test_user():
    """Authenticate a test user and get JWT token"""
    print("=== AUTHENTICATING TEST USER ===")
    
    supabase = get_supabase_client()
    
    # Try to sign in with a test user
    test_users = [
        {"email": "testuserkit@email.com", "password": "testpassword123"},
        {"email": "testuser@email.com", "password": "testpassword123"},
        {"email": "brennan.testuser4@email.com", "password": "testpassword123"}
    ]
    
    for user_creds in test_users:
        try:
            print(f"Trying to authenticate: {user_creds['email']}")
            response = supabase.auth.sign_in_with_password(user_creds)
            
            if response.user and response.session:
                print(f"✅ Successfully authenticated: {user_creds['email']}")
                print(f"User ID: {response.user.id}")
                print(f"Token: {response.session.access_token[:50]}...")
                return response.session.access_token
                
        except Exception as e:
            print(f"❌ Failed to authenticate {user_creds['email']}: {e}")
            continue
    
    print("❌ All authentication attempts failed")
    return None

def test_authenticated_pump_query(token):
    """Test authenticated pump query that should trigger 503 error"""
    print("\n=== TESTING AUTHENTICATED PUMP QUERY ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with pump-specific query that should trigger context service
    pump_queries = [
        "Tell me about 4x6-13 transfer pumps",
        "What are the specifications for transfer pumps?",
        "I need information about water transfer pumps"
    ]
    
    for i, query in enumerate(pump_queries):
        print(f"\n--- Test Query {i+1}: {query} ---")
        
        try:
            response = requests.post(
                'https://patchai-backend.onrender.com/prompt',
                headers=headers,
                json={'messages': [{'role': 'user', 'content': query}]}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 503:
                print("🔍 503 ERROR DETECTED - Analyzing response:")
                try:
                    error_data = response.json()
                    print(f"Error Detail: {error_data.get('detail', 'No detail')}")
                except:
                    print(f"Raw Response: {response.text}")
                    
                # Check backend health after error
                print("\n🔍 Checking backend health after 503 error:")
                health_response = requests.get('https://patchai-backend.onrender.com/health')
                health_data = health_response.json()
                print(f"OpenAI Errors: {health_data.get('application', {}).get('openai_errors', 0)}")
                
            elif response.status_code == 200:
                print("✅ SUCCESS - Got response:")
                try:
                    success_data = response.json()
                    print(f"Response: {success_data.get('response', 'No response')[:100]}...")
                except:
                    print(f"Raw Response: {response.text[:100]}...")
                    
            else:
                print(f"❓ Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def test_non_pump_authenticated_query(token):
    """Test authenticated non-pump query to see if issue is pump-specific"""
    print("\n=== TESTING NON-PUMP AUTHENTICATED QUERY ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            'https://patchai-backend.onrender.com/prompt',
            headers=headers,
            json={'messages': [{'role': 'user', 'content': 'Hello, how are you?'}]}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Main test function"""
    print("TESTING AUTHENTICATED 503 ERRORS")
    print("=" * 50)
    
    # Step 1: Get authentication token
    token = authenticate_test_user()
    if not token:
        print("❌ Cannot proceed without authentication token")
        print("This suggests test users need to be created or have different passwords")
        return
    
    # Step 2: Test non-pump query first
    non_pump_works = test_non_pump_authenticated_query(token)
    
    # Step 3: Test pump queries that should trigger 503
    test_authenticated_pump_query(token)
    
    # Step 4: Analysis
    print("\n=== ANALYSIS ===")
    if non_pump_works:
        print("✅ Non-pump queries work with authentication")
        print("🔍 Issue appears to be pump-specific - likely in PumpContextService")
    else:
        print("❌ All authenticated queries fail")
        print("🔍 Issue is with general OpenAI integration, not pump-specific")
    
    print("\nRECOMMENDATIONS:")
    print("1. Check PumpContextService initialization and context generation")
    print("2. Verify pump data files are accessible in production")
    print("3. Check OpenAI token limits and rate limiting")
    print("4. Consider implementing fallback pump data responses")

if __name__ == "__main__":
    main()
