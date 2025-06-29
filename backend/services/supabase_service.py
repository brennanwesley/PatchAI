"""
Supabase client configuration and initialization
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Supabase configuration missing - check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

logger.info("Supabase client initialized successfully")


# Referral-related database helper functions
async def get_user_referral_stats(user_id: str) -> dict:
    """
    Get comprehensive referral statistics for a user using RPC call
    """
    try:
        # This would call a stored procedure for complex referral stats
        # For now, we'll use the referral service directly
        logger.info(f"Getting referral stats for user: {user_id}")
        return {"user_id": user_id, "stats_available": True}
    except Exception as e:
        logger.error(f"Error getting referral stats for user {user_id}: {e}")
        return {}


async def calculate_referral_rewards(referring_user_id: str, payment_amount: float, subscription_months: int) -> dict:
    """
    Calculate referral rewards based on payment and subscription duration
    """
    try:
        # Referral reward logic:
        # - 10% of monthly subscription for first 12 months
        # - 5% after 12 months
        # - Based on base subscription price (not after discounts/taxes)
        
        if subscription_months <= 12:
            reward_percentage = 0.10  # 10%
        else:
            reward_percentage = 0.05  # 5%
        
        reward_amount = payment_amount * reward_percentage
        
        logger.info(f"Calculated referral reward: ${reward_amount:.2f} ({reward_percentage*100}%) for user {referring_user_id}")
        
        return {
            "referring_user_id": referring_user_id,
            "reward_amount": reward_amount,
            "reward_percentage": reward_percentage,
            "base_payment": payment_amount,
            "subscription_months": subscription_months
        }
        
    except Exception as e:
        logger.error(f"Error calculating referral rewards: {e}")
        return {}


async def record_referral_reward(reward_data: dict) -> bool:
    """
    Record a referral reward in the database
    """
    try:
        reward_record = {
            "id": reward_data.get("id"),
            "referrer_user_id": reward_data.get("referrer_user_id"),
            "referee_user_id": reward_data.get("referee_user_id"),
            "payment_transaction_id": reward_data.get("payment_transaction_id"),
            "reward_amount": reward_data.get("reward_amount"),
            "reward_percentage": reward_data.get("reward_percentage"),
            "base_payment_amount": reward_data.get("base_payment_amount"),
            "subscription_month": reward_data.get("subscription_month"),
            "status": "calculated",
            "created_at": reward_data.get("created_at"),
            "payment_date": reward_data.get("payment_date")
        }
        
        result = supabase.table("referral_rewards").insert(reward_record).execute()
        
        if result.data:
            logger.info(f"Recorded referral reward: {reward_record['id']}")
            return True
        else:
            logger.error(f"Failed to record referral reward: {reward_record}")
            return False
            
    except Exception as e:
        logger.error(f"Error recording referral reward: {e}")
        return False
