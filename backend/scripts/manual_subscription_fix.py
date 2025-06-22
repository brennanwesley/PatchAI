#!/usr/bin/env python3
"""
Manual Subscription Status Fix Script
Temporarily fix subscription status for users who completed payment but webhook didn't sync
"""

import os
import sys
from datetime import datetime, timedelta
import stripe
from supabase import create_client, Client

# Add parent directory to path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def initialize_services():
    """Initialize Stripe and Supabase clients"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize Stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise ValueError("STRIPE_SECRET_KEY not found in environment")
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found in environment")
    
    supabase = create_client(supabase_url, supabase_key)
    
    return stripe, supabase

def fix_user_subscription(email: str):
    """
    Manually fix subscription status for a user who completed payment
    """
    try:
        stripe_client, supabase = initialize_services()
        
        print(f"[INFO] Looking up user: {email}")
        
        # 1. Find user in our database
        user_response = supabase.table("user_profiles").select(
            "id, email, stripe_customer_id, subscription_status"
        ).eq("email", email).single().execute()
        
        if not user_response.data:
            print(f"[ERROR] User not found in database: {email}")
            return False
        
        user = user_response.data
        user_id = user['id']
        customer_id = user.get('stripe_customer_id')
        
        print(f"[SUCCESS] Found user: {user_id}")
        print(f"   Current status: {user.get('subscription_status', 'None')}")
        print(f"   Stripe customer: {customer_id}")
        
        if not customer_id:
            print("[ERROR] No Stripe customer ID found")
            return False
        
        # 2. Get active subscriptions from Stripe
        print(f"[INFO] Checking Stripe subscriptions for customer: {customer_id}")
        
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=10
        )
        
        if not subscriptions.data:
            print("[ERROR] No active subscriptions found in Stripe")
            return False
        
        # 3. Process the first active subscription
        subscription = subscriptions.data[0]
        print(f"[SUCCESS] Found active subscription: {subscription['id']}")
        print(f"   Status: {subscription['status']}")
        
        # Debug: Print subscription object keys
        print(f"   DEBUG: Subscription keys: {list(subscription.keys())}")
        
        # Handle period dates safely
        period_start = subscription.get('current_period_start')
        period_end = subscription.get('current_period_end')
        created = subscription.get('created')
        
        if period_start and period_end:
            print(f"   Current period: {datetime.fromtimestamp(period_start)} - {datetime.fromtimestamp(period_end)}")
        else:
            print("   Current period: Not available")
        
        # 4. Get plan info
        price_id = subscription['items']['data'][0]['price']['id']
        print(f"   Price ID: {price_id}")
        
        # Find plan in our database
        plan_response = supabase.table("subscription_plans").select("*").eq(
            "stripe_price_id", price_id
        ).single().execute()
        
        if not plan_response.data:
            print(f"[ERROR] No plan found for price_id: {price_id}")
            return False
        
        plan = plan_response.data
        print(f"[SUCCESS] Found plan: {plan['plan_name']} ({plan['plan_id']})")
        
        # 5. Create/update subscription record
        subscription_data = {
            "user_id": user_id,
            "plan_id": plan['id'],  # Use UUID id, not plan_id string
            "stripe_subscription_id": subscription['id'],
            "status": subscription['status']
        }
        
        # Add optional fields if available
        if period_start:
            subscription_data["current_period_start"] = datetime.fromtimestamp(period_start).isoformat()
        if period_end:
            subscription_data["current_period_end"] = datetime.fromtimestamp(period_end).isoformat()
        if created:
            subscription_data["created_at"] = datetime.fromtimestamp(created).isoformat()
        
        # Check if subscription record already exists
        existing_sub = supabase.table("user_subscriptions").select("*").eq(
            "stripe_subscription_id", subscription['id']
        ).execute()
        
        if existing_sub.data:
            print("[INFO] Updating existing subscription record")
            supabase.table("user_subscriptions").update(subscription_data).eq(
                "stripe_subscription_id", subscription['id']
            ).execute()
        else:
            print("[INFO] Creating new subscription record")
            supabase.table("user_subscriptions").insert(subscription_data).execute()
        
        # 6. Update user profile
        profile_update = {
            "subscription_status": subscription['status'],
            "plan_tier": plan['plan_id'],
            "stripe_customer_id": customer_id
        }
        
        print("[INFO] Updating user profile")
        supabase.table("user_profiles").update(profile_update).eq(
            "id", user_id
        ).execute()
        
        print(f"[SUCCESS] Successfully fixed subscription for {email}")
        print(f"   Status: {subscription['status']}")
        print(f"   Plan: {plan['plan_name']}")
        print(f"   Valid until: {datetime.fromtimestamp(period_end)}" if period_end else "Not available")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error fixing subscription: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python manual_subscription_fix.py <email>")
        print("Example: python manual_subscription_fix.py feedbacklooploop@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"Manual Subscription Fix for: {email}")
    print("=" * 50)
    
    success = fix_user_subscription(email)
    
    if success:
        print("\n[SUCCESS] SUBSCRIPTION FIX COMPLETED!")
        print("The user should now be able to access the chat without paywall.")
    else:
        print("\n[ERROR] SUBSCRIPTION FIX FAILED!")
        print("Please check the logs above for details.")

if __name__ == "__main__":
    main()
