#!/usr/bin/env python3
"""
COMPREHENSIVE STRIPE SYNC DEBUG SCRIPT
Systematically test ALL potential failure points in the sync system
"""

import os
import sys
import stripe
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test 1: Verify all required environment variables are present"""
    logger.info("🔍 TEST 1: Environment Variables")
    
    load_dotenv()
    
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    logger.info(f"  STRIPE_SECRET_KEY: {'✅ Present' if stripe_key else '❌ Missing'}")
    logger.info(f"  SUPABASE_URL: {'✅ Present' if supabase_url else '❌ Missing'}")
    logger.info(f"  SUPABASE_SERVICE_ROLE_KEY: {'✅ Present' if supabase_key else '❌ Missing'}")
    
    if stripe_key:
        logger.info(f"  Stripe key length: {len(stripe_key)}")
        logger.info(f"  Stripe key starts with: {stripe_key[:7]}...")
    
    return stripe_key, supabase_url, supabase_key

def test_stripe_initialization(stripe_key):
    """Test 2: Verify Stripe API initialization"""
    logger.info("🔍 TEST 2: Stripe API Initialization")
    
    try:
        # Initialize Stripe
        stripe.api_key = stripe_key
        logger.info(f"  stripe.api_key set: {'✅ Yes' if stripe.api_key else '❌ No'}")
        logger.info(f"  stripe.api_key value: {stripe.api_key[:7]}..." if stripe.api_key else "  stripe.api_key value: None")
        
        # Test basic Stripe API call
        logger.info("  Testing basic Stripe API call...")
        customers = stripe.Customer.list(limit=1)
        logger.info(f"  ✅ Stripe API working - returned {type(customers)}")
        logger.info(f"  ✅ Has .data attribute: {hasattr(customers, 'data')}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Stripe initialization failed: {str(e)}")
        return False

def test_supabase_connection(supabase_url, supabase_key):
    """Test 3: Verify Supabase connection"""
    logger.info("🔍 TEST 3: Supabase Connection")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Test basic query
        response = supabase.table("user_profiles").select("id, email").limit(1).execute()
        logger.info(f"  ✅ Supabase connection working - returned {len(response.data)} records")
        
        return supabase
        
    except Exception as e:
        logger.error(f"  ❌ Supabase connection failed: {str(e)}")
        return None

def test_user_lookup(supabase, test_email="brennan.testuser6@email.com"):
    """Test 4: Verify user profile lookup"""
    logger.info(f"🔍 TEST 4: User Profile Lookup for {test_email}")
    
    try:
        user_response = supabase.table("user_profiles").select(
            "id, email, stripe_customer_id, subscription_status, plan_tier"
        ).eq("email", test_email).single().execute()
        
        if user_response.data:
            user = user_response.data
            logger.info(f"  ✅ User found:")
            logger.info(f"    ID: {user.get('id')}")
            logger.info(f"    Email: {user.get('email')}")
            logger.info(f"    Stripe Customer ID: {user.get('stripe_customer_id')}")
            logger.info(f"    Subscription Status: {user.get('subscription_status')}")
            logger.info(f"    Plan Tier: {user.get('plan_tier')}")
            
            return user
        else:
            logger.error(f"  ❌ User not found for {test_email}")
            return None
            
    except Exception as e:
        logger.error(f"  ❌ User lookup failed: {str(e)}")
        return None

def test_stripe_subscription_lookup(stripe_customer_id):
    """Test 5: Verify Stripe subscription lookup"""
    logger.info(f"🔍 TEST 5: Stripe Subscription Lookup for customer {stripe_customer_id}")
    
    try:
        # This is the EXACT same call that's failing in the sync endpoint
        logger.info("  Making stripe.Subscription.list() call...")
        stripe_subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status='active',
            limit=10
        )
        
        logger.info(f"  ✅ stripe.Subscription.list() returned: {type(stripe_subscriptions)}")
        logger.info(f"  ✅ Has .data attribute: {hasattr(stripe_subscriptions, 'data')}")
        
        if hasattr(stripe_subscriptions, 'data'):
            logger.info(f"  ✅ Found {len(stripe_subscriptions.data)} active subscriptions")
            
            for i, sub in enumerate(stripe_subscriptions.data):
                logger.info(f"    Subscription {i+1}:")
                logger.info(f"      ID: {sub.id}")
                logger.info(f"      Status: {sub.status}")
                logger.info(f"      Plan: {sub.items.data[0].price.id if sub.items.data else 'Unknown'}")
        else:
            logger.error(f"  ❌ stripe_subscriptions object has no .data attribute!")
            logger.error(f"  ❌ Object type: {type(stripe_subscriptions)}")
            logger.error(f"  ❌ Object attributes: {dir(stripe_subscriptions)}")
        
        return stripe_subscriptions
        
    except Exception as e:
        logger.error(f"  ❌ Stripe subscription lookup failed: {str(e)}")
        import traceback
        logger.error(f"  ❌ Full traceback: {traceback.format_exc()}")
        return None

def test_import_order():
    """Test 6: Verify import order and module state"""
    logger.info("🔍 TEST 6: Import Order and Module State")
    
    logger.info(f"  stripe module: {stripe}")
    logger.info(f"  stripe.api_key: {stripe.api_key}")
    logger.info(f"  stripe.Subscription: {stripe.Subscription}")
    logger.info(f"  stripe.Subscription.list: {stripe.Subscription.list}")
    
    # Test if Subscription.list is a function or method
    logger.info(f"  stripe.Subscription.list type: {type(stripe.Subscription.list)}")
    logger.info(f"  Is callable: {callable(stripe.Subscription.list)}")

def main():
    """Run comprehensive sync system debug"""
    logger.info("🚀 STARTING COMPREHENSIVE STRIPE SYNC DEBUG")
    logger.info("=" * 60)
    
    # Test 1: Environment Variables
    stripe_key, supabase_url, supabase_key = test_environment_variables()
    if not all([stripe_key, supabase_url, supabase_key]):
        logger.error("❌ CRITICAL: Missing required environment variables")
        return
    
    print()
    
    # Test 2: Stripe Initialization
    if not test_stripe_initialization(stripe_key):
        logger.error("❌ CRITICAL: Stripe initialization failed")
        return
    
    print()
    
    # Test 3: Supabase Connection
    supabase = test_supabase_connection(supabase_url, supabase_key)
    if not supabase:
        logger.error("❌ CRITICAL: Supabase connection failed")
        return
    
    print()
    
    # Test 4: User Lookup
    user = test_user_lookup(supabase)
    if not user:
        logger.error("❌ CRITICAL: User lookup failed")
        return
    
    print()
    
    # Test 5: Stripe Subscription Lookup
    stripe_customer_id = user.get('stripe_customer_id')
    if stripe_customer_id:
        test_stripe_subscription_lookup(stripe_customer_id)
    else:
        logger.warning("⚠️ No Stripe customer ID found - skipping subscription lookup")
    
    print()
    
    # Test 6: Import Order
    test_import_order()
    
    logger.info("=" * 60)
    logger.info("🏁 COMPREHENSIVE DEBUG COMPLETE")

if __name__ == "__main__":
    main()
