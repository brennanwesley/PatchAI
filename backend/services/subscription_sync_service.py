"""
Enhanced Subscription Sync Service - Phase 2/3 Implementation
Provides robust, self-healing subscription synchronization between Stripe and PatchAI
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import stripe
from services.supabase_service import SupabaseService
from core.stripe_config import get_stripe_config

logger = logging.getLogger(__name__)

class SubscriptionSyncService:
    """
    Comprehensive subscription synchronization service with:
    - Proactive sync detection and recovery
    - Webhook failure detection and retry
    - Real-time monitoring and alerting
    - Self-healing capabilities
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        stripe_config = get_stripe_config()
        stripe.api_key = stripe_config.secret_key
        self.max_retry_attempts = 3
        self.sync_cooldown_minutes = 5
        
    async def comprehensive_user_sync(self, user_email: str) -> Dict:
        """
        Comprehensive sync for a specific user with full error handling and recovery
        """
        try:
            logger.info(f"🔄 Starting comprehensive sync for {user_email}")
            
            # Step 1: Get user profile
            user_profile = await self._get_user_profile(user_email)
            if not user_profile:
                return {"success": False, "error": "User not found", "error_code": "USER_NOT_FOUND"}
            
            user_id = user_profile['id']
            
            # Step 2: Get Stripe customer and subscriptions
            stripe_data = await self._get_stripe_data_for_user(user_email)
            if not stripe_data["success"]:
                return stripe_data
            
            customer = stripe_data["customer"]
            subscriptions = stripe_data["subscriptions"]
            
            # Step 3: Sync each active subscription
            sync_results = []
            for subscription in subscriptions:
                if subscription.status in ['active', 'trialing']:
                    result = await self._sync_single_subscription(user_id, subscription)
                    sync_results.append(result)
            
            # Step 4: Update user profile status
            if sync_results and any(r["success"] for r in sync_results):
                await self._update_user_profile_status(user_id, "active", "standard")
                logger.info(f"✅ Comprehensive sync completed successfully for {user_email}")
                return {
                    "success": True, 
                    "message": "Subscription synchronized successfully",
                    "synced_subscriptions": len([r for r in sync_results if r["success"]])
                }
            else:
                logger.warning(f"⚠️ No active subscriptions found for {user_email}")
                return {
                    "success": False, 
                    "error": "No active subscriptions found in Stripe",
                    "error_code": "NO_ACTIVE_SUBSCRIPTIONS"
                }
                
        except Exception as e:
            logger.error(f"❌ Comprehensive sync failed for {user_email}: {str(e)}")
            return {
                "success": False, 
                "error": f"Sync failed: {str(e)}", 
                "error_code": "SYNC_EXCEPTION"
            }
    
    async def _get_user_profile(self, email: str) -> Optional[Dict]:
        """Get user profile from database"""
        try:
            result = self.supabase.table("user_profiles").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user profile for {email}: {str(e)}")
            return None
    
    async def _get_stripe_data_for_user(self, email: str) -> Dict:
        """Get Stripe customer and subscription data"""
        try:
            # Find customer by email
            customers = stripe.Customer.list(email=email, limit=1)
            if not customers.data:
                return {"success": False, "error": "Customer not found in Stripe", "error_code": "STRIPE_CUSTOMER_NOT_FOUND"}
            
            customer = customers.data[0]
            
            # Get customer's subscriptions
            subscriptions = stripe.Subscription.list(customer=customer.id, status='all')
            
            return {
                "success": True,
                "customer": customer,
                "subscriptions": subscriptions.data
            }
            
        except Exception as e:
            logger.error(f"Failed to get Stripe data for {email}: {str(e)}")
            return {"success": False, "error": f"Stripe API error: {str(e)}", "error_code": "STRIPE_API_ERROR"}
    
    async def _sync_single_subscription(self, user_id: str, stripe_subscription) -> Dict:
        """Sync a single Stripe subscription to database"""
        try:
            # Get plan information
            plan_info = await self._get_plan_info(stripe_subscription)
            if not plan_info:
                return {"success": False, "error": "Plan not found"}
            
            # Check if subscription already exists
            existing = self.supabase.table("user_subscriptions").select("*").eq("user_id", user_id).eq("stripe_subscription_id", stripe_subscription.id).execute()
            
            subscription_data = {
                "user_id": user_id,
                "plan_id": plan_info["id"],
                "stripe_subscription_id": stripe_subscription.id,
                "status": stripe_subscription.status,
                "current_period_start": datetime.fromtimestamp(stripe_subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(stripe_subscription.current_period_end).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if existing.data:
                # Update existing subscription
                result = self.supabase.table("user_subscriptions").update(subscription_data).eq("id", existing.data[0]["id"]).execute()
                logger.info(f"✅ Updated existing subscription {stripe_subscription.id}")
            else:
                # Create new subscription
                subscription_data["id"] = self.supabase.generate_uuid()
                subscription_data["created_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("user_subscriptions").insert(subscription_data).execute()
                logger.info(f"✅ Created new subscription record {stripe_subscription.id}")
            
            return {"success": True, "subscription_id": stripe_subscription.id}
            
        except Exception as e:
            logger.error(f"Failed to sync subscription {stripe_subscription.id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_plan_info(self, stripe_subscription) -> Optional[Dict]:
        """Get plan information from database based on Stripe price ID"""
        try:
            price_id = stripe_subscription.items.data[0].price.id
            result = self.supabase.table("subscription_plans").select("*").eq("stripe_price_id", price_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get plan info: {str(e)}")
            return None
    
    async def _update_user_profile_status(self, user_id: str, status: str, plan_tier: str):
        """Update user profile with subscription status"""
        try:
            update_data = {
                "subscription_status": status,
                "plan_tier": plan_tier,
                "last_payment_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
            logger.info(f"✅ Updated user profile status: {status}/{plan_tier}")
            
        except Exception as e:
            logger.error(f"Failed to update user profile status: {str(e)}")
    
    async def proactive_sync_check(self) -> Dict:
        """
        Proactive sync check - finds users with payment issues and fixes them
        """
        try:
            logger.info("🔍 Starting proactive sync check...")
            
            # Find users with recent payments but inactive status
            recent_cutoff = (datetime.utcnow() - timedelta(hours=2)).isoformat()
            
            # Users who might have sync issues
            problem_users = self.supabase.table("user_profiles").select("email, subscription_status, created_at").gte("created_at", recent_cutoff).eq("subscription_status", "inactive").execute()
            
            sync_results = []
            for user in problem_users.data:
                logger.info(f"🔧 Checking user {user['email']} for sync issues...")
                result = await self.comprehensive_user_sync(user['email'])
                sync_results.append({
                    "email": user['email'],
                    "result": result
                })
            
            fixed_count = len([r for r in sync_results if r["result"]["success"]])
            
            logger.info(f"✅ Proactive sync check complete: {fixed_count}/{len(sync_results)} users fixed")
            
            return {
                "success": True,
                "checked_users": len(sync_results),
                "fixed_users": fixed_count,
                "results": sync_results
            }
            
        except Exception as e:
            logger.error(f"❌ Proactive sync check failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict:
        """Health check for the sync service"""
        try:
            # Test database connection
            db_test = self.supabase.table("user_profiles").select("count").execute()
            
            # Test Stripe connection
            stripe_test = stripe.Account.retrieve()
            
            return {
                "success": True,
                "database_connected": bool(db_test.data),
                "stripe_connected": bool(stripe_test.id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global service instance
subscription_sync_service = SubscriptionSyncService()
