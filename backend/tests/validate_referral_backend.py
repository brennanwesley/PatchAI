"""
Production-Safe Referral System Validation
Tests core referral functionality without creating test users
"""

import asyncio
import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.referral_service import ReferralService
from services.supabase_service import supabase, calculate_referral_rewards
from models.schemas import SignupWithReferralRequest, ProfileUpdateRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferralBackendValidator:
    """Production-safe validation of referral system backend"""
    
    def __init__(self):
        self.referral_service = ReferralService(supabase)
        
    async def validate_all_components(self):
        """Validate all referral system components"""
        logger.info("🚀 Starting Referral System Backend Validation")
        
        try:
            # Test 1: Database Schema Validation
            await self.validate_database_schema()
            
            # Test 2: Referral Code Generation
            await self.validate_referral_code_generation()
            
            # Test 3: Referral Code Validation Logic
            await self.validate_referral_code_validation()
            
            # Test 4: Reward Calculation Logic
            await self.validate_reward_calculation()
            
            # Test 5: Service Integration Points
            await self.validate_service_integration()
            
            # Test 6: API Endpoint Registration
            await self.validate_api_endpoints()
            
            logger.info("✅ All Referral System Backend Components Validated Successfully!")
            
        except Exception as e:
            logger.error(f"❌ Backend Validation Failed: {e}")
            raise
    
    async def validate_database_schema(self):
        """Validate database schema and tables exist"""
        logger.info("🧪 Validating Database Schema...")
        
        # Check user_profiles table has referral columns
        try:
            result = supabase.table("user_profiles").select("id, referral_code, referred_by, company").limit(1).execute()
            logger.info("✅ user_profiles table has referral columns")
        except Exception as e:
            raise Exception(f"user_profiles table missing referral columns: {e}")
        
        # Check referral_relationships table exists
        try:
            result = supabase.table("referral_relationships").select("*").limit(1).execute()
            logger.info("✅ referral_relationships table exists")
        except Exception as e:
            raise Exception(f"referral_relationships table missing: {e}")
        
        # Check referral_rewards table exists
        try:
            result = supabase.table("referral_rewards").select("*").limit(1).execute()
            logger.info("✅ referral_rewards table exists")
        except Exception as e:
            raise Exception(f"referral_rewards table missing: {e}")
        
        logger.info("✅ Database schema validation complete")
    
    async def validate_referral_code_generation(self):
        """Validate referral code generation logic"""
        logger.info("🧪 Validating Referral Code Generation...")
        
        # Test code generation format
        codes = set()
        for i in range(5):
            code = self.referral_service.generate_referral_code()
            
            # Validate format
            assert len(code) == 6, f"Code length should be 6, got {len(code)}"
            assert code.isalnum(), f"Code should be alphanumeric, got {code}"
            assert code.isupper(), f"Code should be uppercase, got {code}"
            assert code not in codes, f"Duplicate code generated: {code}"
            codes.add(code)
        
        logger.info(f"✅ Generated {len(codes)} unique referral codes with correct format")
    
    async def validate_referral_code_validation(self):
        """Validate referral code validation logic"""
        logger.info("🧪 Validating Referral Code Validation...")
        
        # Test invalid formats
        invalid_codes = ["", "ABC", "ABCDEFG", "abc123", "AB@123", None]
        for invalid_code in invalid_codes:
            result = await self.referral_service.validate_referral_code(invalid_code)
            assert result is None, f"Invalid code {invalid_code} should return None"
        
        # Test valid format but non-existent code
        result = await self.referral_service.validate_referral_code("XYZ999")
        assert result is None, "Non-existent code should return None"
        
        logger.info("✅ Referral code validation logic working correctly")
    
    async def validate_reward_calculation(self):
        """Validate referral reward calculation logic"""
        logger.info("🧪 Validating Reward Calculation...")
        
        # Test first 12 months (10% reward)
        reward_data = await calculate_referral_rewards("test_user", 2000.0, 6)  # $20, 6 months
        assert reward_data["reward_percentage"] == 0.10, "Should be 10% for first 12 months"
        assert reward_data["reward_amount"] == 200.0, "Reward amount calculation incorrect"
        
        # Test after 12 months (5% reward)
        reward_data = await calculate_referral_rewards("test_user", 2000.0, 15)  # $20, 15 months
        assert reward_data["reward_percentage"] == 0.05, "Should be 5% after 12 months"
        assert reward_data["reward_amount"] == 100.0, "Reward amount calculation incorrect"
        
        # Test edge cases
        reward_data = await calculate_referral_rewards("test_user", 0.0, 6)  # $0
        assert reward_data["reward_amount"] == 0.0, "Zero amount should result in zero reward"
        
        logger.info("✅ Reward calculation logic working correctly")
    
    async def validate_service_integration(self):
        """Validate service integration points"""
        logger.info("🧪 Validating Service Integration...")
        
        # Test ReferralService initialization
        assert self.referral_service.supabase is not None, "ReferralService should have supabase client"
        
        # Test service methods exist
        assert hasattr(self.referral_service, 'generate_referral_code'), "Missing generate_referral_code method"
        assert hasattr(self.referral_service, 'validate_referral_code'), "Missing validate_referral_code method"
        assert hasattr(self.referral_service, 'assign_referral_code_to_user'), "Missing assign_referral_code_to_user method"
        assert hasattr(self.referral_service, 'create_referral_relationship'), "Missing create_referral_relationship method"
        assert hasattr(self.referral_service, 'get_user_referral_info'), "Missing get_user_referral_info method"
        
        logger.info("✅ Service integration points validated")
    
    async def validate_api_endpoints(self):
        """Validate API endpoint registration"""
        logger.info("🧪 Validating API Endpoint Registration...")
        
        # Check if referral routes file exists
        referral_routes_path = os.path.join(os.path.dirname(__file__), '..', 'routes', 'referral_routes.py')
        assert os.path.exists(referral_routes_path), "referral_routes.py file missing"
        
        # Check main.py includes referral routes
        main_py_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(main_py_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
            assert 'referral_routes' in main_content, "referral_routes not imported in main.py"
            assert 'app.include_router(referral_router' in main_content, "referral_router not registered in main.py"
        
        logger.info("✅ API endpoint registration validated")
    
    async def validate_existing_users_compatibility(self):
        """Validate that existing users are not affected"""
        logger.info("🧪 Validating Existing Users Compatibility...")
        
        # Check that existing users can still be queried
        try:
            result = supabase.table("user_profiles").select("id, email, display_name").limit(5).execute()
            assert result.data, "Should be able to query existing user profiles"
            logger.info(f"✅ Successfully queried {len(result.data)} existing user profiles")
        except Exception as e:
            raise Exception(f"Failed to query existing users: {e}")
        
        # Check that new columns are nullable and don't break existing data
        for user in result.data:
            # These should not cause errors even if null
            user_id = user.get('id')
            referral_code = user.get('referral_code')  # Can be null
            referred_by = user.get('referred_by')      # Can be null
            company = user.get('company')              # Can be null
            
            logger.info(f"User {user_id}: referral_code={referral_code}, referred_by={referred_by}, company={company}")
        
        logger.info("✅ Existing users compatibility validated")


async def main():
    """Run the backend validation"""
    validator = ReferralBackendValidator()
    await validator.validate_all_components()
    await validator.validate_existing_users_compatibility()


if __name__ == "__main__":
    asyncio.run(main())
