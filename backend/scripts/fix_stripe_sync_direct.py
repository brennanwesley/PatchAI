#!/usr/bin/env python3
"""
Direct database fix for Stripe sync bug - bypass API authentication
These 3 users have paid on Stripe but webhook sync failed
"""

import os
import sys
import logging
import stripe
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

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

def get_stripe_subscription_for_customer(customer_id):
    """
    Get active Stripe subscription for a customer
    """
    try:
        # Get subscriptions for this customer
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=10
        )
        
        if subscriptions.data:
            return subscriptions.data[0]  # Return first active subscription
        else:
            logger.warning(f"No active subscriptions found for customer {customer_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Stripe subscription for {customer_id}: {e}")
        return None

def fix_user_subscription_direct(user_data):
    """
    Directly fix user subscription in database using Stripe data
    """
    try:
        email = user_data['email']
        user_id = user_data['user_id']
        customer_id = user_data['stripe_customer_id']
        
        logger.info(f"🔧 Fixing {email} directly via database...")
        
        # Get Stripe subscription data
        stripe_subscription = get_stripe_subscription_for_customer(customer_id)
        
        if not stripe_subscription:
            logger.error(f"❌ No active Stripe subscription found for {email}")
            return False
        
        subscription_id = stripe_subscription.id
        logger.info(f"📋 Found Stripe subscription: {subscription_id}")
        
        # Get Standard Plan ID from database
        plan_response = supabase.table("subscription_plans").select(
            "id, plan_name, monthly_price"
        ).eq("plan_name", "Standard Plan").execute()
        
        if not plan_response.data:
            logger.error("❌ Standard Plan not found in database")
            return False
        
        plan_data = plan_response.data[0]
        plan_id = plan_data['id']
        
        logger.info(f"📋 Using plan ID: {plan_id}")
        
        # Create user_subscriptions record
        current_time = datetime.now(timezone.utc)
        
        # Calculate next month for period end
        if current_time.month == 12:
            next_month = current_time.replace(year=current_time.year + 1, month=1)
        else:
            next_month = current_time.replace(month=current_time.month + 1)
        
        subscription_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "stripe_subscription_id": subscription_id,
            "status": "active",
            "current_period_start": current_time.isoformat(),
            "current_period_end": next_month.isoformat(),
            "cancel_at_period_end": False,
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
        
        # Insert subscription record
        sub_result = supabase.table("user_subscriptions").insert(subscription_data).execute()
        
        if not sub_result.data:
            logger.error(f"❌ Failed to create subscription record for {email}")
            return False
        
        logger.info(f"✅ Created subscription record for {email}")
        
        # Update user profile to remove provisional access
        profile_update = {
            "subscription_status": "active",
            "plan_tier": "standard",
            "provisional_access_until": None,
            "provisional_plan_tier": None,
            "last_payment_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
        
        profile_result = supabase.table("user_profiles").update(profile_update).eq("id", user_id).execute()
        
        if not profile_result.data:
            logger.error(f"❌ Failed to update profile for {email}")
            return False
        
        logger.info(f"✅ Updated profile for {email} - removed provisional access")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing {user_data['email']}: {e}")
        return False

def verify_fix(user_data):
    """
    Verify that the user is now properly synced
    """
    try:
        email = user_data['email']
        user_id = user_data['user_id']
        
        # Check user_profiles
        profile_response = supabase.table("user_profiles").select(
            "subscription_status, plan_tier, provisional_access_until, last_payment_at"
        ).eq("id", user_id).execute()
        
        # Check user_subscriptions  
        subscription_response = supabase.table("user_subscriptions").select(
            "stripe_subscription_id, status, plan_id"
        ).eq("user_id", user_id).execute()
        
        if not profile_response.data or not subscription_response.data:
            logger.error(f"❌ Missing data for {email}")
            return False
        
        profile_data = profile_response.data[0]
        subscription_data = subscription_response.data[0]
        
        # Check all conditions
        conditions = {
            "has_subscription": bool(subscription_data.get('stripe_subscription_id')),
            "is_active": profile_data.get('subscription_status') == 'active',
            "is_standard": profile_data.get('plan_tier') == 'standard',
            "no_provisional": profile_data.get('provisional_access_until') is None,
            "has_payment_date": profile_data.get('last_payment_at') is not None
        }
        
        all_good = all(conditions.values())
        
        if all_good:
            logger.info(f"✅ VERIFIED: {email} is now a proper paid subscriber")
            return True
        else:
            logger.warning(f"⚠️ PARTIAL: {email} conditions: {conditions}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying {user_data['email']}: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("🚀 Starting direct Stripe sync fix for 3 paid users...")
    
    success_count = 0
    total_users = len(AFFECTED_USERS)
    
    for user_data in AFFECTED_USERS:
        email = user_data['email']
        logger.info(f"\n📧 Processing {email}...")
        
        # Attempt to fix sync directly
        if fix_user_subscription_direct(user_data):
            # Verify the fix worked
            if verify_fix(user_data):
                success_count += 1
                logger.info(f"🎉 {email} successfully fixed and verified!")
            else:
                logger.warning(f"⚠️ {email} fix attempted but verification failed")
        else:
            logger.error(f"❌ {email} fix failed")
    
    # Summary
    logger.info(f"\n📊 DIRECT STRIPE SYNC FIX SUMMARY:")
    logger.info(f"   Total users processed: {total_users}")
    logger.info(f"   ✅ Successfully fixed: {success_count}")
    logger.info(f"   ❌ Failed: {total_users - success_count}")
    
    if success_count == total_users:
        logger.info("🎉 ALL USERS SUCCESSFULLY CONVERTED TO PAID SUBSCRIBERS!")
        return True
    else:
        logger.error("❌ Some users still need manual attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
