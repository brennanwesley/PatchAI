#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Stripe webhook is properly configured
"""
import requests
import json

def test_webhook_endpoint():
    """Test if the webhook endpoint is accessible"""
    webhook_url = "https://patchai-backend.onrender.com/payments/webhook"
    
    print("Testing Stripe Webhook Endpoint")
    print("=" * 50)
    print(f"URL: {webhook_url}")
    
    try:
        # Test with a simple POST (will fail signature verification, but endpoint should respond)
        response = requests.post(
            webhook_url,
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print("Endpoint is accessible!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 400:
            print("This is expected - webhook signature verification failed (good!)")
        elif response.status_code == 200:
            print("Unexpected 200 response - check webhook handler")
        else:
            print(f"Status {response.status_code} - check webhook implementation")
            
    except requests.exceptions.RequestException as e:
        print(f"Error accessing webhook endpoint: {e}")
        return False
    
    print("\nNext Steps:")
    print("1. Configure webhook in Stripe Dashboard:")
    print("   URL: https://patchai-backend.onrender.com/payments/webhook")
    print("2. Select events: customer.subscription.*, invoice.payment_*")
    print("3. Copy webhook secret to backend environment variables")
    print("4. Test with a real Stripe payment")
    
    return True

if __name__ == "__main__":
    test_webhook_endpoint()
