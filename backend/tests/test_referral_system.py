"""
Comprehensive Test Suite for Referral System Phase 2
Tests all referral functionality including code generation, validation, signup, and rewards
"""

import asyncio
import sys
import os
import uuid
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.referral_service import ReferralService
from services.supabase_service import supabase
from models.schemas import SignupWithReferralRequest, ProfileUpdateRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferralSystemTester:
    """Comprehensive test suite for referral system"""
    
    def __init__(self):
        self.referral_service = ReferralService(supabase)
        self.test_users = []
        self.test_referral_codes = []
        
    async def run_all_tests(self):
        """Run all referral system tests"""
        logger.info("🚀 Starting Referral System Phase 2 Tests")
        
        try:
            # Test 1: Referral Code Generation
            await self.test_referral_code_generation()
            
            # Test 2: Referral Code Validation
            await self.test_referral_code_validation()
            
            # Test 3: User Profile Management
            await self.test_user_profile_management()
            
            # Test 4: Referral Relationship Creation
            await self.test_referral_relationship_creation()
            
            # Test 5: Referral Info Retrieval
            await self.test_referral_info_retrieval()
            
            # Test 6: Reward Calculation Logic
            await self.test_reward_calculation()
            
            # Test 7: Edge Cases and Error Handling
            await self.test_edge_cases()
            
            logger.info("✅ All Referral System Tests Completed Successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test Suite Failed: {e}")
            raise
        finally:
            # Cleanup test data
            await self.cleanup_test_data()
    
    async def test_referral_code_generation(self):
        """Test referral code generation and uniqueness"""
        logger.info("🧪 Testing Referral Code Generation...")
        
        # Test 1: Generate multiple codes and verify uniqueness
        codes = set()
        for i in range(10):
            code = self.referral_service.generate_referral_code()
            assert len(code) == 6, f"Code length should be 6, got {len(code)}"
            assert code.isalnum(), f"Code should be alphanumeric, got {code}"
            assert code.isupper(), f"Code should be uppercase, got {code}"
            assert code not in codes, f"Duplicate code generated: {code}"
            codes.add(code)
            self.test_referral_codes.append(code)
        
        logger.info(f"✅ Generated {len(codes)} unique referral codes")
    
    async def test_referral_code_validation(self):
        """Test referral code validation logic"""
        logger.info("🧪 Testing Referral Code Validation...")
        
        # Test valid format but non-existent code
        result = await self.referral_service.validate_referral_code("ABC123")
        assert result is None, "Non-existent code should return None"
        
        # Test invalid formats
        invalid_codes = ["", "ABC", "ABCDEFG", "abc123", "AB@123"]
        for invalid_code in invalid_codes:
            result = await self.referral_service.validate_referral_code(invalid_code)
            assert result is None, f"Invalid code {invalid_code} should return None"
        
        logger.info("✅ Referral code validation working correctly")
    
    async def test_user_profile_management(self):
        """Test user profile creation and referral code assignment"""
        logger.info("🧪 Testing User Profile Management...")
        
        # Create test user profile
        test_user_id = str(uuid.uuid4())
        test_email = f"test_{test_user_id[:8]}@example.com"
        
        # Insert test user profile (without phone - that's in auth.users)
        profile_data = {
            "id": test_user_id,
            "email": test_email,
            "display_name": "Test User",
            "company": "Test Company",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("user_profiles").insert(profile_data).execute()
        assert result.data, "Failed to create test user profile"
        self.test_users.append(test_user_id)
        
        # Test referral code assignment
        referral_code = await self.referral_service.assign_referral_code_to_user(test_user_id)
        assert referral_code, "Failed to assign referral code"
        assert len(referral_code) == 6, "Referral code should be 6 characters"
        
        # Verify code was saved to profile
        profile = supabase.table("user_profiles").select("referral_code").eq("id", test_user_id).single().execute()
        assert profile.data["referral_code"] == referral_code, "Referral code not saved to profile"
        
        logger.info(f"✅ User profile management working correctly, assigned code: {referral_code}")
    
    async def test_referral_relationship_creation(self):
        """Test creating referral relationships between users"""
        logger.info("🧪 Testing Referral Relationship Creation...")
        
        # Create two test users
        referring_user_id = str(uuid.uuid4())
        referred_user_id = str(uuid.uuid4())
        
        # Create referring user
        referring_profile = {
            "id": referring_user_id,
            "email": f"referring_{referring_user_id[:8]}@example.com",
            "display_name": "Referring User",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_profiles").insert(referring_profile).execute()
        self.test_users.append(referring_user_id)
        
        # Assign referral code to referring user
        referring_code = await self.referral_service.assign_referral_code_to_user(referring_user_id)
        
        # Create referred user
        referred_profile = {
            "id": referred_user_id,
            "email": f"referred_{referred_user_id[:8]}@example.com",
            "display_name": "Referred User",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_profiles").insert(referred_profile).execute()
        self.test_users.append(referred_user_id)
        
        # Test referral relationship creation
        success = await self.referral_service.create_referral_relationship(
            referring_user_id, referred_user_id, referring_code
        )
        assert success, "Failed to create referral relationship"
        
        # Verify relationship was created
        relationship = supabase.table("referral_relationships").select("*").eq(
            "referrer_user_id", referring_user_id
        ).eq("referee_user_id", referred_user_id).single().execute()
        
        assert relationship.data, "Referral relationship not found in database"
        assert relationship.data["status"] == "active", "Referral relationship should be active"
        
        # Verify referred_by was updated in user profile
        referred_profile = supabase.table("user_profiles").select("referred_by").eq(
            "id", referred_user_id
        ).single().execute()
        assert referred_profile.data["referred_by"] == referring_user_id, "referred_by not updated"
        
        logger.info("✅ Referral relationship creation working correctly")
    
    async def test_referral_info_retrieval(self):
        """Test retrieving comprehensive referral information"""
        logger.info("🧪 Testing Referral Info Retrieval...")
        
        if not self.test_users:
            logger.warning("No test users available, skipping referral info test")
            return
        
        # Get referral info for a test user
        test_user_id = self.test_users[0]
        referral_info = await self.referral_service.get_user_referral_info(test_user_id)
        
        assert referral_info, "Failed to retrieve referral info"
        assert "user_id" in referral_info, "Missing user_id in referral info"
        assert "referral_code" in referral_info, "Missing referral_code in referral info"
        assert "total_referrals" in referral_info, "Missing total_referrals in referral info"
        
        logger.info("✅ Referral info retrieval working correctly")
    
    async def test_reward_calculation(self):
        """Test referral reward calculation logic"""
        logger.info("🧪 Testing Reward Calculation...")
        
        from services.supabase_service import calculate_referral_rewards
        
        # Test first 12 months (10% reward)
        reward_data = await calculate_referral_rewards("test_user", 2000.0, 6)  # $20, 6 months
        assert reward_data["reward_percentage"] == 0.10, "Should be 10% for first 12 months"
        assert reward_data["reward_amount"] == 200.0, "Reward amount calculation incorrect"
        
        # Test after 12 months (5% reward)
        reward_data = await calculate_referral_rewards("test_user", 2000.0, 15)  # $20, 15 months
        assert reward_data["reward_percentage"] == 0.05, "Should be 5% after 12 months"
        assert reward_data["reward_amount"] == 100.0, "Reward amount calculation incorrect"
        
        logger.info("✅ Reward calculation working correctly")
    
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        logger.info("🧪 Testing Edge Cases and Error Handling...")
        
        # Test self-referral prevention
        if self.test_users:
            test_user_id = self.test_users[0]
            user_profile = supabase.table("user_profiles").select("referral_code").eq(
                "id", test_user_id
            ).single().execute()
            
            if user_profile.data and user_profile.data.get("referral_code"):
                success = await self.referral_service.create_referral_relationship(
                    test_user_id, test_user_id, user_profile.data["referral_code"]
                )
                assert not success, "Self-referral should be prevented"
        
        # Test duplicate referral code assignment
        if self.test_users:
            test_user_id = self.test_users[0]
            code1 = await self.referral_service.assign_referral_code_to_user(test_user_id)
            code2 = await self.referral_service.assign_referral_code_to_user(test_user_id)
            assert code1 == code2, "Should return existing code, not generate new one"
        
        logger.info("✅ Edge cases and error handling working correctly")
    
    async def cleanup_test_data(self):
        """Clean up test data from database"""
        logger.info("🧹 Cleaning up test data...")
        
        try:
            # Delete test user profiles
            for user_id in self.test_users:
                supabase.table("user_profiles").delete().eq("id", user_id).execute()
                
            # Delete test referral relationships
            for user_id in self.test_users:
                supabase.table("referral_relationships").delete().eq("referrer_user_id", user_id).execute()
                supabase.table("referral_relationships").delete().eq("referee_user_id", user_id).execute()
            
            logger.info("✅ Test data cleanup completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Test cleanup failed: {e}")


async def main():
    """Run the comprehensive test suite"""
    tester = ReferralSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
