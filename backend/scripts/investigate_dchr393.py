#!/usr/bin/env python3
"""
URGENT: Investigate dchr393@gmail.com - User reports PAID TWICE in Stripe but shows inactive in DB
This is a CRITICAL sync issue that needs immediate resolution
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

async def investigate_dchr393():
    """URGENT: Investigate dchr393@gmail.com subscription discrepancy"""
    print("URGENT INVESTIGATION: dchr393@gmail.com")
    print("USER REPORTS: PAID TWICE IN STRIPE BUT SHOWS INACTIVE")
    print("=" * 60)
    
    email = "dchr393@gmail.com"
    
    # Get user from database
    user_response = supabase.table("user_profiles").select(
        "id, email, subscription_status, plan_tier, stripe_customer_id, last_payment_at, created_at"
    ).eq("email", email).single().execute()
    
    if not user_response.data:
        print(f"[ERROR] User {email} not found in database")
        return
    
    user_data = user_response.data
    user_id = user_data['id']
    stripe_customer_id = user_data['stripe_customer_id']
    
    print(f"[DATABASE] User Profile:")
    print(f"  Email: {user_data['email']}")
    print(f"  User ID: {user_id}")
    print(f"  Subscription Status: {user_data['subscription_status']}")
    print(f"  Plan Tier: {user_data['plan_tier']}")
    print(f"  Last Payment: {user_data['last_payment_at']}")
    print(f"  Account Created: {user_data['created_at']}")
    print(f"  Stripe Customer ID: {stripe_customer_id}")
    
    # Get subscription records from database
    sub_response = supabase.table("user_subscriptions").select(
        "id, stripe_subscription_id, status, current_period_start, current_period_end, created_at"
    ).eq("user_id", user_id).execute()
    
    print(f"\n[DATABASE] Subscription Records: {len(sub_response.data)} found")
    for i, sub in enumerate(sub_response.data):
        print(f"  Subscription {i+1}:")
        print(f"    ID: {sub['id']}")
        print(f"    Stripe Sub ID: {sub['stripe_subscription_id']}")
        print(f"    Status: {sub['status']}")
        print(f"    Period: {sub['current_period_start']} to {sub['current_period_end']}")
        print(f"    Created: {sub['created_at']}")
    
    # Get payment transactions from database
    payment_response = supabase.table("payment_transactions").select(
        "id, stripe_payment_intent_id, stripe_invoice_id, amount_paid, status, created_at"
    ).eq("user_id", user_id).execute()
    
    print(f"\n[DATABASE] Payment Transactions: {len(payment_response.data)} found")
    for i, payment in enumerate(payment_response.data):
        print(f"  Payment {i+1}:")
        print(f"    Payment Intent: {payment['stripe_payment_intent_id']}")
        print(f"    Invoice: {payment['stripe_invoice_id']}")
        print(f"    Amount: ${payment['amount_paid']}")
        print(f"    Status: {payment['status']}")
        print(f"    Created: {payment['created_at']}")
    
    # Now check Stripe - THIS IS THE CRITICAL PART
    print(f"\n[STRIPE] COMPREHENSIVE CHECK FOR {email}")
    print("=" * 50)
    
    if not stripe_customer_id:
        print("[ERROR] No Stripe customer ID found in database")
        # Try to find customer by email
        print("[STRIPE] Searching for customer by email...")
        try:
            customers = stripe.Customer.list(email=email, limit=10)
            if customers.data:
                for customer in customers.data:
                    print(f"[STRIPE] Found customer: {customer.id} ({customer.email})")
                    stripe_customer_id = customer.id
                    break
            else:
                print("[STRIPE] No customer found by email")
                return
        except Exception as e:
            print(f"[ERROR] Failed to search customers: {str(e)}")
            return
    
    # Initialize variables
    total_paid = 0
    subscriptions = None
    
    try:
        # Get customer details
        customer = stripe.Customer.retrieve(stripe_customer_id)
        print(f"[STRIPE] Customer Details:")
        print(f"  ID: {customer.id}")
        print(f"  Email: {getattr(customer, 'email', 'N/A')}")
        print(f"  Created: {datetime.fromtimestamp(customer.created)}")
        print(f"  Name: {getattr(customer, 'name', 'N/A')}")
        print(f"  Description: {getattr(customer, 'description', 'N/A')}")
        
        # Get all subscriptions for this customer
        subscriptions = stripe.Subscription.list(customer=stripe_customer_id, limit=10)
        print(f"\n[STRIPE] Subscriptions: {len(subscriptions.data)} found")
        
        for i, subscription in enumerate(subscriptions.data):
            print(f"  Subscription {i+1}:")
            print(f"    ID: {subscription.id}")
            print(f"    Status: {subscription.status}")
            print(f"    Created: {datetime.fromtimestamp(subscription.created)}")
            
            try:
                start_date = datetime.fromtimestamp(subscription.current_period_start)
                end_date = datetime.fromtimestamp(subscription.current_period_end)
                print(f"    Current Period: {start_date} to {end_date}")
            except:
                print(f"    Period: {subscription.current_period_start} to {subscription.current_period_end}")
            
            # Get subscription items and pricing
            if subscription.items and subscription.items.data:
                for item in subscription.items.data:
                    price = item.price
                    print(f"    Price: ${price.unit_amount / 100} {price.currency} ({price.recurring.interval})")
        
        # Get all invoices for this customer
        invoices = stripe.Invoice.list(customer=stripe_customer_id, limit=20)
        print(f"\n[STRIPE] Invoices: {len(invoices.data)} found")
        
        for i, invoice in enumerate(invoices.data):
            print(f"  Invoice {i+1}:")
            print(f"    ID: {invoice.id}")
            print(f"    Status: {invoice.status}")
            print(f"    Amount: ${invoice.amount_paid / 100} (due: ${invoice.amount_due / 100})")
            print(f"    Created: {datetime.fromtimestamp(invoice.created)}")
            print(f"    Payment Intent: {invoice.payment_intent}")
            
            if invoice.status == 'paid':
                total_paid += invoice.amount_paid / 100
        
        print(f"\n[STRIPE] TOTAL AMOUNT PAID: ${total_paid}")
        
        # Get payment intents
        payment_intents = stripe.PaymentIntent.list(customer=stripe_customer_id, limit=20)
        print(f"\n[STRIPE] Payment Intents: {len(payment_intents.data)} found")
        
        for i, pi in enumerate(payment_intents.data):
            print(f"  Payment Intent {i+1}:")
            print(f"    ID: {pi.id}")
            print(f"    Status: {pi.status}")
            print(f"    Amount: ${pi.amount / 100}")
            print(f"    Created: {datetime.fromtimestamp(pi.created)}")
            
    except Exception as e:
        print(f"[ERROR] Failed to retrieve Stripe data: {str(e)}")
        print(f"[ERROR] Exception details: {type(e).__name__}: {str(e)}")
        subscriptions = stripe.Subscription.list(customer=stripe_customer_id, limit=10) if stripe_customer_id else None
    
    print(f"\n[ANALYSIS] CRITICAL FINDINGS:")
    print(f"  Database Status: {user_data['subscription_status']}")
    print(f"  Database Payments: {len(payment_response.data)} records")
    print(f"  Stripe Total Paid: ${total_paid}")
    print(f"  Active Subscriptions: {len([s for s in subscriptions.data if s.status == 'active'])}")
    
    if total_paid > 0 and user_data['subscription_status'] != 'active':
        print(f"\n[CRITICAL] SYNC ISSUE CONFIRMED!")
        print(f"  User has paid ${total_paid} in Stripe but database shows '{user_data['subscription_status']}'")
        print(f"  This requires IMMEDIATE manual sync fix!")

if __name__ == "__main__":
    asyncio.run(investigate_dchr393())
