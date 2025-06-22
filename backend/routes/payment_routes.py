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
        # Get user profile to check for existing customer
        user_response = supabase.table("user_profiles").select(
            "stripe_customer_id, email"
        ).eq("id", user_id).single().execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_profile = user_response.data
        email = user_profile.get('email')
        existing_customer_id = user_profile.get('stripe_customer_id')
        
        # Get plan details
        plan_response = supabase.table("subscription_plans").select(
            "stripe_price_id, plan_name, monthly_price"
        ).eq("plan_id", request.plan_id).eq("active", True).single().execute()
        
        if not plan_response.data:
            raise HTTPException(status_code=404, detail="Plan not found or inactive")
        
        plan = plan_response.data
        stripe_price_id = plan['stripe_price_id']
        
        if not stripe_price_id:
            raise HTTPException(status_code=400, detail="Plan not configured with Stripe price ID")
        
        # Create or use existing Stripe customer
        if existing_customer_id:
            try:
                customer = stripe.Customer.retrieve(existing_customer_id)
            except stripe.error.InvalidRequestError:
                # Customer doesn't exist in Stripe, create new one
                customer = stripe.Customer.create(
                    email=email,
                    metadata={"user_id": user_id}
                )
                # Update user profile with new customer ID
                supabase.table("user_profiles").update({
                    "stripe_customer_id": customer.id
                }).eq("id", user_id).execute()
        else:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": user_id}
            )
            # Update user profile with customer ID
            supabase.table("user_profiles").update({
                "stripe_customer_id": customer.id
            }).eq("id", user_id).execute()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan['stripe_price_id'],  # Production Price ID: price_1RchcvGKwE0ADhm7uSACGHdG
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
        
        logger.info(f"Created checkout session for user {user_id}: {checkout_session.id}")
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

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
            return SubscriptionStatusResponse(has_subscription=False)
        
        user_profile = user_response.data
        subscription_status = user_profile.get('subscription_status', 'inactive')
        plan_tier = user_profile.get('plan_tier')
        stripe_customer_id = user_profile.get('stripe_customer_id')
        
        has_subscription = subscription_status in ['active', 'trialing']
        
        # Get detailed subscription info if active
        current_period_end = None
        cancel_at_period_end = None
        
        if has_subscription:
            subscription_response = supabase.rpc(
                "get_user_active_subscription",
                {"user_uuid": user_id}
            ).execute()
            
            if subscription_response.data and len(subscription_response.data) > 0:
                subscription = subscription_response.data[0]
                current_period_end = subscription.get('current_period_end')
                
                # Check Stripe for cancellation status
                if subscription.get('stripe_subscription_id'):
                    try:
                        stripe_sub = stripe.Subscription.retrieve(subscription['stripe_subscription_id'])
                        cancel_at_period_end = stripe_sub.cancel_at_period_end
                    except:
                        pass  # Ignore Stripe API errors for status check
        
        return SubscriptionStatusResponse(
            has_subscription=has_subscription,
            subscription_status=subscription_status,
            plan_tier=plan_tier,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            stripe_customer_id=stripe_customer_id
        )
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

@router.get("/plans")
async def get_available_plans():
    """
    Get all available subscription plans
    """
    try:
        plans_response = supabase.table("subscription_plans").select(
            "plan_id, plan_name, monthly_price, message_limit, features, active"
        ).eq("active", True).order("monthly_price").execute()
        
        return {"plans": plans_response.data}
        
    except Exception as e:
        logger.error(f"Error getting plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plans")

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
