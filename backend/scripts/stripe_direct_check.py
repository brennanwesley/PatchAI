#!/usr/bin/env python3
"""
Direct Stripe API check for dchr393@gmail.com
USER REPORTS: PAID TWICE but shows inactive in database
"""

import os
import sys
import stripe
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_stripe_customer():
    """Direct check of Stripe customer data"""
    print("DIRECT STRIPE CHECK: dchr393@gmail.com")
    print("USER REPORTS: PAID TWICE IN STRIPE")
    print("=" * 50)
    
    customer_id = "cus_SYHyVJ3iuN8Ejm"
    email = "dchr393@gmail.com"
    
    try:
        # Method 1: Get customer by ID
        print(f"[STRIPE] Retrieving customer {customer_id}...")
        customer = stripe.Customer.retrieve(customer_id)
        print(f"Customer object type: {type(customer)}")
        print(f"Customer data: {json.dumps(dict(customer), indent=2, default=str)}")
        
    except Exception as e:
        print(f"[ERROR] Failed to get customer by ID: {str(e)}")
        
    try:
        # Method 2: Search by email
        print(f"\n[STRIPE] Searching customers by email: {email}")
        customers = stripe.Customer.list(email=email, limit=10)
        print(f"Found {len(customers.data)} customers")
        
        for i, cust in enumerate(customers.data):
            print(f"\nCustomer {i+1}:")
            print(f"  ID: {cust.id}")
            print(f"  Email: {cust.get('email', 'N/A')}")
            print(f"  Created: {datetime.fromtimestamp(cust.get('created', 0))}")
            
            # Get subscriptions for this customer
            subs = stripe.Subscription.list(customer=cust.id, limit=10)
            print(f"  Subscriptions: {len(subs.data)}")
            
            for j, sub in enumerate(subs.data):
                print(f"    Sub {j+1}: {sub.id} - {sub.status}")
                if sub.status == 'active':
                    print(f"      ACTIVE SUBSCRIPTION FOUND!")
            
            # Get invoices for this customer
            invoices = stripe.Invoice.list(customer=cust.id, limit=20)
            print(f"  Invoices: {len(invoices.data)}")
            
            total_paid = 0
            paid_invoices = []
            
            for inv in invoices.data:
                if inv.status == 'paid' and inv.amount_paid > 0:
                    amount = inv.amount_paid / 100
                    total_paid += amount
                    paid_invoices.append({
                        'id': inv.id,
                        'amount': amount,
                        'date': datetime.fromtimestamp(inv.created),
                        'payment_intent': inv.payment_intent
                    })
            
            print(f"  TOTAL PAID: ${total_paid}")
            print(f"  PAID INVOICES: {len(paid_invoices)}")
            
            for inv in paid_invoices:
                print(f"    ${inv['amount']} on {inv['date']} (Invoice: {inv['id']})")
            
            if total_paid > 0:
                print(f"\n🚨 CRITICAL: Customer has paid ${total_paid} but database shows inactive!")
                
    except Exception as e:
        print(f"[ERROR] Failed to search customers: {str(e)}")

if __name__ == "__main__":
    check_stripe_customer()
