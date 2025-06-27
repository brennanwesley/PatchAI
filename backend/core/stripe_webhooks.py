"""
Stripe Webhook Handlers
Handles real-time subscription events from Stripe to keep database in sync
"""

import logging
import stripe
from fastapi import HTTPException, Request
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime
from .stripe_config import STRIPE_WEBHOOK_SECRET
import uuid

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_service_role_key)

if not supabase_url or not supabase_service_role_key:
    raise ValueError("Supabase configuration missing for webhook handlers")

logger = logging.getLogger(__name__)

class StripeWebhookHandler:
    """Handles Stripe webhook events for subscription management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """
        Verify Stripe webhook signature and parse event
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            
        Returns:
            dict: Parsed Stripe event
            
        Raises:
            HTTPException: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            self.logger.info(f"Webhook verified: {event['type']} - {event['id']}")
            return event
        except ValueError as e:
            self.logger.error(f"Invalid payload: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            self.logger.error(f"Invalid signature: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    async def handle_customer_subscription_created(self, subscription: dict):
        """Handle new subscription creation"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            status = subscription['status']
            
            self.logger.info(f" Processing subscription created: {subscription_id} for customer {customer_id}")
            
            # Get customer to find user_id
            customer = stripe.Customer.retrieve(customer_id)
            user_id = customer.metadata.get('user_id')
            
            if not user_id:
                self.logger.error(f" No user_id found in customer metadata for {customer_id}")
                self.logger.error(f" Customer metadata: {customer.metadata}")
                return
            
            self.logger.info(f" Found user_id: {user_id}")
            
            # Get plan info from subscription items
            if subscription['items']['data']:
                price_id = subscription['items']['data'][0]['price']['id']
                self.logger.info(f" Looking up plan for price_id: {price_id}")
                
                # Find matching plan in our database
                plan_response = supabase.table("subscription_plans").select("*").eq(
                    "stripe_price_id", price_id
                ).single().execute()
                
                if not plan_response.data:
                    self.logger.error(f" No plan found for price_id: {price_id}")
                    # List all available plans for debugging
                    all_plans = supabase.table("subscription_plans").select("plan_id, stripe_price_id").execute()
                    self.logger.error(f" Available plans: {all_plans.data}")
                    return
                
                plan = plan_response.data
                self.logger.info(f" Found plan: {plan['plan_name']} ({plan['plan_id']})")
                
                # Check if subscription already exists
                existing_sub = supabase.table("user_subscriptions").select("id").eq(
                    "stripe_subscription_id", subscription_id
                ).execute()
                
                if existing_sub.data:
                    self.logger.info(f" Subscription {subscription_id} already exists in database")
                    return
                
                # Get period dates from subscription items or main subscription
                item = subscription['items']['data'][0]
                current_period_start = item.get('current_period_start') or subscription.get('current_period_start')
                current_period_end = item.get('current_period_end') or subscription.get('current_period_end')
                
                # Create subscription record
                subscription_data = {
                    "user_id": user_id,
                    "plan_id": plan['id'],  # Use UUID id field, not string plan_id
                    "stripe_subscription_id": subscription_id,
                    "status": status,
                    "current_period_start": datetime.fromtimestamp(current_period_start).isoformat() if current_period_start else None,
                    "current_period_end": datetime.fromtimestamp(current_period_end).isoformat() if current_period_end else None,
                    "trial_start": datetime.fromtimestamp(subscription['trial_start']).isoformat() if subscription.get('trial_start') else None,
                    "trial_end": datetime.fromtimestamp(subscription['trial_end']).isoformat() if subscription.get('trial_end') else None,
                    "created_at": datetime.fromtimestamp(subscription['created']).isoformat()
                }
                
                self.logger.info(f" Creating subscription record: {subscription_data}")
                supabase.table("user_subscriptions").insert(subscription_data).execute()
                
                # Update user profile
                profile_update = {
                    "subscription_status": status,
                    "plan_tier": plan['plan_id'],  # Use string plan_id for plan_tier
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                self.logger.info(f" Updating user profile: {profile_update}")
                supabase.table("user_profiles").update(profile_update).eq("id", user_id).execute()
                
                self.logger.info(f" Successfully processed subscription creation for user {user_id}")
                
        except Exception as e:
            self.logger.error(f" Error handling subscription creation: {str(e)}")
            self.logger.error(f" Subscription data: {subscription}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def handle_customer_subscription_updated(self, subscription: dict):
        """Handle subscription updates (status changes, plan changes, etc.)"""
        try:
            subscription_id = subscription['id']
            status = subscription['status']
            
            # Update subscription record
            update_data = {
                "status": status,
                "current_period_start": datetime.fromtimestamp(subscription['current_period_start']).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription['current_period_end']).isoformat(),
                "trial_start": datetime.fromtimestamp(subscription['trial_start']).isoformat() if subscription.get('trial_start') else None,
                "trial_end": datetime.fromtimestamp(subscription['trial_end']).isoformat() if subscription.get('trial_end') else None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Check if plan changed
            if subscription['items']['data']:
                price_id = subscription['items']['data'][0]['price']['id']
                
                plan_response = supabase.table("subscription_plans").select("plan_id").eq(
                    "stripe_price_id", price_id
                ).single().execute()
                
                if plan_response.data:
                    update_data["plan_id"] = plan_response.data['plan_id']
            
            supabase.table("user_subscriptions").update(update_data).eq(
                "stripe_subscription_id", subscription_id
            ).execute()
            
            self.logger.info(f" Updated subscription {subscription_id}: status={status}")
            
        except Exception as e:
            self.logger.error(f" Error handling subscription update: {str(e)}")
            self.logger.error(f" Subscription data: {subscription}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def handle_customer_subscription_deleted(self, subscription: dict):
        """Handle subscription cancellation/deletion"""
        try:
            subscription_id = subscription['id']
            
            # Update subscription status to canceled
            supabase.table("user_subscriptions").update({
                "status": "canceled",
                "canceled_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("stripe_subscription_id", subscription_id).execute()
            
            self.logger.info(f" Canceled subscription {subscription_id}")
            
        except Exception as e:
            self.logger.error(f" Error handling subscription deletion: {str(e)}")
            self.logger.error(f" Subscription data: {subscription}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def handle_invoice_payment_succeeded(self, invoice: dict):
        """Handle successful payment"""
        try:
            subscription_id = invoice.get('subscription')
            payment_intent_id = invoice.get('payment_intent')
            amount = invoice.get('amount_paid', 0)
            
            if subscription_id:
                # Get subscription to find user
                subscription_response = supabase.table("user_subscriptions").select(
                    "user_id, id"
                ).eq("stripe_subscription_id", subscription_id).single().execute()
                
                if subscription_response.data:
                    user_id = subscription_response.data['user_id']
                    subscription_db_id = subscription_response.data['id']
                    
                    # Record payment transaction
                    transaction_data = {
                        "user_id": user_id,
                        "subscription_id": subscription_db_id,
                        "stripe_payment_intent_id": payment_intent_id,
                        "stripe_invoice_id": invoice['id'],
                        "amount": amount,
                        "currency": invoice.get('currency', 'usd'),
                        "status": "succeeded",
                        "payment_method": "card",  # Default, could be enhanced
                        "created_at": datetime.fromtimestamp(invoice['created']).isoformat()
                    }
                    
                    transaction_result = supabase.table("payment_transactions").insert(transaction_data).execute()
                    
                    # Update user's last payment date
                    supabase.table("user_profiles").update({
                        "last_payment_at": datetime.utcnow().isoformat()
                    }).eq("id", user_id).execute()
                    
                    self.logger.info(f" Recorded successful payment for user {user_id}: ${amount/100}")
                    
                    # Process referral rewards if user was referred
                    await self._process_referral_rewards(user_id, amount, transaction_result.data[0]['id'] if transaction_result.data else None)
            
        except Exception as e:
            self.logger.error(f" Error handling payment success: {str(e)}")
            self.logger.error(f" Invoice data: {invoice}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def _process_referral_rewards(self, referred_user_id: str, payment_amount: int, transaction_id: str = None):
        """
        Process referral rewards for successful payments
        """
        try:
            self.logger.info(f" Processing referral rewards for user {referred_user_id}, amount: ${payment_amount/100}")
            
            # Check if this user was referred by someone
            user_profile = supabase.table("user_profiles").select(
                "referred_by"
            ).eq("id", referred_user_id).single().execute()
            
            if not user_profile.data or not user_profile.data.get('referred_by'):
                self.logger.debug(f" User {referred_user_id} was not referred by anyone, skipping rewards")
                return
            
            referring_user_id = user_profile.data['referred_by']
            self.logger.info(f" User {referred_user_id} was referred by {referring_user_id}")
            
            # Get referral relationship to check status and calculate subscription month
            referral_relationship = supabase.table("referral_relationships").select(
                "id, created_at, status"
            ).eq("referring_user_id", referring_user_id).eq("referred_user_id", referred_user_id).single().execute()
            
            if not referral_relationship.data or referral_relationship.data.get('status') != 'active':
                self.logger.warning(f" Referral relationship not active for users {referring_user_id} -> {referred_user_id}")
                return
            
            # Calculate which subscription month this is (for reward percentage calculation)
            referral_start_date = datetime.fromisoformat(referral_relationship.data['created_at'].replace('Z', '+00:00'))
            current_date = datetime.utcnow()
            months_since_referral = ((current_date.year - referral_start_date.year) * 12 + 
                                   current_date.month - referral_start_date.month)
            
            # Calculate reward amount based on subscription month
            if months_since_referral < 12:
                reward_percentage = 0.10  # 10% for first 12 months
            else:
                reward_percentage = 0.05  # 5% after 12 months
            
            # Convert amount from cents to dollars for calculation
            base_payment_amount = payment_amount / 100
            reward_amount = base_payment_amount * reward_percentage
            
            # Create referral reward record
            reward_data = {
                "id": str(uuid.uuid4()),
                "referring_user_id": referring_user_id,
                "referred_user_id": referred_user_id,
                "payment_transaction_id": transaction_id,
                "reward_amount": reward_amount,
                "reward_percentage": reward_percentage,
                "base_payment_amount": base_payment_amount,
                "subscription_month": months_since_referral + 1,
                "status": "calculated",
                "created_at": datetime.utcnow().isoformat(),
                "payment_date": datetime.utcnow().isoformat()
            }
            
            reward_result = supabase.table("referral_rewards").insert(reward_data).execute()
            
            if reward_result.data:
                self.logger.info(f" Created referral reward: ${reward_amount:.2f} ({reward_percentage*100}%) for user {referring_user_id}")
            else:
                self.logger.error(f" Failed to create referral reward record: {reward_data}")
                
        except Exception as e:
            self.logger.error(f" Error processing referral rewards: {e}")
            # Don't raise exception - referral reward failure shouldn't break payment processing
    
    async def handle_invoice_payment_failed(self, invoice: dict):
        """Handle failed payment"""
        try:
            subscription_id = invoice.get('subscription')
            payment_intent_id = invoice.get('payment_intent')
            amount = invoice.get('amount_due', 0)
            
            if subscription_id:
                # Get subscription to find user
                subscription_response = supabase.table("user_subscriptions").select(
                    "user_id, id"
                ).eq("stripe_subscription_id", subscription_id).single().execute()
                
                if subscription_response.data:
                    user_id = subscription_response.data['user_id']
                    subscription_db_id = subscription_response.data['id']
                    
                    # Record failed payment transaction
                    transaction_data = {
                        "user_id": user_id,
                        "subscription_id": subscription_db_id,
                        "stripe_payment_intent_id": payment_intent_id,
                        "stripe_invoice_id": invoice['id'],
                        "amount": amount,
                        "currency": invoice.get('currency', 'usd'),
                        "status": "failed",
                        "failure_reason": "payment_failed",
                        "created_at": datetime.fromtimestamp(invoice['created']).isoformat()
                    }
                    
                    supabase.table("payment_transactions").insert(transaction_data).execute()
                    
                    self.logger.warning(f" Recorded failed payment for user {user_id}: ${amount/100}")
            
        except Exception as e:
            self.logger.error(f" Error handling payment failure: {str(e)}")
            self.logger.error(f" Invoice data: {invoice}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def process_webhook_event(self, event: dict):
        """Process webhook event based on type"""
        event_type = event['type']
        self.logger.info(f" Processing webhook event: {event_type}")
        
        try:
            if event_type == 'checkout.session.completed':
                await self.handle_checkout_session_completed(event['data']['object'])
            elif event_type == 'customer.subscription.created':
                await self.handle_customer_subscription_created(event['data']['object'])
            elif event_type == 'customer.subscription.updated':
                await self.handle_customer_subscription_updated(event['data']['object'])
            elif event_type == 'customer.subscription.deleted':
                await self.handle_customer_subscription_deleted(event['data']['object'])
            elif event_type == 'invoice.payment_succeeded':
                await self.handle_invoice_payment_succeeded(event['data']['object'])
            elif event_type == 'invoice.payment_failed':
                await self.handle_invoice_payment_failed(event['data']['object'])
            else:
                self.logger.info(f" Unhandled webhook event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f" Error processing webhook event {event_type}: {str(e)}")
            self.logger.error(f" Event data: {event}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def handle_checkout_session_completed(self, session: dict):
        """Handle completed checkout session - this is the first event after payment"""
        try:
            self.logger.info(f" Processing checkout session: {session['id']}")
            
            # Check if this is a subscription checkout
            if session.get('mode') != 'subscription':
                self.logger.info(f" Skipping non-subscription checkout: {session['mode']}")
                return
            
            # Get user info from metadata
            user_id = session.get('metadata', {}).get('user_id')
            if not user_id:
                self.logger.error(f" No user_id in checkout session metadata")
                return
            
            self.logger.info(f" Processing checkout for user: {user_id}")
            
            # If subscription is already created, get it
            if session.get('subscription'):
                subscription_id = session['subscription']
                self.logger.info(f" Subscription already exists: {subscription_id}")
                
                # Retrieve the full subscription object from Stripe
                subscription = stripe.Subscription.retrieve(subscription_id)
                await self.handle_customer_subscription_created(subscription)
            else:
                # Subscription might be created shortly after checkout completion
                # We'll wait for the customer.subscription.created event
                self.logger.info(f" Subscription not yet created, waiting for subscription.created event")
                
                # Update user profile to indicate payment was successful
                try:
                    profile_update = {
                        "subscription_status": "processing",
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    supabase.table("user_profiles").update(profile_update).eq("id", user_id).execute()
                    self.logger.info(f" Updated user profile to processing status")
                except Exception as e:
                    self.logger.error(f" Failed to update user profile: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f" Error handling checkout session: {str(e)}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            raise
    
    async def sync_subscription_from_stripe(self, user_email: str):
        """Manually sync a user's subscription from Stripe - useful for fixing stuck subscriptions"""
        try:
            self.logger.info(f" Manual sync for user: {user_email}")
            
            # Find user in database
            user_response = supabase.table("user_profiles").select("*").eq("email", user_email).execute()
            if not user_response.data:
                self.logger.error(f" User not found: {user_email}")
                return False
                
            user = user_response.data[0]
            user_id = user['id']
            stripe_customer_id = user.get('stripe_customer_id')
            
            if not stripe_customer_id:
                self.logger.error(f" No Stripe customer ID for user: {user_email}")
                return False
            
            # Get active subscriptions from Stripe
            subscriptions = stripe.Subscription.list(customer=stripe_customer_id, status='active')
            
            if not subscriptions.data:
                self.logger.info(f" No active subscriptions found for {user_email}")
                return False
            
            # Process the first active subscription
            subscription = subscriptions.data[0]
            self.logger.info(f" Processing subscription: {subscription.id}")
            
            # Simulate webhook event processing
            await self.handle_customer_subscription_created(subscription)
            
            self.logger.info(f" Manual sync completed for {user_email}")
            return True
            
        except Exception as e:
            self.logger.error(f" Error in manual sync: {str(e)}")
            self.logger.error(f" User email: {user_email}")
            import traceback
            self.logger.error(f" Traceback: {traceback.format_exc()}")
            return False

# Global instance
webhook_handler = StripeWebhookHandler()
