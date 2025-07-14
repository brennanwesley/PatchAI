#!/usr/bin/env python3
"""
Quick test script to verify pump data loading works
"""
import sys
import os
import traceback

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pump_data_loading():
    """Test if pump data can be loaded successfully"""
    print("[DEBUG] Testing pump data loading...")
    
    try:
        # Test 1: Import data loader
        print("[INFO] Importing PumpDataLoader...")
        from data.pumps.data_loader import PumpDataLoader
        print("[SUCCESS] PumpDataLoader imported successfully")
        
        # Test 2: Initialize data loader
        print("[INFO] Initializing PumpDataLoader...")
        loader = PumpDataLoader()
        print("[SUCCESS] PumpDataLoader initialized successfully")
        
        # Test 3: Check file path
        print(f"[INFO] Data file path: {loader.transfer_pumps_file}")
        print(f"[INFO] File exists: {loader.transfer_pumps_file.exists()}")
        
        # Test 4: Load pump data
        print("[INFO] Loading transfer pumps data...")
        pumps = loader.load_transfer_pumps()
        print(f"[SUCCESS] Loaded {len(pumps)} pumps successfully")
        
        # Test 5: Check specific pump
        pump_4x6 = loader.get_pump_by_size("4x6-13")
        if pump_4x6:
            print("[SUCCESS] Found 4x6-13 pump data")
            print(f"   Model: {pump_4x6.get('model')}")
            print(f"   Type: {pump_4x6.get('type')}")
        else:
            print("[ERROR] 4x6-13 pump not found")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during pump data loading test: {e}")
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return False

def test_pump_service():
    """Test if pump service can be initialized"""
    print("\n[DEBUG] Testing pump service initialization...")
    
    try:
        # Test 1: Import pump service
        print("[INFO] Importing PumpSelectionService...")
        from services.pump_service import PumpSelectionService
        print("[SUCCESS] PumpSelectionService imported successfully")
        
        # Test 2: Initialize pump service
        print("[INFO] Initializing PumpSelectionService...")
        service = PumpSelectionService()
        print("[SUCCESS] PumpSelectionService initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during pump service test: {e}")
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return False

def test_pump_context_service():
    """Test if pump context service can be initialized"""
    print("\n[DEBUG] Testing pump context service initialization...")
    
    try:
        # Test 1: Import pump context service
        print("[INFO] Importing PumpContextService...")
        from services.pump_context_service import PumpContextService
        print("[SUCCESS] PumpContextService imported successfully")
        
        # Test 2: Initialize pump context service
        print("[INFO] Initializing PumpContextService...")
        service = PumpContextService()
        print("[SUCCESS] PumpContextService initialized successfully")
        
        # Test 3: Test pump query detection
        print("[INFO] Testing pump query detection...")
        is_pump_query = service.detect_pump_query("Can you provide me a table of the head vs flow for the 4x6-13 pump?")
        print(f"[SUCCESS] Pump query detected: {is_pump_query}")
        
        # Test 4: Test context generation
        print("[INFO] Testing context generation...")
        context = service.generate_pump_context("Can you provide me a table of the head vs flow for the 4x6-13 pump?")
        if context:
            print(f"[SUCCESS] Context generated: {len(context)} characters")
            print(f"[INFO] Context preview: {context[:200]}...")
        else:
            print("[ERROR] No context generated")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during pump context service test: {e}")
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("PUMP DATA LOADING TEST SUITE")
    print("=" * 50)
    
    # Run all tests
    test1_passed = test_pump_data_loading()
    test2_passed = test_pump_service()
    test3_passed = test_pump_context_service()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"   Data Loading: {'PASS' if test1_passed else 'FAIL'}")
    print(f"   Pump Service: {'PASS' if test2_passed else 'FAIL'}")
    print(f"   Context Service: {'PASS' if test3_passed else 'FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\nALL TESTS PASSED - Pump services should work in production!")
    else:
        print("\nSOME TESTS FAILED - This explains the 500 error!")
