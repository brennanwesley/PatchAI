"""
Referral Code System Service
Handles referral code generation, relationship management, and reward tracking
"""

import uuid
import random
import string
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from supabase import Client

logger = logging.getLogger(__name__)


class ReferralService:
    """Service for managing referral codes, relationships, and rewards"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
        # Referral code configuration
        self.CODE_LENGTH = 6
        self.CODE_CHARACTERS = string.ascii_uppercase + string.digits  # A-Z, 0-9
        self.MAX_GENERATION_ATTEMPTS = 10
        
        logger.info("ReferralService initialized")
    
    def generate_referral_code(self) -> str:
        """
        Generate a unique 6-character alphanumeric referral code
        Format: Random sequence of A-Z and 0-9 (e.g., A7B2K9, 3X8M1P)
        """
        for attempt in range(self.MAX_GENERATION_ATTEMPTS):
            # Generate random code
            code = ''.join(random.choices(self.CODE_CHARACTERS, k=self.CODE_LENGTH))
            
            # Check for uniqueness in database
            try:
                existing_code = self.supabase.table("user_profiles").select("id").eq(
                    "referral_code", code
                ).execute()
                
                if not existing_code.data:
                    logger.info(f"Generated unique referral code: {code} (attempt {attempt + 1})")
                    return code
                else:
                    logger.debug(f"Code collision detected: {code}, retrying...")
                    
            except Exception as e:
                logger.error(f"Error checking code uniqueness: {e}")
                # Continue to next attempt
                
        # If we reach here, we couldn't generate a unique code
        logger.error(f"Failed to generate unique referral code after {self.MAX_GENERATION_ATTEMPTS} attempts")
        raise Exception("Unable to generate unique referral code")
    
    async def assign_referral_code_to_user(self, user_id: str) -> str:
        """
        Generate and assign a referral code to a user
        Returns the generated code
        """
        try:
            # Check if user already has a referral code
            user_profile = self.supabase.table("user_profiles").select(
                "referral_code"
            ).eq("id", user_id).single().execute()
            
            if not user_profile.data:
                logger.error(f"User profile not found for user_id: {user_id}")
                raise Exception("User profile not found")
            
            existing_code = user_profile.data.get('referral_code')
            if existing_code:
                logger.info(f"User {user_id} already has referral code: {existing_code}")
                return existing_code
            
            # Generate new referral code
            referral_code = self.generate_referral_code()
            
            # Update user profile with referral code
            update_result = self.supabase.table("user_profiles").update({
                "referral_code": referral_code,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            if not update_result.data:
                logger.error(f"Failed to update user profile with referral code for user_id: {user_id}")
                raise Exception("Failed to assign referral code")
            
            logger.info(f"Successfully assigned referral code {referral_code} to user {user_id}")
            return referral_code
            
        except Exception as e:
            logger.error(f"Error assigning referral code to user {user_id}: {e}")
            raise
    
    async def validate_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """
        Validate a referral code and return the referring user's information
        Returns None if code is invalid
        """
        try:
            if not referral_code or len(referral_code) != self.CODE_LENGTH:
                logger.debug(f"Invalid referral code format: {referral_code}")
                return None
            
            # Clean and uppercase the code
            clean_code = referral_code.strip().upper()
            
            # Look up the referring user
            referring_user = self.supabase.table("user_profiles").select(
                "id, email, referral_code"
            ).eq("referral_code", clean_code).single().execute()
            
            if not referring_user.data:
                logger.debug(f"Referral code not found: {clean_code}")
                return None
            
            user_data = referring_user.data
            logger.info(f"Valid referral code {clean_code} belongs to user {user_data['id']}")
            
            return {
                "referring_user_id": user_data['id'],
                "referring_user_email": user_data['email'],
                "referral_code": user_data['referral_code']
            }
            
        except Exception as e:
            logger.error(f"Error validating referral code {referral_code}: {e}")
            return None
    
    async def create_referral_relationship(self, referring_user_id: str, referred_user_id: str, referral_code: str) -> bool:
        """
        Create a referral relationship between two users
        Returns True if successful, False otherwise
        """
        try:
            # Validate that users exist and are different
            if referring_user_id == referred_user_id:
                logger.warning(f"User {referred_user_id} attempted to refer themselves")
                return False
            
            # Check if referred user already has a referral relationship
            existing_relationship = self.supabase.table("referral_relationships").select("id").eq(
                "referred_user_id", referred_user_id
            ).execute()
            
            if existing_relationship.data:
                logger.warning(f"User {referred_user_id} already has a referral relationship")
                return False
            
            # Create referral relationship record
            relationship_data = {
                "id": str(uuid.uuid4()),
                "referring_user_id": referring_user_id,
                "referred_user_id": referred_user_id,
                "referral_code_used": referral_code,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            relationship_result = self.supabase.table("referral_relationships").insert(
                relationship_data
            ).execute()
            
            if not relationship_result.data:
                logger.error(f"Failed to create referral relationship: {relationship_data}")
                return False
            
            # Update referred user's profile with referring user ID
            profile_update = self.supabase.table("user_profiles").update({
                "referred_by": referring_user_id,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", referred_user_id).execute()
            
            if not profile_update.data:
                logger.error(f"Failed to update referred user profile: {referred_user_id}")
                # Note: We don't return False here as the relationship was created
            
            logger.info(f"Successfully created referral relationship: {referring_user_id} -> {referred_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating referral relationship: {e}")
            return False
    
    async def get_user_referral_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive referral information for a user
        """
        try:
            # Get user's own referral code and who referred them
            user_profile = self.supabase.table("user_profiles").select(
                "referral_code, referred_by"
            ).eq("id", user_id).single().execute()
            
            if not user_profile.data:
                logger.error(f"User profile not found: {user_id}")
                return {}
            
            profile_data = user_profile.data
            referral_info = {
                "user_id": user_id,
                "referral_code": profile_data.get('referral_code'),
                "referred_by": profile_data.get('referred_by'),
                "referring_user_info": None,
                "referrals_made": [],
                "total_referrals": 0
            }
            
            # Get information about who referred this user
            if profile_data.get('referred_by'):
                referring_user = self.supabase.table("user_profiles").select(
                    "id, email"
                ).eq("id", profile_data['referred_by']).single().execute()
                
                if referring_user.data:
                    referral_info["referring_user_info"] = {
                        "user_id": referring_user.data['id'],
                        "email": referring_user.data['email']
                    }
            
            # Get list of users this user has referred
            referrals_made = self.supabase.table("referral_relationships").select(
                "referred_user_id, referral_code_used, created_at, status"
            ).eq("referring_user_id", user_id).order("created_at", desc=True).execute()
            
            if referrals_made.data:
                # Get referred users' email addresses
                referred_user_ids = [r['referred_user_id'] for r in referrals_made.data]
                referred_users = self.supabase.table("user_profiles").select(
                    "id, email"
                ).in_("id", referred_user_ids).execute()
                
                # Create lookup dict for emails
                email_lookup = {user['id']: user['email'] for user in referred_users.data}
                
                # Build referrals list with email information
                for referral in referrals_made.data:
                    referral_info["referrals_made"].append({
                        "referred_user_id": referral['referred_user_id'],
                        "referred_user_email": email_lookup.get(referral['referred_user_id'], 'Unknown'),
                        "referral_code_used": referral['referral_code_used'],
                        "created_at": referral['created_at'],
                        "status": referral['status']
                    })
                
                referral_info["total_referrals"] = len(referrals_made.data)
            
            logger.info(f"Retrieved referral info for user {user_id}: {referral_info['total_referrals']} referrals made")
            return referral_info
            
        except Exception as e:
            logger.error(f"Error getting referral info for user {user_id}: {e}")
            return {}
    
    async def get_referral_rewards_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get referral rewards summary for a user
        """
        try:
            # Get all referral rewards for this user
            rewards = self.supabase.table("referral_rewards").select(
                "*"
            ).eq("referring_user_id", user_id).order("created_at", desc=True).execute()
            
            if not rewards.data:
                return {
                    "user_id": user_id,
                    "total_rewards": 0,
                    "total_paid": 0,
                    "pending_rewards": 0,
                    "rewards_history": []
                }
            
            total_rewards = 0
            total_paid = 0
            pending_rewards = 0
            
            for reward in rewards.data:
                amount = reward.get('reward_amount', 0)
                status = reward.get('status', 'pending')
                
                total_rewards += amount
                if status == 'paid':
                    total_paid += amount
                elif status in ['pending', 'calculated']:
                    pending_rewards += amount
            
            return {
                "user_id": user_id,
                "total_rewards": total_rewards,
                "total_paid": total_paid,
                "pending_rewards": pending_rewards,
                "rewards_history": rewards.data
            }
            
        except Exception as e:
            logger.error(f"Error getting referral rewards for user {user_id}: {e}")
            return {}
