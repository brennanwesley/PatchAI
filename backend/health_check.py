#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health check script to verify the FastAPI app can start without errors.
This is useful for deployment verification.
"""

import sys
import os
import importlib.util

def check_imports():
    """Check if all required modules can be imported."""
    required_modules = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'openai',
        'supabase',
        'jwt',
        'dotenv'
    ]
    
    failed_imports = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except ImportError as e:
            print(f"[FAIL] {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def check_app_creation():
    """Check if the FastAPI app can be created without errors."""
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import main module
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # Check if app exists
        if hasattr(main_module, 'app'):
            print("[OK] FastAPI app created successfully")
            return True
        else:
            print("[FAIL] FastAPI app not found in main module")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error creating FastAPI app: {e}")
        return False

def main():
    """Run all health checks."""
    print("=== FastAPI Health Check ===")
    
    print("\n1. Checking imports...")
    imports_ok = check_imports()
    
    print("\n2. Checking app creation...")
    app_ok = check_app_creation()
    
    print("\n=== Results ===")
    if imports_ok and app_ok:
        print("[OK] All checks passed! App is ready for deployment.")
        sys.exit(0)
    else:
        print("[FAIL] Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
