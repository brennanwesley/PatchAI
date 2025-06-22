"""
Payment Routes
Stripe payment processing endpoints for subscription management
"""

import logging
import stripe
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from core.auth import verify_jwt_token
from core.stripe_webhooks import webhook_handler
from core.stripe_config import get_stripe_publishable_key

# Load environment variables
load_dotenv()

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
    has_subscription: bool
    subscription_status: Optional[str] = None
    plan_tier: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None
    stripe_customer_id: Optional[str] = None

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
            success_url=request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
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
                has_subscription=False,
                subscription_status="inactive",
                plan_tier=None,
                current_period_end=None,
                cancel_at_period_end=None,
                stripe_customer_id=None
            )
        
        user_profile = user_response.data
        subscription_status = user_profile.get('subscription_status', 'inactive')
        plan_tier = user_profile.get('plan_tier')
        stripe_customer_id = user_profile.get('stripe_customer_id')
        
        has_subscription = subscription_status in ['active', 'trialing']
        
        # For now, return basic subscription info without detailed period data
        # TODO: Add detailed subscription period info when needed
        return SubscriptionStatusResponse(
            has_subscription=has_subscription,
            subscription_status=subscription_status,
            plan_tier=plan_tier,
            current_period_end=None,  # Simplified for now
            cancel_at_period_end=None,  # Simplified for now
            stripe_customer_id=stripe_customer_id
        )
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        # Return a safe default instead of raising an exception
        return SubscriptionStatusResponse(
            has_subscription=False,
            subscription_status="inactive",
            plan_tier=None,
            current_period_end=None,
            cancel_at_period_end=None,
            stripe_customer_id=None
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
    Handle Stripe webhook events
    """
    try:
        payload = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Verify webhook signature and get event
        event = await webhook_handler.verify_webhook_signature(payload, signature)
        
        # Process the event
        await webhook_handler.process_webhook_event(event)
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
