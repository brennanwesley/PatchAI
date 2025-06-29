#!/usr/bin/env python3
"""
Emergency script to fix the specific sync issue for brennan.testuser1@email.com
This user has an active Stripe subscription but no database record
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stripe_webhooks import webhook_handler
from services.supabase_service import supabase

# Load environment variables
load_dotenv()

async def fix_brennan_sync():
    """Fix the specific sync issue for brennan.testuser1@email.com"""
    email = "brennan.testuser1@email.com"
    
    print(f"[FIX] EMERGENCY FIX: Fixing sync for {email}")
    print("=" * 60)
    
    # Step 1: Check current database state
    print("\n[STEP 1] Checking current database state...")
    
    user_response = supabase.table("user_profiles").select("*").eq("email", email).execute()
    if not user_response.data:
        print(f"[ERROR] User not found: {email}")
        return False
    
    user = user_response.data[0]
    user_id = user['id']
    print(f"[OK] User found: {user_id}")
    print(f"   Current status: {user['subscription_status']}")
    print(f"   Current tier: {user['plan_tier']}")
    print(f"   Stripe customer: {user['stripe_customer_id']}")
    
    # Check existing subscriptions
    existing_subs = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
    print(f"   Existing subscription records: {len(existing_subs.data)}")
    
    # Step 2: Run the sync process with detailed logging
    print("\n[STEP 2] Running sync process...")
    
    try:
        success = await webhook_handler.sync_subscription_from_stripe(email)
        print(f"   Sync result: {success}")
        
        if success:
            print("[SUCCESS] Sync completed successfully!")
        else:
            print("[FAILED] Sync failed - investigating...")
            
    except Exception as e:
        print(f"[ERROR] Sync error: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    # Step 3: Verify the results
    print("\n[STEP 3] Verifying results...")
    
    # Check user profile
    updated_user = supabase.table("user_profiles").select("*").eq("email", email).execute()
    if updated_user.data:
        user = updated_user.data[0]
        print(f"   Updated status: {user['subscription_status']}")
        print(f"   Updated tier: {user['plan_tier']}")
    
    # Check subscription records
    updated_subs = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
    print(f"   Subscription records after sync: {len(updated_subs.data)}")
    
    for sub in updated_subs.data:
        print(f"     - {sub['stripe_subscription_id']}: {sub['status']}")
    
    return success

async def main():
    """Main execution function"""
    print("EMERGENCY SYNC FIX FOR BRENNAN.TESTUSER1@EMAIL.COM")
    print("=" * 60)
    
    success = await fix_brennan_sync()
    
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Sync issue has been resolved!")
        print("   The user should now be able to use the sync button successfully.")
    else:
        print("[FAILED] Sync issue persists - manual intervention required.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
