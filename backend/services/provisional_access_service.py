"""
Provisional Access Service
Handles 24-hour provisional Standard Plan access verification and cleanup
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import stripe
import os
from services.supabase_service import supabase

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class ProvisionalAccessService:
    """Service to manage provisional access verification and cleanup"""
    
    def __init__(self):
        self.logger = logger
        
    async def verify_provisional_payments(self) -> Dict[str, int]:
        """
        Check all users with provisional access and verify their payment status
        Returns summary of actions taken
        """
        try:
            self.logger.info("🔍 Starting provisional access verification sweep...")
            
            # Get all users with provisional access
            provisional_users = await self._get_provisional_users()
            
            if not provisional_users:
                self.logger.info("✅ No users with provisional access found")
                return {"verified": 0, "expired": 0, "errors": 0}
            
            self.logger.info(f"📋 Found {len(provisional_users)} users with provisional access")
            
            verified_count = 0
            expired_count = 0
            error_count = 0
            
            for user in provisional_users:
                try:
                    result = await self._verify_single_user(user)
                    if result == "verified":
                        verified_count += 1
                    elif result == "expired":
                        expired_count += 1
                except Exception as e:
                    self.logger.error(f"❌ Error verifying user {user.get('id', 'unknown')}: {str(e)}")
                    error_count += 1
            
            summary = {
                "verified": verified_count,
                "expired": expired_count, 
                "errors": error_count
            }
            
            self.logger.info(f"✅ Verification complete: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"💥 Failed to verify provisional payments: {str(e)}")
            raise
    
    async def _get_provisional_users(self) -> List[Dict]:
        """Get all users with active provisional access"""
        try:
            result = supabase.table("user_profiles").select(
                "id, email, provisional_access_until, provisional_plan_tier, payment_intent_id, subscription_status, plan_tier"
            ).not_.is_("provisional_access_until", "null").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch provisional users: {str(e)}")
            raise
    
    async def _verify_single_user(self, user: Dict) -> str:
        """
        Verify a single user's payment status and update accordingly
        Returns: 'verified', 'expired', or 'pending'
        """
        user_id = user.get('id')
        email = user.get('email')
        provisional_until = user.get('provisional_access_until')
        payment_intent_id = user.get('payment_intent_id')
        
        self.logger.info(f"🔍 Verifying user {email} (ID: {user_id})")
        
        # Check if provisional access has expired
        if provisional_until:
            expiry_time = datetime.fromisoformat(provisional_until.replace('Z', '+00:00'))
            if datetime.utcnow().replace(tzinfo=expiry_time.tzinfo) > expiry_time:
                self.logger.info(f"⏰ Provisional access expired for {email}")
                return await self._handle_expired_access(user)
        
        # Check if user has completed payment via Stripe
        payment_confirmed = await self._check_stripe_payment(email, payment_intent_id)
        
        if payment_confirmed:
            self.logger.info(f"✅ Payment confirmed for {email} - converting to permanent subscription")
            return await self._convert_to_permanent(user)
        else:
            self.logger.info(f"⏳ Payment still pending for {email}")
            return "pending"
    
    async def _check_stripe_payment(self, email: str, payment_intent_id: str) -> bool:
        """Check if user has completed payment in Stripe"""
        try:
            # Check if user has active subscription in Stripe
            customers = stripe.Customer.list(email=email, limit=1)
            
            if not customers.data:
                self.logger.info(f"📭 No Stripe customer found for {email}")
                return False
            
            customer = customers.data[0]
            subscriptions = stripe.Subscription.list(customer=customer.id, status='active', limit=1)
            
            if subscriptions.data:
                self.logger.info(f"💳 Active Stripe subscription found for {email}")
                return True
            
            # Also check for successful payment intents
            if payment_intent_id and payment_intent_id.startswith('provisional_'):
                # For provisional payment intents, check recent successful payments
                payment_intents = stripe.PaymentIntent.list(
                    customer=customer.id,
                    limit=10
                )
                
                for pi in payment_intents.data:
                    if pi.status == 'succeeded' and pi.created > (datetime.utcnow() - timedelta(hours=48)).timestamp():
                        self.logger.info(f"💰 Recent successful payment found for {email}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking Stripe payment for {email}: {str(e)}")
            return False
    
    async def _convert_to_permanent(self, user: Dict) -> str:
        """Convert provisional access to permanent subscription"""
        try:
            user_id = user.get('id')
            email = user.get('email')
            
            # Clear provisional access fields and ensure permanent subscription
            update_data = {
                "subscription_status": "active",
                "plan_tier": "standard",
                "provisional_access_until": None,
                "provisional_plan_tier": None,
                "payment_intent_id": None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
            
            if result.data:
                self.logger.info(f"✅ Successfully converted {email} to permanent Standard subscription")
                return "verified"
            else:
                self.logger.error(f"❌ Failed to update user profile for {email}")
                return "error"
                
        except Exception as e:
            self.logger.error(f"💥 Error converting to permanent for {user.get('email', 'unknown')}: {str(e)}")
            raise
    
    async def _handle_expired_access(self, user: Dict) -> str:
        """Handle expired provisional access - revert to free tier"""
        try:
            user_id = user.get('id')
            email = user.get('email')
            
            # Check one more time if payment was completed
            payment_confirmed = await self._check_stripe_payment(email, user.get('payment_intent_id'))
            
            if payment_confirmed:
                self.logger.info(f"🎉 Last-minute payment found for {email} - converting to permanent")
                return await self._convert_to_permanent(user)
            
            # No payment found - revert to free tier
            update_data = {
                "subscription_status": "inactive",
                "plan_tier": "free",
                "provisional_access_until": None,
                "provisional_plan_tier": None,
                "payment_intent_id": None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
            
            if result.data:
                self.logger.info(f"⏰ Successfully reverted {email} to free tier (provisional access expired)")
                return "expired"
            else:
                self.logger.error(f"❌ Failed to revert user profile for {email}")
                return "error"
                
        except Exception as e:
            self.logger.error(f"💥 Error handling expired access for {user.get('email', 'unknown')}: {str(e)}")
            raise

# Global service instance
provisional_access_service = ProvisionalAccessService()
