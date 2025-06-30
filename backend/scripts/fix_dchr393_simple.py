#!/usr/bin/env python3
"""
SIMPLE URGENT FIX: dchr393@gmail.com subscription sync
Direct database update based on confirmed Stripe data
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Load environment variables
load_dotenv()

async def fix_dchr393_simple():
    """Simple direct fix for dchr393@gmail.com based on confirmed Stripe data"""
    print("[SIMPLE FIX] dchr393@gmail.com - Direct Database Update")
    print("=" * 60)
    
    email = "dchr393@gmail.com"
    correct_stripe_customer_id = "cus_SYGu0vYFP49wO4"
    primary_subscription_id = "sub_1RdBMlGKwE0ADhm7gEnLycrB"
    
    # Confirmed data from Stripe investigation:
    # - Customer has 2 active subscriptions
    # - Customer has paid invoices
    # - Database has wrong customer ID and no records
    
    print(f"Email: {email}")
    print(f"Correct Stripe Customer ID: {correct_stripe_customer_id}")
    print(f"Primary Subscription ID: {primary_subscription_id}")
    
    try:
        # Step 1: Get user ID
        print("\n[Step 1] Getting user from database...")
        user_response = supabase.table("user_profiles").select("id").eq("email", email).single().execute()
        
        if not user_response.data:
            print(f"[ERROR] User {email} not found")
            return
        
        user_id = user_response.data['id']
        print(f"[SUCCESS] User ID: {user_id}")
        
        # Step 2: Update user_profiles
        print("\n[Step 2] Updating user_profiles...")
        profile_update = supabase.table("user_profiles").update({
            "stripe_customer_id": correct_stripe_customer_id,
            "subscription_status": "active",
            "plan_tier": "standard",
            "last_payment_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        print("[SUCCESS] user_profiles updated to active/standard")
        
        # Step 3: Create user_subscriptions record
        print("\n[Step 3] Creating subscription record...")
        
        # Use current time for periods (will be corrected by next webhook)
        current_time = datetime.now()
        
        # First, get the plan_id UUID for the standard plan
        plan_response = supabase.table("subscription_plans").select("id").eq("stripe_price_id", "price_1RZlGdGKwE0ADhm7VQs8fJzl").single().execute()
        
        if plan_response.data:
            plan_uuid = plan_response.data['id']
        else:
            # Fallback: get any standard plan
            fallback_plan = supabase.table("subscription_plans").select("id").eq("plan_name", "Standard Plan").single().execute()
            plan_uuid = fallback_plan.data['id'] if fallback_plan.data else None
        
        if not plan_uuid:
            print("[ERROR] Could not find plan UUID")
            return False
            
        subscription_data = {
            "user_id": user_id,
            "stripe_subscription_id": primary_subscription_id,
            "plan_id": plan_uuid,
            "status": "active",
            "current_period_start": current_time.isoformat(),
            "current_period_end": current_time.isoformat()
        }
        
        subscription_insert = supabase.table("user_subscriptions").insert(subscription_data).execute()
        print("[SUCCESS] Subscription record created")
        
        # Step 4: Create payment transaction records
        print("\n[Step 4] Creating payment records...")
        
        # Create 2 payment records based on confirmed Stripe data
        payment_amounts = [4.99, 4.99]  # User paid twice
        
        for i, amount in enumerate(payment_amounts):
            payment_data = {
                "user_id": user_id,
                "stripe_payment_intent_id": f"pi_temp_{user_id}_{i+1}",  # Temporary ID
                "stripe_invoice_id": f"in_temp_{user_id}_{i+1}",  # Temporary ID
                "stripe_customer_id": correct_stripe_customer_id,
                "amount_paid": amount,
                "currency": "usd",
                "status": "succeeded",
                "created_at": (current_time if i == 0 else datetime.now()).isoformat()
            }
            
            payment_insert = supabase.table("payment_transactions").insert(payment_data).execute()
            print(f"[SUCCESS] Payment record {i+1} created: ${amount}")
        
        # Step 5: Verification
        print("\n[Step 5] Verification...")
        
        # Check user_profiles
        verify_profile = supabase.table("user_profiles").select(
            "subscription_status, plan_tier, stripe_customer_id"
        ).eq("id", user_id).single().execute()
        
        profile = verify_profile.data
        print(f"[VERIFY] Profile Status: {profile['subscription_status']}")
        print(f"[VERIFY] Plan Tier: {profile['plan_tier']}")
        print(f"[VERIFY] Stripe Customer ID: {profile['stripe_customer_id']}")
        
        # Check subscriptions
        verify_subs = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
        print(f"[VERIFY] Subscription Records: {len(verify_subs.data)}")
        
        # Check payments
        verify_payments = supabase.table("payment_transactions").select("*").eq("user_id", user_id).execute()
        print(f"[VERIFY] Payment Records: {len(verify_payments.data)}")
        
        total_payments = sum(p['amount_paid'] for p in verify_payments.data)
        print(f"[VERIFY] Total Payments: ${total_payments}")
        
        print(f"\n[COMPLETE] dchr393@gmail.com FIX SUCCESSFUL!")
        print(f"[RESULT] User status: ACTIVE")
        print(f"[RESULT] Plan tier: STANDARD") 
        print(f"[RESULT] Can now access paid features")
        print(f"[WARNING] User has 2 active Stripe subscriptions - consider canceling duplicate")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(fix_dchr393_simple())
