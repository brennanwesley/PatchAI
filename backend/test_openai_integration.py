#!/usr/bin/env python3
"""
Test script to verify OpenAI API integration
Tests both local and deployed endpoints
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_local_endpoint():
    """Test the local development server"""
    url = "http://localhost:8000/prompt"
    
    test_message = {
        "messages": [
            {
                "role": "user",
                "content": "Hello! Can you help me with oilfield operations?"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=test_message, timeout=30)
        print(f"Local Test - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Local Test - Response: {data['response'][:100]}...")
            return True
        else:
            print(f"Local Test - Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Local Test - Connection Error: {e}")
        return False

def test_deployed_endpoint(render_url):
    """Test the deployed Render endpoint"""
    url = f"{render_url}/prompt"
    
    test_message = {
        "messages": [
            {
                "role": "user",
                "content": "What are the key safety considerations in drilling operations?"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=test_message, timeout=30)
        print(f"Deployed Test - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Deployed Test - Response: {data['response'][:100]}...")
            return True
        else:
            print(f"Deployed Test - Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Deployed Test - Connection Error: {e}")
        return False

def test_health_check(render_url):
    """Test the health check endpoint"""
    url = f"{render_url}/"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Health Check - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Health Check - Response: {data}")
            return True
        else:
            print(f"Health Check - Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Health Check - Connection Error: {e}")
        return False

def main():
    print("=== PatchAI OpenAI Integration Test ===\n")
    
    # Get the Render URL from user input
    render_url = input("Enter your Render service URL (e.g., https://patchai-backend-xxxx.onrender.com): ").strip()
    
    if not render_url:
        print("No Render URL provided. Testing local endpoint only.\n")
    else:
        print(f"Testing deployed endpoint: {render_url}\n")
        
        # Test health check first
        print("1. Testing Health Check...")
        health_ok = test_health_check(render_url)
        print()
        
        # Test OpenAI integration
        print("2. Testing OpenAI Integration...")
        deployed_ok = test_deployed_endpoint(render_url)
        print()
        
        if health_ok and deployed_ok:
            print("✅ All tests passed! Your OpenAI integration is working correctly.")
        else:
            print("❌ Some tests failed. Check the error messages above.")
    
    # Test local endpoint if available
    print("3. Testing Local Development Server (if running)...")
    local_ok = test_local_endpoint()
    print()
    
    if local_ok:
        print("✅ Local development server is also working correctly.")

if __name__ == "__main__":
    main()
