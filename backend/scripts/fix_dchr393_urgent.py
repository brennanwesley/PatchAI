#!/usr/bin/env python3
"""
URGENT FIX: dchr393@gmail.com subscription sync
- User has 2 ACTIVE Stripe subscriptions but DB shows inactive
- Wrong Stripe customer ID in database
- Missing subscription and payment records
"""

import os
import sys
import asyncio
import stripe
from dotenv import load_dotenv
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

async def fix_dchr393_urgent():
    """URGENT: Fix dchr393@gmail.com subscription sync"""
    print("[URGENT FIX] dchr393@gmail.com")
    print("=" * 50)
    
    email = "dchr393@gmail.com"
    correct_stripe_customer_id = "cus_SYGu0vYFP49wO4"  # Found from investigation
    
    # Step 1: Get user from database
    print("[Step 1] Getting user from database...")
    user_response = supabase.table("user_profiles").select(
        "id, email, subscription_status, plan_tier, stripe_customer_id"
    ).eq("email", email).single().execute()
    
    if not user_response.data:
        print(f"[ERROR] User {email} not found in database")
        return
    
    user_data = user_response.data
    user_id = user_data['id']
    
    print(f"[SUCCESS] User found: {user_id}")
    print(f"   Current status: {user_data['subscription_status']}")
    print(f"   Current plan: {user_data['plan_tier']}")
    print(f"   Current Stripe ID: {user_data['stripe_customer_id']}")
    
    # Step 2: Get Stripe subscription details
    print(f"\n[Step 2] Getting Stripe subscription details...")
    
    try:
        # Get customer subscriptions
        subscriptions = stripe.Subscription.list(customer=correct_stripe_customer_id, limit=10)
        print(f"[SUCCESS] Found {len(subscriptions.data)} subscriptions")
        
        active_subscriptions = [s for s in subscriptions.data if s.status == 'active']
        print(f"[SUCCESS] Active subscriptions: {len(active_subscriptions)}")
        
        if not active_subscriptions:
            print("[ERROR] No active subscriptions found")
            return
        
        # Use the first active subscription (we'll handle the duplicate later)
        primary_subscription = active_subscriptions[0]
        print(f"[SUCCESS] Primary subscription: {primary_subscription.id}")
        print(f"   Status: {primary_subscription.status}")
        print(f"   Created: {datetime.fromtimestamp(primary_subscription.created)}")
        
        # Get pricing info
        if hasattr(primary_subscription, 'items') and primary_subscription.items and len(primary_subscription.items.data) > 0:
            price_info = primary_subscription.items.data[0].price
            monthly_amount = price_info.unit_amount / 100
            print(f"   Price: ${monthly_amount} {price_info.currency}")
        else:
            print("   Price: Unable to retrieve pricing info")
            price_info = None
            monthly_amount = 9.98  # Default standard plan price
        
        # Get invoices to find payments
        invoices = stripe.Invoice.list(customer=correct_stripe_customer_id, limit=20)
        paid_invoices = [inv for inv in invoices.data if inv.status == 'paid']
        print(f"[SUCCESS] Found {len(paid_invoices)} paid invoices")
        
        total_paid = sum(inv.amount_paid / 100 for inv in paid_invoices)
        print(f"[SUCCESS] Total amount paid: ${total_paid}")
        
    except Exception as e:
        print(f"[ERROR] Getting Stripe data: {str(e)}")
        return
    
    # Step 3: Update database with correct information
    print(f"\n[Step 3] Updating database...")
    
    try:
        # Update user_profiles with correct Stripe customer ID and status
        print("[UPDATING] user_profiles...")
        profile_update = supabase.table("user_profiles").update({
            "stripe_customer_id": correct_stripe_customer_id,
            "subscription_status": "active",
            "plan_tier": "standard",
            "last_payment_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        print("[SUCCESS] user_profiles updated")
        
        # Create user_subscriptions record
        print("[CREATING] user_subscriptions record...")
        subscription_data = {
            "user_id": user_id,
            "stripe_subscription_id": primary_subscription.id,
            "stripe_customer_id": correct_stripe_customer_id,
            "status": "active",
            "current_period_start": datetime.fromtimestamp(primary_subscription.current_period_start).isoformat(),
            "current_period_end": datetime.fromtimestamp(primary_subscription.current_period_end).isoformat(),
            "plan_id": price_info.id if price_info else "price_1RZlGdGKwE0ADhm7VQs8fJzl",
            "quantity": 1
        }
        
        subscription_insert = supabase.table("user_subscriptions").insert(subscription_data).execute()
        print("[SUCCESS] user_subscriptions record created")
        
        # Create payment_transactions records for each paid invoice
        print("[CREATING] payment_transactions records...")
        for invoice in paid_invoices:
            payment_data = {
                "user_id": user_id,
                "stripe_payment_intent_id": invoice.payment_intent,
                "stripe_invoice_id": invoice.id,
                "stripe_customer_id": correct_stripe_customer_id,
                "amount_paid": invoice.amount_paid / 100,
                "currency": invoice.currency,
                "status": "succeeded",
                "created_at": datetime.fromtimestamp(invoice.created).isoformat()
            }
            
            payment_insert = supabase.table("payment_transactions").insert(payment_data).execute()
            print(f"[SUCCESS] Payment record created: ${invoice.amount_paid / 100} on {datetime.fromtimestamp(invoice.created)}")
        
        print(f"\n[SUCCESS] dchr393@gmail.com has been fixed!")
        print(f"   [SUCCESS] Stripe customer ID updated: {correct_stripe_customer_id}")
        print(f"   [SUCCESS] Subscription status: active")
        print(f"   [SUCCESS] Plan tier: standard")
        print(f"   [SUCCESS] Subscription record created")
        print(f"   [SUCCESS] {len(paid_invoices)} payment records created")
        print(f"   [SUCCESS] Total payments recorded: ${total_paid}")
        
        # Handle duplicate subscription warning
        if len(active_subscriptions) > 1:
            print(f"\n[WARNING] User has {len(active_subscriptions)} active subscriptions:")
            for i, sub in enumerate(active_subscriptions):
                print(f"   {i+1}. {sub.id} - {sub.status}")
            print("   Consider canceling duplicate subscriptions to avoid double billing")
        
    except Exception as e:
        print(f"[ERROR] Updating database: {str(e)}")
        return
    
    # Step 4: Verification
    print(f"\n[Step 4] Verification...")
    
    try:
        # Verify user_profiles
        verify_profile = supabase.table("user_profiles").select(
            "subscription_status, plan_tier, stripe_customer_id"
        ).eq("id", user_id).single().execute()
        
        profile = verify_profile.data
        print(f"[SUCCESS] Profile verification:")
        print(f"   Status: {profile['subscription_status']}")
        print(f"   Plan: {profile['plan_tier']}")
        print(f"   Stripe ID: {profile['stripe_customer_id']}")
        
        # Verify subscriptions
        verify_subs = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
        print(f"[SUCCESS] Subscription records: {len(verify_subs.data)}")
        
        # Verify payments
        verify_payments = supabase.table("payment_transactions").select("*").eq("user_id", user_id).execute()
        print(f"[SUCCESS] Payment records: {len(verify_payments.data)}")
        
        print(f"\n[COMPLETE] DCHR393@GMAIL.COM FIX COMPLETE!")
        print(f"User can now access paid features immediately.")
        
    except Exception as e:
        print(f"[ERROR] During verification: {str(e)}")

if __name__ == "__main__":
    asyncio.run(fix_dchr393_urgent())
