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
        # Import here to avoid circular imports
        self._monitor = None
    
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
                    
                    # CRITICAL FIX: Get subscription details from Stripe to update status
                    try:
                        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                        subscription_status = stripe_subscription.status
                        
                        # Get plan information from subscription
                        plan_tier = "standard"  # Default
                        if stripe_subscription.items and stripe_subscription.items.data:
                            price_id = stripe_subscription.items.data[0].price.id
                            plan_response = supabase.table("subscription_plans").select(
                                "plan_id"
                            ).eq("stripe_price_id", price_id).single().execute()
                            
                            if plan_response.data:
                                plan_tier = plan_response.data['plan_id']
                        
                        # Update user profile with subscription status AND plan tier
                        profile_update = {
                            "last_payment_at": datetime.utcnow().isoformat(),
                            "subscription_status": subscription_status,
                            "plan_tier": plan_tier,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        
                        supabase.table("user_profiles").update(profile_update).eq("id", user_id).execute()
                        
                        self.logger.info(f" ✅ CRITICAL FIX: Updated subscription status for user {user_id}: {subscription_status} ({plan_tier})")
                        
                    except Exception as status_error:
                        self.logger.error(f" ❌ Failed to update subscription status: {str(status_error)}")
                        # Fallback: just update payment date
                        supabase.table("user_profiles").update({
                            "last_payment_at": datetime.utcnow().isoformat()
                        }).eq("id", user_id).execute()
                    
                    self.logger.info(f" Recorded successful payment for user {user_id}: ${amount/100}")
                    
                    # Process referral rewards if user was referred
                    await self._process_referral_rewards(user_id, amount, transaction_result.data[0]['id'] if transaction_result.data else None)
                else:
                    # FALLBACK: No subscription record found, but payment succeeded
                    # This handles cases where customer.subscription.created webhook failed
                    self.logger.warning(f" No subscription record found for Stripe subscription {subscription_id}")
                    
                    try:
                        # Get subscription details directly from Stripe
                        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                        customer_id = stripe_subscription.customer
                        
                        # Find user by Stripe customer ID
                        user_response = supabase.table("user_profiles").select(
                            "id, email"
                        ).eq("stripe_customer_id", customer_id).single().execute()
                        
                        if user_response.data:
                            user_id = user_response.data['id']
                            user_email = user_response.data['email']
                            
                            self.logger.info(f" ⚠️ FALLBACK: Processing payment for user {user_email} without subscription record")
                            
                            # Create the missing subscription record
                            await self.handle_customer_subscription_created(stripe_subscription)
                            
                            # Update user profile with active status
                            profile_update = {
                                "last_payment_at": datetime.utcnow().isoformat(),
                                "subscription_status": stripe_subscription.status,
                                "plan_tier": "standard",  # Default
                                "updated_at": datetime.utcnow().isoformat()
                            }
                            
                            supabase.table("user_profiles").update(profile_update).eq("id", user_id).execute()
                            
                            self.logger.info(f" ✅ FALLBACK SUCCESS: Fixed subscription for {user_email}")
                        else:
                            self.logger.error(f" ❌ FALLBACK FAILED: No user found for customer {customer_id}")
                            
                    except Exception as fallback_error:
                        self.logger.error(f" ❌ FALLBACK ERROR: {str(fallback_error)}")
            
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
            ).eq("referrer_user_id", referring_user_id).eq("referee_user_id", referred_user_id).single().execute()
            
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
                "referrer_user_id": referring_user_id,
                "referee_user_id": referred_user_id,
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
    
    @property
    def monitor(self):
        """Lazy load monitor to avoid circular imports"""
        if self._monitor is None:
            try:
                from services.subscription_monitor import subscription_monitor
                self._monitor = subscription_monitor
            except ImportError:
                self.logger.warning("Subscription monitor not available")
                self._monitor = None
        return self._monitor
    
    async def process_webhook_event(self, event: dict):
        """Process webhook event based on type with monitoring integration"""
        event_type = event['type']
        self.logger.info(f" Processing webhook event: {event_type}")
        
        # Extract user email for monitoring (if available)
        user_email = None
        try:
            if event_type in ['customer.subscription.created', 'customer.subscription.updated']:
                customer_id = event['data']['object'].get('customer')
                if customer_id:
                    customer = stripe.Customer.retrieve(customer_id)
                    user_email = customer.email
            elif event_type == 'invoice.payment_succeeded':
                customer_id = event['data']['object'].get('customer')
                if customer_id:
                    customer = stripe.Customer.retrieve(customer_id)
                    user_email = customer.email
        except Exception as e:
            self.logger.debug(f"Could not extract user email for monitoring: {str(e)}")
        
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
            
            # Record failure for monitoring and potential recovery
            if self.monitor and user_email:
                self.monitor.record_webhook_failure(event_type, user_email, str(e))
            
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
        """Manually sync a user's subscription from Stripe - robust version with multiple fallback strategies"""
        try:
            self.logger.info(f"🔄 SYNC: Starting manual sync for user: {user_email}")
            
            # Find user in database with comprehensive error handling
            try:
                user_response = supabase.table("user_profiles").select("*").eq("email", user_email).execute()
                if not user_response.data:
                    self.logger.error(f"❌ SYNC: User not found in database: {user_email}")
                    return False
                    
                user = user_response.data[0]
                user_id = user['id']
                stripe_customer_id = user.get('stripe_customer_id')
                
                self.logger.info(f"✅ SYNC: Found user {user_id} with customer ID: {stripe_customer_id}")
                
            except Exception as e:
                self.logger.error(f"❌ SYNC: Database query failed: {str(e)}")
                return False
            
            if not stripe_customer_id:
                self.logger.error(f"❌ SYNC: No Stripe customer ID for user: {user_email}")
                return False
            
            # Get ALL subscriptions from Stripe (active, past_due, trialing, etc.)
            try:
                self.logger.info(f"🔍 SYNC: Querying Stripe for customer: {stripe_customer_id}")
                
                # Check multiple subscription statuses
                all_subscriptions = []
                for status in ['active', 'past_due', 'trialing', 'incomplete']:
                    subs = stripe.Subscription.list(customer=stripe_customer_id, status=status)
                    all_subscriptions.extend(subs.data)
                    self.logger.info(f"🔍 SYNC: Found {len(subs.data)} {status} subscriptions")
                
                if not all_subscriptions:
                    self.logger.warning(f"⚠️ SYNC: No subscriptions found for customer {stripe_customer_id}")
                    # Try to get recent payments as fallback
                    try:
                        payments = stripe.PaymentIntent.list(customer=stripe_customer_id, limit=10)
                        recent_successful = [p for p in payments.data if p.status == 'succeeded']
                        if recent_successful:
                            self.logger.info(f"💰 SYNC: Found {len(recent_successful)} recent successful payments")
                            # If we have recent payments but no subscriptions, this indicates a webhook failure
                            self.logger.error(f"🚨 SYNC: WEBHOOK FAILURE DETECTED - Recent payments exist but no subscriptions processed")
                    except Exception as payment_e:
                        self.logger.error(f"❌ SYNC: Could not check recent payments: {str(payment_e)}")
                    return False
                
                # Process the most recent subscription
                subscription = max(all_subscriptions, key=lambda s: s.created)
                self.logger.info(f"✅ SYNC: Processing most recent subscription: {subscription.id} (status: {subscription.status})")
                
            except Exception as e:
                self.logger.error(f"❌ SYNC: Stripe API query failed: {str(e)}")
                return False
            
            # Enhanced subscription processing with validation
            try:
                self.logger.info(f"🔧 SYNC: Processing subscription data...")
                
                # Validate subscription has required data
                if not subscription.get('items') or not subscription['items'].get('data'):
                    self.logger.error(f"❌ SYNC: Subscription missing items data: {subscription.id}")
                    return False
                
                price_id = subscription['items']['data'][0]['price']['id']
                self.logger.info(f"💰 SYNC: Subscription price ID: {price_id}")
                
                # Check if subscription already exists in database
                existing_sub = supabase.table("user_subscriptions").select("id").eq(
                    "stripe_subscription_id", subscription.id
                ).execute()
                
                if existing_sub.data:
                    self.logger.info(f"ℹ️ SYNC: Subscription already exists in database, updating status...")
                    # Update existing subscription
                    await self.handle_customer_subscription_updated(subscription)
                else:
                    self.logger.info(f"🆕 SYNC: Creating new subscription record...")
                    # Create new subscription
                    await self.handle_customer_subscription_created(subscription)
                
                # Verify the sync worked by checking database
                verification = supabase.table("user_profiles").select(
                    "subscription_status, plan_tier"
                ).eq("id", user_id).single().execute()
                
                if verification.data:
                    new_status = verification.data.get('subscription_status')
                    new_tier = verification.data.get('plan_tier')
                    self.logger.info(f"✅ SYNC: Verification - Status: {new_status}, Tier: {new_tier}")
                    
                    if new_status != 'inactive' and new_tier != 'none':
                        self.logger.info(f"🎉 SYNC: Manual sync completed successfully for {user_email}")
                        return True
                    else:
                        self.logger.error(f"❌ SYNC: Sync failed - user still inactive after processing")
                        return False
                else:
                    self.logger.error(f"❌ SYNC: Could not verify sync results")
                    return False
                
            except Exception as e:
                self.logger.error(f"❌ SYNC: Subscription processing failed: {str(e)}")
                import traceback
                self.logger.error(f"❌ SYNC: Processing traceback: {traceback.format_exc()}")
                return False
            
        except Exception as e:
            self.logger.error(f"💥 SYNC: Unexpected error in manual sync: {str(e)}")
            self.logger.error(f"💥 SYNC: User email: {user_email}")
            import traceback
            self.logger.error(f"💥 SYNC: Full traceback: {traceback.format_exc()}")
            return False

# Global instance
webhook_handler = StripeWebhookHandler()
