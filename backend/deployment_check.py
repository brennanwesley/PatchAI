#!/usr/bin/env python3
"""
Deployment Verification Script for PatchAI Backend
Checks if all required files and dependencies are properly deployed
"""

import os
import sys
import json
import traceback
from pathlib import Path

def check_pump_data_files():
    """Check if pump data files are present and readable"""
    print("=" * 60)
    print("CHECKING PUMP DATA FILES")
    print("=" * 60)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    pump_data_dir = script_dir / "data" / "pumps"
    
    print(f"Script directory: {script_dir}")
    print(f"Pump data directory: {pump_data_dir}")
    print(f"Directory exists: {pump_data_dir.exists()}")
    
    if not pump_data_dir.exists():
        print("[CRITICAL] Pump data directory does not exist!")
        return False
    
    # Check for required files
    required_files = [
        "transfer_pumps.json",
        "data_loader.py",
        "__init__.py"
    ]
    
    all_files_present = True
    for file_name in required_files:
        file_path = pump_data_dir / file_name
        exists = file_path.exists()
        print(f"  {file_name}: {'[OK]' if exists else '[FAIL]'} {'EXISTS' if exists else 'MISSING'}")
        
        if exists and file_name.endswith('.json'):
            try:
                size = file_path.stat().st_size
                print(f"    Size: {size} bytes")
                
                # Try to read and parse JSON
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'pumps' in data:
                        pump_count = len(data['pumps'])
                        print(f"    Contains {pump_count} pump models")
                    else:
                        print(f"    JSON structure: {type(data)}")
            except Exception as e:
                print(f"    [ERROR] Error reading file: {e}")
                all_files_present = False
        elif exists and file_name.endswith('.py'):
            try:
                size = file_path.stat().st_size
                print(f"    Size: {size} bytes")
                readable = os.access(file_path, os.R_OK)
                print(f"    Readable: {'[OK]' if readable else '[FAIL]'}")
            except Exception as e:
                print(f"    [ERROR] Error checking file: {e}")
                all_files_present = False
        
        if not exists:
            all_files_present = False
    
    return all_files_present

def check_pump_service_imports():
    """Check if PumpContextService can be imported"""
    print("\n" + "=" * 60)
    print("CHECKING PUMP SERVICE IMPORTS")
    print("=" * 60)
    
    try:
        print("Attempting to import PumpDataLoader...")
        from data.pumps.data_loader import PumpDataLoader
        print("[OK] PumpDataLoader import successful")
        
        print("Attempting to instantiate PumpDataLoader...")
        loader = PumpDataLoader()
        print("[OK] PumpDataLoader instantiation successful")
        
        print("Testing pump data loading...")
        pumps = loader.load_transfer_pumps()
        print(f"[OK] Loaded {len(pumps)} pump models")
        
        # List pump models
        for pump_data in pumps:
            pump_size = pump_data.get('size', 'Unknown')
            pump_model = pump_data.get('model', 'Unknown')
            pump_type = pump_data.get('type', 'Unknown')
            print(f"  - {pump_size}: {pump_model} ({pump_type})")
        
        # Test validation
        print("\nTesting data validation...")
        validation = loader.validate_data_structure()
        print(f"Data valid: {validation['valid']}")
        if validation['errors']:
            print(f"Validation errors: {len(validation['errors'])}")
            for error in validation['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
    except Exception as e:
        print(f"[ERROR] Error with PumpDataLoader: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False
    
    try:
        print("\nAttempting to import PumpContextService...")
        from services.pump_context_service import PumpContextService
        print("[OK] PumpContextService import successful")
        
        print("Attempting to instantiate PumpContextService...")
        service = PumpContextService()
        print("[OK] PumpContextService instantiation successful")
        
        print("Testing pump context generation...")
        test_query = "What is the flowrate vs pressure table for the 4x6-13 pump?"
        context = service.generate_pump_context(test_query)
        
        if context:
            print(f"[OK] Context generation successful: {len(context)} characters")
            print(f"Context preview: {context[:200]}...")
        else:
            print("[WARNING] No context generated (query may not be pump-related)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error with PumpContextService: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False

def check_environment():
    """Check environment and Python path"""
    print("\n" + "=" * 60)
    print("CHECKING ENVIRONMENT")
    print("=" * 60)
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {Path(__file__).absolute()}")
    
    print("\nPython path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    print(f"\nEnvironment variables:")
    env_vars = ['PYTHONPATH', 'PATH', 'HOME', 'USER']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        print(f"  {var}: {value}")

def main():
    """Run all deployment checks"""
    print("PATCHAI BACKEND DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    # Check environment
    check_environment()
    
    # Check pump data files
    files_ok = check_pump_data_files()
    
    # Check service imports
    imports_ok = check_pump_service_imports()
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT CHECK SUMMARY")
    print("=" * 60)
    
    print(f"Pump data files: {'[OK]' if files_ok else '[FAILED]'}")
    print(f"Service imports: {'[OK]' if imports_ok else '[FAILED]'}")
    
    if files_ok and imports_ok:
        print("\n[SUCCESS] ALL CHECKS PASSED - Deployment appears to be working correctly!")
        return 0
    else:
        print("\n[FAILED] DEPLOYMENT ISSUES DETECTED - Check the errors above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
