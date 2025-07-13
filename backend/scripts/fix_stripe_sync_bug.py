#!/usr/bin/env python3
"""
Fix Stripe sync bug for 3 paid users who show as provisional in database
These users have paid on Stripe but webhook sync failed
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Users who need sync fix
AFFECTED_USERS = [
    {
        'email': 'pcolwell@rushpetroleum.com',
        'stripe_customer_id': 'cus_Sd7zEMGrEiGXD2',
        'user_id': 'cf06b8ea-29bf-4ad1-8bc4-c3a371815bb7'
    },
    {
        'email': 'stew460@hotmail.com', 
        'stripe_customer_id': 'cus_SbSNCNK8BEO8jD',
        'user_id': '7b493cd8-a635-45b0-9a21-d85b1619e0e6'
    },
    {
        'email': 'rachelle_wells@yahoo.com',
        'stripe_customer_id': 'cus_SbT5c797ynjLUa', 
        'user_id': '33dbf981-0a72-477c-bb19-68ef4de54e70'
    }
]

def fix_stripe_sync_for_user(user_data):
    """
    Fix Stripe sync for a single user using our manual sync endpoint
    """
    try:
        email = user_data['email']
        logger.info(f"🔧 Fixing Stripe sync for {email}...")
        
        # Use our existing manual sync endpoint
        sync_url = "https://patchai-backend.onrender.com/payments/sync-subscription"
        
        payload = {
            "user_email": email
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(sync_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Successfully synced {email}: {result.get('message', 'Success')}")
            return True
        else:
            logger.error(f"❌ Failed to sync {email}: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error syncing {user_data['email']}: {e}")
        return False

def verify_fix(user_data):
    """
    Verify that the user is now properly synced in database
    """
    try:
        email = user_data['email']
        user_id = user_data['user_id']
        
        # Check user_profiles
        profile_response = supabase.table("user_profiles").select(
            "subscription_status, plan_tier, provisional_access_until"
        ).eq("id", user_id).execute()
        
        # Check user_subscriptions  
        subscription_response = supabase.table("user_subscriptions").select(
            "stripe_subscription_id, status"
        ).eq("user_id", user_id).execute()
        
        profile_data = profile_response.data[0] if profile_response.data else {}
        subscription_data = subscription_response.data[0] if subscription_response.data else {}
        
        has_subscription = bool(subscription_data.get('stripe_subscription_id'))
        is_active = profile_data.get('subscription_status') == 'active'
        no_provisional = profile_data.get('provisional_access_until') is None
        
        if has_subscription and is_active and no_provisional:
            logger.info(f"✅ VERIFIED: {email} is now properly synced as paid subscriber")
            return True
        else:
            logger.warning(f"⚠️ PARTIAL: {email} sync incomplete - subscription: {has_subscription}, active: {is_active}, no_provisional: {no_provisional}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying {user_data['email']}: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("🚀 Starting Stripe sync bug fix for 3 paid users...")
    
    success_count = 0
    total_users = len(AFFECTED_USERS)
    
    for user_data in AFFECTED_USERS:
        email = user_data['email']
        logger.info(f"\n📧 Processing {email}...")
        
        # Attempt to fix sync
        if fix_stripe_sync_for_user(user_data):
            # Wait a moment for database to update
            import time
            time.sleep(2)
            
            # Verify the fix worked
            if verify_fix(user_data):
                success_count += 1
                logger.info(f"🎉 {email} successfully fixed and verified!")
            else:
                logger.warning(f"⚠️ {email} sync attempted but verification failed")
        else:
            logger.error(f"❌ {email} sync failed")
    
    # Summary
    logger.info(f"\n📊 STRIPE SYNC FIX SUMMARY:")
    logger.info(f"   Total users processed: {total_users}")
    logger.info(f"   ✅ Successfully fixed: {success_count}")
    logger.info(f"   ❌ Failed: {total_users - success_count}")
    
    if success_count == total_users:
        logger.info("🎉 ALL USERS SUCCESSFULLY SYNCED!")
        return True
    else:
        logger.error("❌ Some users still need manual attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
