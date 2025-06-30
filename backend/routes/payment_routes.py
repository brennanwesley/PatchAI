"""
Payment Routes
Stripe payment processing endpoints for subscription management
"""

import logging
import stripe
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
import os
import uuid
import logging
import stripe
import traceback
from datetime import datetime
from dotenv import load_dotenv
from core.auth import verify_jwt_token
from core.stripe_webhooks import StripeWebhookHandler
from core.stripe_config import validate_stripe_config
from services.supabase_service import supabase
load_dotenv()

# Initialize Stripe API key BEFORE importing services that use Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY environment variable is required")

# Import Stripe-dependent services AFTER API key initialization
from services.subscription_sync_service import subscription_sync_service

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_service_role_key:
    raise ValueError("Supabase configuration missing for payment routes")

supabase: Client = create_client(supabase_url, supabase_service_role_key)

# Create router
router = APIRouter(prefix="/payments", tags=["payments"])

# Request/Response Models
class CreateCheckoutRequest(BaseModel):
    plan_id: str
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class CustomerPortalRequest(BaseModel):
    return_url: str

class CustomerPortalResponse(BaseModel):
    portal_url: str

class SubscriptionStatusResponse(BaseModel):
    has_active_subscription: bool
    subscription_status: Optional[str] = None
    plan_tier: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None
    stripe_customer_id: Optional[str] = None
    subscription: Optional[dict] = None

class SyncSubscriptionRequest(BaseModel):
    email: Optional[str] = None

class CancellationRequest(BaseModel):
    reason: Optional[str] = None

