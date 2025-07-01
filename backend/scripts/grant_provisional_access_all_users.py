#!/usr/bin/env python3
"""
Grant 7-day provisional access to ALL existing users without active paid subscriptions
This ensures all users get automatic 7-day access as requested
"""

import os
import sys
import logging
from datetime import datetime, timedelta, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def grant_provisional_access_to_all():
    """
    Grant 7-day provisional access to all users without active paid subscriptions
    """
    try:
        # Use the global supabase client from supabase_service
        if not supabase:
            logger.error("Supabase client not available")
            return False
        
        logger.info("🔍 Finding users who need 7-day provisional access...")
        
        # Get all users who don't have active paid subscriptions
        # This includes users with 'inactive', 'none', or null subscription status
        users_response = supabase.table("user_profiles").select(
            "id, email, subscription_status, plan_tier, provisional_access_until, created_at"
        ).execute()
        
        if not users_response.data:
            logger.warning("No users found in database")
            return False
        
        all_users = users_response.data
        logger.info(f"📊 Found {len(all_users)} total users in database")
        
        # Filter users who need provisional access
        users_needing_access = []
        
        for user in all_users:
            user_id = user['id']
            email = user['email']
            subscription_status = user.get('subscription_status', 'inactive')
            plan_tier = user.get('plan_tier', 'none')
            provisional_until = user.get('provisional_access_until')
            
            # Check if user needs provisional access
            needs_access = False
            reason = ""
            
            # Case 1: No active paid subscription
            if subscription_status not in ['active']:
                needs_access = True
                reason = f"subscription_status: {subscription_status}"
            
            # Case 2: Active subscription but no plan tier (edge case)
            elif subscription_status == 'active' and plan_tier in ['none', None]:
                needs_access = True
                reason = f"active status but plan_tier: {plan_tier}"
            
            # Case 3: Has provisional access but it's expired
            elif provisional_until:
                try:
                    if provisional_until.endswith('Z'):
                        expiry_time = datetime.fromisoformat(provisional_until.replace('Z', '+00:00'))
                    elif '+' in provisional_until:
                        expiry_time = datetime.fromisoformat(provisional_until)
                    else:
                        expiry_time = datetime.fromisoformat(provisional_until).replace(tzinfo=timezone.utc)
                    
                    current_time = datetime.now(timezone.utc)
                    if current_time > expiry_time:
                        needs_access = True
                        reason = f"provisional access expired at {provisional_until}"
                except Exception as e:
                    logger.warning(f"Error parsing provisional_until for {email}: {e}")
                    needs_access = True
                    reason = "invalid provisional_until format"
            
            if needs_access:
                users_needing_access.append({
                    'id': user_id,
                    'email': email,
                    'current_status': subscription_status,
                    'current_tier': plan_tier,
                    'reason': reason
                })
        
        logger.info(f"🎯 Found {len(users_needing_access)} users who need 7-day provisional access")
        
        if not users_needing_access:
            logger.info("✅ All users already have active access - no action needed")
            return True
        
        # Calculate 7-day expiration
        current_utc = datetime.now(timezone.utc)
        provisional_until = current_utc + timedelta(hours=168)  # 7 days
        
        logger.info(f"⏰ Granting provisional access until: {provisional_until}")
        
        # Grant provisional access to all users who need it
        success_count = 0
        error_count = 0
        
        for user in users_needing_access:
            try:
                user_id = user['id']
                email = user['email']
                reason = user['reason']
                
                # Update user profile with 7-day provisional access
                update_response = supabase.table("user_profiles").update({
                    "subscription_status": "active",
                    "plan_tier": "standard",
                    "provisional_access_until": provisional_until.isoformat(),
                    "provisional_plan_tier": "standard"
                }).eq("id", user_id).execute()
                
                if update_response.data:
                    logger.info(f"✅ Granted 7-day access to {email} (reason: {reason})")
                    success_count += 1
                else:
                    logger.error(f"❌ Failed to update {email} - no data returned")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error granting access to {user['email']}: {e}")
                error_count += 1
        
        # Summary
        logger.info(f"\n📊 PROVISIONAL ACCESS GRANT SUMMARY:")
        logger.info(f"   Total users processed: {len(users_needing_access)}")
        logger.info(f"   ✅ Successfully granted: {success_count}")
        logger.info(f"   ❌ Errors: {error_count}")
        logger.info(f"   ⏰ Access expires: {provisional_until}")
        
        if success_count > 0:
            logger.info(f"\n🎉 SUCCESS: {success_count} users now have 7-day provisional access!")
        
        return error_count == 0
        
    except Exception as e:
        logger.error(f"❌ Critical error in grant_provisional_access_to_all: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("🚀 Starting 7-day provisional access grant for all users...")
    
    success = grant_provisional_access_to_all()
    
    if success:
        logger.info("✅ Provisional access grant completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Provisional access grant failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
