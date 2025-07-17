#!/usr/bin/env python3
"""
Direct test to reproduce and diagnose 500 errors with pump data queries
"""

import os
import sys
import requests
import json
import traceback
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pump_context_service_directly():
    """Test pump context service initialization and functionality"""
    print("[TEST 1] Testing PumpContextService directly...")
    
    try:
        # Test import
        from services.pump_context_service import PumpContextService
        print("[OK] PumpContextService import successful")
        
        # Test initialization
        pump_service = PumpContextService()
        print("[OK] PumpContextService initialization successful")
        
        # Test pump data loading
        if hasattr(pump_service, 'pump_data_loader'):
            print(f"[OK] Pump data loader available: {pump_service.pump_data_loader is not None}")
        
        # Test with pump query
        test_queries = [
            "What are the specs for a 4x6-13 pump?",
            "4x6-13 transfer pump performance",
            "pump flowrate and pressure data"
        ]
        
        for query in test_queries:
            print(f"\n[TESTING] Query: {query}")
            try:
                context = pump_service.generate_pump_context(query)
                if context:
                    print(f"[OK] Generated context ({len(context)} chars): {context[:100]}...")
                else:
                    print("[WARN] No context generated (query may not be pump-related)")
            except Exception as e:
                print(f"[ERROR] Error generating context: {e}")
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] PumpContextService test failed: {e}")
        traceback.print_exc()
        return False

def test_openai_integration():
    """Test OpenAI client initialization and basic functionality"""
    print("\n[TEST 2] Testing OpenAI integration...")
    
    try:
        from services.openai_service import initialize_openai_client
        
        # Test OpenAI client initialization
        openai_client = initialize_openai_client()
        print(f"[OK] OpenAI client initialized: {openai_client is not None}")
        
        if openai_client:
            # Test basic OpenAI call
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test message."}
            ]
            
            print("[TESTING] Basic OpenAI API call...")
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=test_messages,
                max_tokens=50,
                temperature=0.7
            )
            
            print(f"[OK] OpenAI API call successful: {response.choices[0].message.content[:50]}...")
            return True
        else:
            print("[ERROR] OpenAI client is None")
            return False
            
    except Exception as e:
        print(f"[ERROR] OpenAI integration test failed: {e}")
        traceback.print_exc()
        return False

def test_backend_prompt_endpoint():
    """Test the /prompt endpoint directly with a pump query"""
    print("\n[TEST 3] Testing backend /prompt endpoint...")
    
    backend_url = "https://patchai-backend.onrender.com"
    
    # Test without authentication first to see the error
    print("[TESTING] Testing /prompt endpoint without auth (should get 403)...")
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
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 403:
            print("[OK] Expected 403 - authentication required")
        elif response.status_code == 500:
            print("[ERROR] 500 Internal Server Error - this is the problem!")
            return False
        else:
            print(f"[WARN] Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Error testing /prompt endpoint: {e}")
        return False
    
    return True

def test_pump_data_files():
    """Test pump data files directly"""
    print("\n[TEST 4] Testing pump data files...")
    
    try:
        from pathlib import Path
        
        # Check pump data directory
        pump_data_dir = Path(__file__).parent / "backend" / "data" / "pumps"
        print(f"Pump data directory: {pump_data_dir}")
        print(f"Directory exists: {pump_data_dir.exists()}")
        
        if pump_data_dir.exists():
            pump_files = list(pump_data_dir.glob("*.json"))
            print(f"Found {len(pump_files)} JSON files:")
            
            for pump_file in pump_files:
                print(f"  - {pump_file.name} ({pump_file.stat().st_size} bytes)")
                
                # Test loading the JSON
                try:
                    with open(pump_file, 'r') as f:
                        data = json.load(f)
                    print(f"    [OK] JSON valid, contains {len(data)} items")
                except Exception as e:
                    print(f"    [ERROR] JSON invalid: {e}")
                    return False
        else:
            print("[ERROR] Pump data directory not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Error testing pump data files: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("=== PUMP 500 ERROR DIAGNOSTIC TESTS ===\n")
    
    results = {
        "pump_context_service": test_pump_context_service_directly(),
        "openai_integration": test_openai_integration(),
        "backend_endpoint": test_backend_prompt_endpoint(),
        "pump_data_files": test_pump_data_files()
    }
    
    print("\n=== TEST RESULTS SUMMARY ===")
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    # Determine likely root cause
    print("\n=== ROOT CAUSE ANALYSIS ===")
    if not results["pump_data_files"]:
        print("[ANALYSIS] LIKELY CAUSE: Pump data files missing or corrupted")
    elif not results["pump_context_service"]:
        print("[ANALYSIS] LIKELY CAUSE: PumpContextService initialization failure")
    elif not results["openai_integration"]:
        print("[ANALYSIS] LIKELY CAUSE: OpenAI API integration issue")
    elif not results["backend_endpoint"]:
        print("[ANALYSIS] LIKELY CAUSE: Backend /prompt endpoint error")
    else:
        print("[ANALYSIS] All local tests pass - issue may be production-specific")

if __name__ == "__main__":
    main()
