#!/usr/bin/env python3
"""
Investigate testuser3@email.com subscription status in Stripe vs Database
"""

import os
import sys
import asyncio
import stripe
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

async def investigate_user_subscription():
    """Investigate testuser3@email.com subscription discrepancy"""
    print("INVESTIGATING testuser3@email.com SUBSCRIPTION STATUS")
    print("=" * 60)
    
    email = "testuser3@email.com"
    
    # Get user from database
    user_response = supabase.table("user_profiles").select(
        "id, email, subscription_status, plan_tier, stripe_customer_id, last_payment_at"
    ).eq("email", email).single().execute()
    
    if not user_response.data:
        print(f"[ERROR] User {email} not found in database")
        return
    
    user_data = user_response.data
    stripe_customer_id = user_data['stripe_customer_id']
    
    print(f"[DATABASE] User Profile:")
    print(f"  Email: {user_data['email']}")
    print(f"  Subscription Status: {user_data['subscription_status']}")
    print(f"  Plan Tier: {user_data['plan_tier']}")
    print(f"  Last Payment: {user_data['last_payment_at']}")
    print(f"  Stripe Customer ID: {stripe_customer_id}")
    
    # Get subscription from database
    sub_response = supabase.table("user_subscriptions").select(
        "stripe_subscription_id, status, current_period_start, current_period_end"
    ).eq("user_id", user_data['id']).execute()
    
    if sub_response.data:
        db_sub = sub_response.data[0]
        stripe_sub_id = db_sub['stripe_subscription_id']
        print(f"\n[DATABASE] Subscription Record:")
        print(f"  Stripe Subscription ID: {stripe_sub_id}")
        print(f"  Status: {db_sub['status']}")
        print(f"  Period: {db_sub['current_period_start']} to {db_sub['current_period_end']}")
        
        # Now check Stripe
        print(f"\n[STRIPE] Checking subscription {stripe_sub_id}...")
        try:
            stripe_subscription = stripe.Subscription.retrieve(stripe_sub_id)
            print(f"  Status: {stripe_subscription.status}")
            print(f"  Created: {stripe_subscription.created}")
            
            # Convert timestamps to readable format
            from datetime import datetime
            try:
                start_date = datetime.fromtimestamp(stripe_subscription.current_period_start)
                end_date = datetime.fromtimestamp(stripe_subscription.current_period_end)
                print(f"  Current Period: {start_date} to {end_date}")
            except Exception as ts_error:
                print(f"  Period timestamps: {stripe_subscription.current_period_start} to {stripe_subscription.current_period_end}")
            
            # Check latest invoice
            if stripe_subscription.latest_invoice:
                try:
                    invoice = stripe.Invoice.retrieve(stripe_subscription.latest_invoice)
                    print(f"  Latest Invoice: {invoice.id}")
                    print(f"  Invoice Status: {invoice.status}")
                    print(f"  Amount Paid: ${invoice.amount_paid / 100}")
                    print(f"  Amount Due: ${invoice.amount_due / 100}")
                    print(f"  Payment Intent: {invoice.payment_intent}")
                    
                    # Check payment intent if exists
                    if invoice.payment_intent:
                        payment_intent = stripe.PaymentIntent.retrieve(invoice.payment_intent)
                        print(f"  Payment Intent Status: {payment_intent.status}")
                        print(f"  Payment Amount: ${payment_intent.amount / 100}")
                        if hasattr(payment_intent, 'charges') and payment_intent.charges.data:
                            charge = payment_intent.charges.data[0]
                            print(f"  Charge Status: {charge.status}")
                            print(f"  Charge Amount: ${charge.amount / 100}")
                except Exception as invoice_error:
                    print(f"  [ERROR] Failed to retrieve invoice: {str(invoice_error)}")
            
            # Check customer
            try:
                customer = stripe.Customer.retrieve(stripe_customer_id)
                print(f"\n[STRIPE] Customer:")
                print(f"  Email: {customer.email}")
                print(f"  Created: {datetime.fromtimestamp(customer.created)}")
            except Exception as customer_error:
                print(f"  [ERROR] Failed to retrieve customer: {str(customer_error)}")
            
        except Exception as e:
            print(f"[ERROR] Failed to retrieve Stripe subscription: {str(e)}")
    
    else:
        print(f"\n[ERROR] No subscription record found in database")
    
    # Check payment transactions
    payment_response = supabase.table("payment_transactions").select(
        "stripe_payment_intent_id, amount_paid, status, created_at"
    ).eq("user_id", user_data['id']).execute()
    
    print(f"\n[DATABASE] Payment Transactions: {len(payment_response.data)} found")
    for payment in payment_response.data:
        print(f"  Payment Intent: {payment['stripe_payment_intent_id']}")
        print(f"  Amount: ${payment['amount_paid']}")
        print(f"  Status: {payment['status']}")
        print(f"  Created: {payment['created_at']}")

if __name__ == "__main__":
    asyncio.run(investigate_user_subscription())
