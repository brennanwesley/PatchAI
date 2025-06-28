#!/usr/bin/env python3
"""
Fix testuser3@email.com subscription sync issue
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

async def fix_testuser3_subscription():
    """Fix testuser3@email.com subscription sync issue"""
    print("FIXING testuser3@email.com SUBSCRIPTION SYNC")
    print("=" * 50)
    
    email = "testuser3@email.com"
    
    # Get user from database
    user_response = supabase.table("user_profiles").select(
        "id, email, subscription_status, plan_tier, stripe_customer_id"
    ).eq("email", email).single().execute()
    
    if not user_response.data:
        print(f"[ERROR] User {email} not found in database")
        return
    
    user_data = user_response.data
    user_id = user_data['id']
    stripe_customer_id = user_data['stripe_customer_id']
    
    print(f"[DATABASE] Current Status:")
    print(f"  Email: {user_data['email']}")
    print(f"  Subscription Status: {user_data['subscription_status']}")
    print(f"  Plan Tier: {user_data['plan_tier']}")
    
    # Get subscription from database
    sub_response = supabase.table("user_subscriptions").select(
        "id, stripe_subscription_id, status"
    ).eq("user_id", user_id).execute()
    
    if not sub_response.data:
        print(f"[ERROR] No subscription record found in database")
        return
    
    db_sub = sub_response.data[0]
    stripe_sub_id = db_sub['stripe_subscription_id']
    
    print(f"[DATABASE] Subscription: {stripe_sub_id} (status: {db_sub['status']})")
    
    # Check Stripe subscription
    try:
        stripe_subscription = stripe.Subscription.retrieve(stripe_sub_id)
        print(f"[STRIPE] Subscription Status: {stripe_subscription.status}")
        
        if stripe_subscription.status == 'active':
            print(f"[STRIPE] SUCCESS: Subscription is ACTIVE in Stripe")
            
            # Get latest invoice to check payment
            if stripe_subscription.latest_invoice:
                invoice = stripe.Invoice.retrieve(stripe_subscription.latest_invoice)
                print(f"[STRIPE] Latest Invoice: {invoice.id}")
                print(f"[STRIPE] Invoice Status: {invoice.status}")
                print(f"[STRIPE] Amount Paid: ${invoice.amount_paid / 100}")
                
                if invoice.status == 'paid' and invoice.amount_paid > 0:
                    print(f"[STRIPE] SUCCESS: Payment SUCCESSFUL: ${invoice.amount_paid / 100}")
                    
                    # Update database to match Stripe
                    print(f"\n[FIX] Updating database to match Stripe...")
                    
                    # Update user_profiles
                    profile_update = supabase.table("user_profiles").update({
                        "subscription_status": "active",
                        "last_payment_at": datetime.now().isoformat()
                    }).eq("id", user_id).execute()
                    
                    if profile_update.data:
                        print(f"[FIX] SUCCESS: Updated user_profiles: subscription_status = active")
                    
                    # Update user_subscriptions
                    sub_update = supabase.table("user_subscriptions").update({
                        "status": "active"
                    }).eq("id", db_sub['id']).execute()
                    
                    if sub_update.data:
                        print(f"[FIX] SUCCESS: Updated user_subscriptions: status = active")
                    
                    # Create payment transaction record
                    payment_intent_id = None
                    try:
                        payment_intent_id = invoice.payment_intent if hasattr(invoice, 'payment_intent') and invoice.payment_intent else f"manual_sync_{invoice.id}"
                    except:
                        payment_intent_id = f"manual_sync_{invoice.id}"
                    
                    payment_data = {
                        "user_id": user_id,
                        "subscription_id": db_sub['id'],
                        "stripe_payment_intent_id": payment_intent_id,
                        "stripe_invoice_id": invoice.id,
                        "amount_paid": invoice.amount_paid / 100,
                        "currency": invoice.currency,
                        "status": "succeeded",
                        "payment_method": "card",
                        "metadata": {"sync_source": "manual_fix", "original_invoice": invoice.id}
                    }
                    
                    payment_insert = supabase.table("payment_transactions").insert(payment_data).execute()
                    
                    if payment_insert.data:
                        print(f"[FIX] SUCCESS: Created payment transaction record")
                    
                    print(f"\n[SUCCESS] testuser3@email.com subscription sync FIXED!")
                    print(f"  Database now matches Stripe: ACTIVE subscription")
                    print(f"  Payment record created for ${invoice.amount_paid / 100}")
                    
                else:
                    print(f"[WARNING] Invoice not paid or amount is 0")
            else:
                print(f"[WARNING] No latest invoice found")
        else:
            print(f"[INFO] Stripe subscription status: {stripe_subscription.status}")
            print(f"[INFO] Database status appears correct")
            
    except Exception as e:
        print(f"[ERROR] Failed to retrieve Stripe subscription: {str(e)}")

if __name__ == "__main__":
    asyncio.run(fix_testuser3_subscription())