@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest, 
    req: Request, 
    user_id: str = Depends(verify_jwt_token)
):
    """
    Create Stripe checkout session for subscription
    """
    try:
        logger.info(f"🛒 Creating checkout session for user {user_id}, plan: {request.plan_id}")
        
        # Get user profile to check for existing customer
        logger.info(f"🔍 Fetching user profile for user {user_id}")
        user_response = supabase.table("user_profiles").select(
            "stripe_customer_id, email"
        ).eq("id", user_id).single().execute()
        
        if not user_response.data:
            logger.error(f"❌ User profile not found for user {user_id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_profile = user_response.data
        email = user_profile.get('email')
        existing_customer_id = user_profile.get('stripe_customer_id')
        
        logger.info(f"👤 User profile found - Email: {email}, Existing Customer: {bool(existing_customer_id)}")
        
        if not email:
            logger.error(f"❌ User profile missing email for user {user_id}")
            raise HTTPException(status_code=400, detail="User profile missing email address")
        
        # Get plan details - using hardcoded configuration for now
        # TODO: Replace with proper subscription_plans table lookup
        if request.plan_id == "standard":
            stripe_price_id = os.getenv("STRIPE_STANDARD_PRICE_ID")
            plan_name = "Standard Plan"
            monthly_price = 20.00
            logger.info(f"💰 Plan configured - Price ID: {stripe_price_id[:20] if stripe_price_id else 'None'}...")
        else:
            logger.error(f"❌ Invalid plan_id: {request.plan_id}")
            raise HTTPException(status_code=404, detail="Plan not found or inactive")
        
        if not stripe_price_id:
            logger.error("❌ STRIPE_STANDARD_PRICE_ID environment variable not set")
            raise HTTPException(
                status_code=503, 
                detail="Payment system is currently being configured. Please try again later or contact support."
            )
        
        # Create or use existing Stripe customer
        if existing_customer_id:
            try:
                logger.info(f"🔍 Retrieving existing Stripe customer: {existing_customer_id}")
                customer = stripe.Customer.retrieve(existing_customer_id)
                logger.info(f"✅ Retrieved existing customer: {customer.id}")
            except stripe.error.InvalidRequestError as e:
                logger.warning(f"⚠️ Existing customer not found in Stripe: {e}")
                # Customer doesn't exist in Stripe, create new one
                logger.info(f"🆕 Creating new Stripe customer for email: {email}")
                customer = stripe.Customer.create(
                    email=email,
                    metadata={"user_id": user_id}
                )
                logger.info(f"✅ Created new customer: {customer.id}")
                # Update user profile with new customer ID
                supabase.table("user_profiles").update({
                    "stripe_customer_id": customer.id
                }).eq("id", user_id).execute()
                logger.info(f"✅ Updated user profile with customer ID")
        else:
            # Create new Stripe customer
            logger.info(f"🆕 Creating new Stripe customer for email: {email}")
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": user_id}
            )
            logger.info(f"✅ Created new customer: {customer.id}")
            # Update user profile with customer ID
            supabase.table("user_profiles").update({
                "stripe_customer_id": customer.id
            }).eq("id", user_id).execute()
            logger.info(f"✅ Updated user profile with customer ID")
        
        # Create checkout session
        logger.info(f"🛒 Creating Stripe checkout session...")
        logger.info(f"🛒 Customer ID: {customer.id}")
        logger.info(f"🛒 Price ID: {stripe_price_id}")
        logger.info(f"🛒 Success URL: {request.success_url}")
        logger.info(f"🛒 Cancel URL: {request.cancel_url}")
        
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,  # Production Price ID: price_1RchcvGKwE0ADhm7uSACGHdG
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url + ('&' if '?' in request.success_url else '?') + 'session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url,
            metadata={
                'user_id': user_id,
                'plan_id': request.plan_id
            },
            subscription_data={
                'metadata': {
                    'user_id': user_id,
                    'plan_id': request.plan_id
                }
            }
        )
        
        logger.info(f"✅ Created checkout session for user {user_id}: {checkout_session.id}")
        logger.info(f"🔗 Checkout URL: {checkout_session.url}")
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
        
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"💳 Stripe API error: {str(e)}")
        logger.error(f"💳 Stripe error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error creating checkout session: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

@router.post("/create-customer-portal", response_model=CustomerPortalResponse)
async def create_customer_portal(
    request: CustomerPortalRequest,
    req: Request,
    user_id: str = Depends(verify_jwt_token)
):
    """
    Create Stripe customer portal session for subscription management
    """
    try:
        # Get user's Stripe customer ID
        user_response = supabase.table("user_profiles").select(
            "stripe_customer_id"
        ).eq("id", user_id).single().execute()
        
        if not user_response.data or not user_response.data.get('stripe_customer_id'):
            raise HTTPException(status_code=404, detail="No Stripe customer found")
        
        customer_id = user_response.data['stripe_customer_id']
        
        # Create customer portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.return_url,
        )
        
        logger.info(f"Created customer portal session for user {user_id}")
        
        return CustomerPortalResponse(portal_url=portal_session.url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer portal: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create customer portal")

@router.get("/subscription-status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    req: Request,
    user_id: str = Depends(verify_jwt_token)
):
    """
    Get current subscription status for user
    """
    try:
        # Get user's subscription info
        user_response = supabase.table("user_profiles").select(
            "subscription_status, plan_tier, stripe_customer_id"
        ).eq("id", user_id).single().execute()
        
        if not user_response.data:
            # User not found, return default inactive status
            return SubscriptionStatusResponse(
                has_active_subscription=False,
                subscription_status="inactive",
                plan_tier=None,
                current_period_end=None,
                cancel_at_period_end=None,
                stripe_customer_id=None,
                subscription=None
            )
        
        user_profile = user_response.data
        subscription_status = user_profile.get('subscription_status', 'inactive')
        plan_tier = user_profile.get('plan_tier')
        stripe_customer_id = user_profile.get('stripe_customer_id')
        
        has_active_subscription = subscription_status in ['active', 'trialing']
        
        # Get detailed subscription info if user has active subscription
        subscription_details = None
        current_period_end = None
        cancel_at_period_end = None
        
        if has_active_subscription and stripe_customer_id:
            try:
                # Get subscription details from database
                sub_response = supabase.table("user_subscriptions").select(
                    "stripe_subscription_id, status, current_period_start, current_period_end, cancel_at_period_end"
                ).eq("user_id", user_id).eq("status", "active").single().execute()
                
                if sub_response.data:
                    sub_data = sub_response.data
                    current_period_end = sub_data.get('current_period_end')
                    cancel_at_period_end = sub_data.get('cancel_at_period_end', False)
                    
                    # Create subscription object for frontend compatibility
                    subscription_details = {
                        "id": sub_data.get('stripe_subscription_id'),
                        "status": sub_data.get('status'),
                        "current_period_start": sub_data.get('current_period_start'),
                        "current_period_end": current_period_end,
                        "cancel_at_period_end": cancel_at_period_end
                    }
                    
            except Exception as sub_error:
                logger.warning(f"Could not fetch detailed subscription info: {str(sub_error)}")
        
        return SubscriptionStatusResponse(
            has_active_subscription=has_active_subscription,
            subscription_status=subscription_status,
            plan_tier=plan_tier,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            stripe_customer_id=stripe_customer_id,
            subscription=subscription_details
        )
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        # Return a safe default instead of raising an exception
        return SubscriptionStatusResponse(
            has_active_subscription=False,
            subscription_status="inactive",
            plan_tier=None,
            current_period_end=None,
            cancel_at_period_end=None,
            stripe_customer_id=None,
            subscription=None
        )

@router.get("/plans")
async def get_available_plans():
    """
    Get all available subscription plans
    """
    try:
        # Return hardcoded plans for now
        # TODO: Replace with proper subscription_plans table lookup
        plans = [
            {
                "plan_id": "standard",
                "plan_name": "Standard Plan",
                "monthly_price": 20.00,
                "message_limit": 1000,
                "features": ["1000 messages per day", "GPT-4 access", "Chat history", "Priority support"],
                "active": True
            }
        ]
        
        return {"plans": plans}
        
    except Exception as e:
        logger.error(f"Error getting plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plans")

@router.get("/config-status")
async def get_payment_config_status():
    """
    Get payment system configuration status for debugging
    """
    try:
        stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        stripe_standard_price_id = os.getenv("STRIPE_STANDARD_PRICE_ID")
        stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        
        return {
            "stripe_secret_key_configured": bool(stripe_secret_key),
            "stripe_secret_key_format": stripe_secret_key[:7] + "..." if stripe_secret_key else None,
            "stripe_standard_price_id_configured": bool(stripe_standard_price_id),
            "stripe_standard_price_id": stripe_standard_price_id,
            "stripe_webhook_secret_configured": bool(stripe_webhook_secret),
            "stripe_publishable_key_configured": bool(stripe_publishable_key),
            "stripe_api_initialized": stripe.api_key is not None,
            "supabase_url_configured": bool(supabase_url),
            "supabase_service_role_configured": bool(supabase_service_role_key)
        }
    except Exception as e:
        logger.error(f"Error getting config status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_payment_config():
    """
    Get payment configuration including Stripe publishable key
    """
    try:
        publishable_key = get_stripe_publishable_key()
        
        if not publishable_key:
            raise HTTPException(status_code=500, detail="Stripe publishable key not configured")
        
        return {
            "stripe_publishable_key": publishable_key
        }
        
    except Exception as e:
        logger.error(f"Error getting payment config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payment configuration")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events with comprehensive debugging
    """
    try:
        # Log incoming request
        logger.info("🎯 WEBHOOK: Incoming request received")
        
        # Get raw body and headers
        body = await request.body()
        headers = dict(request.headers)
        
        logger.info(f"🎯 WEBHOOK: Body length: {len(body)}")
        logger.info(f"🎯 WEBHOOK: Headers: {headers}")
        
        # Check for Stripe signature
        stripe_signature = headers.get('stripe-signature')
        if not stripe_signature:
            logger.error("❌ WEBHOOK: Missing Stripe signature header")
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        logger.info(f"🎯 WEBHOOK: Stripe signature present: {stripe_signature[:50]}...")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                body, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET")
            )
            logger.info(f"✅ WEBHOOK: Signature verified successfully")
            logger.info(f"🎯 WEBHOOK: Event type: {event['type']}")
            logger.info(f"🎯 WEBHOOK: Event ID: {event['id']}")
            
        except ValueError as e:
            logger.error(f"❌ WEBHOOK: Invalid payload: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ WEBHOOK: Signature verification failed: {str(e)}")
            logger.error(f"❌ WEBHOOK: Expected signature: {stripe_signature}")
            logger.error(f"❌ WEBHOOK: Webhook secret configured: {'Yes' if os.getenv('STRIPE_WEBHOOK_SECRET') else 'No'}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Process the event
        try:
            logger.info(f"🎯 WEBHOOK: Processing event {event['type']}")
            await webhook_handler.process_webhook_event(event)
            logger.info(f"✅ WEBHOOK: Event {event['type']} processed successfully")
            
            return {"status": "success", "event_type": event['type']}
            
        except Exception as e:
            logger.error(f"❌ WEBHOOK: Event processing failed: {str(e)}")
            import traceback
            logger.error(f"❌ WEBHOOK: Full traceback: {traceback.format_exc()}")
            
            # Return 200 to prevent Stripe retries for application errors
            return {"status": "error", "message": str(e)}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 WEBHOOK: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"💥 WEBHOOK: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/webhook-test")
async def webhook_test(request: Request):
    """Test endpoint to log all webhook data for debugging"""
    try:
        # Get raw body
        body = await request.body()
        headers = dict(request.headers)
        
        # Log everything for debugging
        logger.info("🔍 WEBHOOK TEST - Raw body length: %d", len(body))
        logger.info("🔍 WEBHOOK TEST - Headers: %s", headers)
        
        if body:
            try:
                # Try to parse as JSON
                import json
                data = json.loads(body)
                logger.info("🔍 WEBHOOK TEST - Parsed JSON: %s", json.dumps(data, indent=2))
            except:
                logger.info("🔍 WEBHOOK TEST - Raw body (not JSON): %s", body.decode('utf-8', errors='ignore'))
        
        return {"status": "received", "body_length": len(body)}
        
    except Exception as e:
        logger.error("❌ Webhook test error: %s", str(e))
        return {"error": str(e)}, 500

@router.post("/sync-subscription")
async def sync_subscription_manually(
    request: SyncSubscriptionRequest,
    current_user_id: str = Depends(verify_jwt_token)
):
    """Simple, direct subscription sync - queries Stripe and updates database"""
    try:
        correlation_id = str(uuid.uuid4())
        logger.info(f"🔄 [SYNC-{correlation_id}] Direct subscription sync requested by user {current_user_id}")
        
        # Determine target email - if not provided, get from user profile
        target_email = request.email
        if not target_email:
            # Get user's email from their profile
            user_profile_response = supabase.table("user_profiles").select(
                "email"
            ).eq("id", current_user_id).single().execute()
            
            if user_profile_response.data:
                target_email = user_profile_response.data.get('email')
        
        if not target_email:
            logger.error(f"❌ [SYNC-{correlation_id}] No email provided for sync")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Email is required for subscription sync",
                    "error_code": "EMAIL_REQUIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        logger.info(f"🎯 [SYNC-{correlation_id}] Target email: {target_email}")
        
        # Step 1: Get user profile from database
        logger.info(f"📋 [SYNC-{correlation_id}] Fetching user profile for {target_email}")
        user_response = supabase.table("user_profiles").select(
            "id, email, stripe_customer_id, subscription_status, plan_tier"
        ).eq("email", target_email).single().execute()
        
        if not user_response.data:
            logger.error(f"❌ [SYNC-{correlation_id}] User profile not found for {target_email}")
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "User profile not found",
                    "error_code": "USER_NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        user_profile = user_response.data
        user_id = user_profile['id']
        stripe_customer_id = user_profile.get('stripe_customer_id')
        
        logger.info(f"👤 [SYNC-{correlation_id}] User found - ID: {user_id}, Stripe Customer: {bool(stripe_customer_id)}")
        
        if not stripe_customer_id:
            logger.warning(f"⚠️ [SYNC-{correlation_id}] No Stripe customer ID found for {target_email}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No Stripe customer found - user may not have a subscription",
                    "subscription_status": "inactive",
                    "plan_tier": "free",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Step 2: Query Stripe for active subscriptions
        logger.info(f"💳 [SYNC-{correlation_id}] Querying Stripe for customer {stripe_customer_id}")
        stripe_subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status='active',
            limit=10
        )
        
        logger.info(f"📊 [SYNC-{correlation_id}] Found {len(stripe_subscriptions.data)} active Stripe subscriptions")
        
        if not stripe_subscriptions.data:
            # No active subscriptions in Stripe - update user to inactive
            logger.info(f"🔄 [SYNC-{correlation_id}] No active Stripe subscriptions - updating user to inactive")
            
            update_response = supabase.table("user_profiles").update({
                "subscription_status": "inactive",
                "plan_tier": "free",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No active subscription found - updated to free tier",
                    "subscription_status": "inactive",
                    "plan_tier": "free",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Step 3: Process the most recent active subscription
        latest_subscription = stripe_subscriptions.data[0]
        subscription_id = latest_subscription.id
        subscription_status = latest_subscription.status
        
        # Determine plan tier from Stripe price ID
        plan_tier = "standard"  # Default
        if latest_subscription.get('items') and latest_subscription['items'].get('data'):
            price_id = latest_subscription['items']['data'][0]['price']['id']
            standard_price_id = os.getenv("STRIPE_STANDARD_PRICE_ID")
            if price_id == standard_price_id:
                plan_tier = "standard"
        
        logger.info(f"✅ [SYNC-{correlation_id}] Active subscription found - Status: {subscription_status}, Plan: {plan_tier}")
        
        # Step 4: Update user profile
        logger.info(f"💾 [SYNC-{correlation_id}] Updating user profile with subscription data")
        profile_update = supabase.table("user_profiles").update({
            "subscription_status": "active" if subscription_status == "active" else "inactive",
            "plan_tier": plan_tier,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        # Step 5: Ensure user_subscriptions record exists
        logger.info(f"🔍 [SYNC-{correlation_id}] Checking user_subscriptions table")
        
        # Get subscription plan ID
        plan_response = supabase.table("subscription_plans").select(
            "id, name"
        ).eq("name", "Standard Plan").single().execute()
        
        plan_id = None
        if plan_response.data:
            plan_id = plan_response.data['id']
            logger.info(f"📋 [SYNC-{correlation_id}] Found plan ID: {plan_id}")
        
        # Check if user_subscriptions record exists
        existing_sub = supabase.table("user_subscriptions").select(
            "id, subscription_id"
        ).eq("user_id", user_id).eq("subscription_id", subscription_id).execute()
        
        if not existing_sub.data and plan_id:
            # Create user_subscriptions record
            logger.info(f"➕ [SYNC-{correlation_id}] Creating user_subscriptions record")
            
            current_period_end = None
            if latest_subscription.current_period_end:
                current_period_end = datetime.fromtimestamp(latest_subscription.current_period_end).isoformat()
            
            sub_insert = supabase.table("user_subscriptions").insert({
                "user_id": user_id,
                "plan_id": plan_id,
                "subscription_id": subscription_id,
                "status": subscription_status,
                "current_period_start": datetime.fromtimestamp(latest_subscription.current_period_start).isoformat() if latest_subscription.current_period_start else None,
                "current_period_end": current_period_end,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"✅ [SYNC-{correlation_id}] Created user_subscriptions record")
        
        logger.info(f"🎉 [SYNC-{correlation_id}] Subscription sync completed successfully for {target_email}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Subscription synchronized successfully",
                "subscription_status": "active" if subscription_status == "active" else "inactive",
                "plan_tier": plan_tier,
                "stripe_subscription_id": subscription_id,
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 401)
        raise
    except stripe.error.StripeError as e:
        logger.error(f"💳 [SYNC] Stripe API error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Unable to connect to payment system. Please try again later.",
                "error_code": "STRIPE_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"❌ [SYNC] Direct subscription sync exception: {str(e)}")
        logger.error(f"❌ [SYNC] Exception traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Sync failed: {str(e)}",
                "error_code": "SYNC_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.post("/sync-all-subscriptions")
async def sync_all_subscriptions(current_user: dict = Depends(verify_jwt_token)):
    """
    Manually sync all Stripe subscriptions for users with missing database records
    """
    try:
        logger.info("🔄 MANUAL SYNC: Starting sync of all subscriptions")
        
        # Get all user profiles with Stripe customer IDs
        profiles_response = supabase.table("user_profiles").select("id, email, stripe_customer_id, subscription_status").execute()
        
        synced_count = 0
        error_count = 0
        
        for profile in profiles_response.data:
            try:
                user_id = profile['id']
                email = profile['email']
                customer_id = profile.get('stripe_customer_id')
                current_status = profile.get('subscription_status', 'inactive')
                
                if not customer_id:
                    logger.info(f"⏭️  SYNC: Skipping {email} - no Stripe customer ID")
                    continue
                
                logger.info(f"🔍 SYNC: Checking {email} (current status: {current_status})")
                
                # Get active subscriptions from Stripe
                subscriptions = stripe.Subscription.list(
                    customer=customer_id,
                    status='active',
                    limit=10
                )
                
                if not subscriptions.data:
                    logger.info(f"⏭️  SYNC: No active subscriptions for {email}")
                    continue
                
                # Process each active subscription
                for subscription in subscriptions.data:
                    # Check if subscription already exists in database
                    existing_sub = supabase.table("user_subscriptions").select("id").eq("stripe_subscription_id", subscription.id).execute()
                    
                    if existing_sub.data:
                        logger.info(f"✅ SYNC: Subscription {subscription.id} already exists for {email}")
                        continue
                    
                    # Process the subscription using webhook handler
                    logger.info(f"🔄 SYNC: Processing subscription {subscription.id} for {email}")
                    await webhook_handler.handle_customer_subscription_created(subscription)
                    synced_count += 1
                    logger.info(f"✅ SYNC: Successfully synced {email}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ SYNC: Error processing {profile.get('email', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"🎉 MANUAL SYNC: Completed - {synced_count} synced, {error_count} errors")
        
        return {
            "status": "success",
            "synced_count": synced_count,
            "error_count": error_count,
            "message": f"Synced {synced_count} subscriptions with {error_count} errors"
        }
        
    except Exception as e:
        logger.error(f"💥 MANUAL SYNC: Failed: {str(e)}")
        import traceback
        logger.error(f"💥 MANUAL SYNC: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/sync-user-subscription")
async def sync_user_subscription(
    request: dict,
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Manually sync a specific user's subscription by email
    """
    try:
        email = request.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        logger.info(f"🔄 USER SYNC: Starting sync for {email}")
        
        # Get user profile
        profile_response = supabase.table("user_profiles").select("*").eq("email", email).execute()
        if not profile_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = profile_response.data[0]
        customer_id = profile.get('stripe_customer_id')
        
        if not customer_id:
            raise HTTPException(status_code=400, detail="User has no Stripe customer ID")
        
        # Get active subscriptions from Stripe
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=10
        )
        
        if not subscriptions.data:
            return {
                "status": "no_subscriptions",
                "message": f"No active subscriptions found for {email}"
            }
        
        synced_count = 0
        for subscription in subscriptions.data:
            # Check if subscription already exists
            existing_sub = supabase.table("user_subscriptions").select("id").eq("stripe_subscription_id", subscription.id).execute()
            
            if existing_sub.data:
                logger.info(f"✅ USER SYNC: Subscription {subscription.id} already exists")
                continue
            
            # Process the subscription
            await webhook_handler.handle_customer_subscription_created(subscription)
            synced_count += 1
            logger.info(f"✅ USER SYNC: Synced subscription {subscription.id}")
        
        return {
            "status": "success",
            "synced_count": synced_count,
            "message": f"Synced {synced_count} subscriptions for {email}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 USER SYNC: Failed for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/request-cancellation")
async def request_subscription_cancellation(
    request: CancellationRequest,
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Log a subscription cancellation request from the user.
    This does not actually cancel the Stripe subscription - just logs the intent.
    """
    try:
        user_id = current_user.get('id')
        user_email = current_user.get('email')
        
        if not user_id or not user_email:
            raise HTTPException(status_code=400, detail="User information not available")
        
        logger.info(f"🚫 Cancellation request from user: {user_email}")
        
        # Get current subscription info
        user_profile = supabase.table("user_profiles").select(
            "subscription_status, plan_tier, stripe_customer_id"
        ).eq("id", user_id).execute()
        
        if not user_profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        profile = user_profile.data[0]
        
        # Insert cancellation request
        cancellation_data = {
            "user_id": user_id,
            "email": user_email,
            "subscription_status": profile.get("subscription_status", "unknown"),
            "plan_tier": profile.get("plan_tier", "unknown"),
            "stripe_customer_id": profile.get("stripe_customer_id"),
            "reason": request.reason,
            "requested_at": datetime.utcnow().isoformat(),
            "processed": False
        }
        
        result = supabase.table("subscription_cancellation_requests").insert(cancellation_data).execute()
        
        if result.data:
            logger.info(f"✅ Cancellation request logged for {user_email}")
            return {
                "success": True,
                "message": "Cancellation request has been logged. We're sorry to see you go!",
                "request_id": result.data[0]["id"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to log cancellation request")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 CANCELLATION REQUEST: Failed for {current_user.get('email', 'unknown')}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process cancellation request: {str(e)}")
