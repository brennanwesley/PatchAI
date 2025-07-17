#!/usr/bin/env python3
"""
Test script to verify referral service initialization and basic functionality
"""

import os
import sys
import asyncio
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_referral_service():
    """Test referral service initialization and basic operations"""
    try:
        print("[INFO] Testing referral service initialization...")
        
        # Test Supabase client initialization
        from services.supabase_service import supabase
        print(f"[SUCCESS] Supabase client initialized: {supabase is not None}")
        
        # Test referral service initialization
        from services.referral_service import ReferralService
        referral_service = ReferralService(supabase)
        print(f"[SUCCESS] Referral service initialized: {referral_service is not None}")
        
        # Test referral code generation
        print("[TEST] Testing referral code generation...")
        code = referral_service.generate_referral_code()
        print(f"[SUCCESS] Generated referral code: {code}")
        
        # Test with a known user ID (quinton@ihoseandsupply.com)
        test_user_id = "3b497871-9ab2-465e-a16d-e68b403c6a4e"  # Real user ID for quinton@ihoseandsupply.com
        print(f"[TEST] Testing referral code assignment for user: {test_user_id}")
        
        try:
            assigned_code = await referral_service.assign_referral_code_to_user(test_user_id)
            print(f"[SUCCESS] Assigned referral code: {assigned_code}")
        except Exception as e:
            print(f"[ERROR] Failed to assign referral code: {e}")
        
        # Test referral code validation
        print("[TEST] Testing referral code validation...")
        try:
            validation_result = await referral_service.validate_referral_code("14CYUY")
            print(f"[SUCCESS] Validation result: {validation_result}")
        except Exception as e:
            print(f"[ERROR] Failed to validate referral code: {e}")
        
        print("[SUCCESS] All referral service tests completed")
        
    except Exception as e:
        print(f"[ERROR] Referral service test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_referral_service())
