"""
Subscription Middleware
Enforces paywall by checking user subscription status before allowing chat access
"""

import logging
from fastapi import HTTPException, Request
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_service_role_key:
    raise ValueError("Supabase configuration missing")

supabase: Client = create_client(supabase_url, supabase_service_role_key)

logger = logging.getLogger(__name__)

class SubscriptionMiddleware:
    """Middleware to enforce subscription-based access control"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_subscription_access(self, user_id: str) -> dict:
        """
        Check if user has active subscription access
        
        Args:
            user_id: The user's UUID
            
        Returns:
            dict: Subscription info with access status
            
        Raises:
            HTTPException: 402 Payment Required if no active subscription
        """
        try:
            # Get user's subscription status from user_profiles (fast lookup)
            # Include provisional access fields for 24hr Standard Plan access
            user_response = supabase.table("user_profiles").select(
                "subscription_status, plan_tier, stripe_customer_id, provisional_access_until, provisional_plan_tier"
            ).eq("id", user_id).single().execute()
            
            if not user_response.data:
                self.logger.warning(f"User profile not found for user_id: {user_id}")
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "subscription_required",
                        "message": "Active subscription required to access chat features",
                        "action": "subscribe"
                    }
                )
            
            user_profile = user_response.data
            subscription_status = user_profile.get("subscription_status", "inactive")
            plan_tier = user_profile.get("plan_tier", "none")
            provisional_until = user_profile.get("provisional_access_until")
            provisional_tier = user_profile.get("provisional_plan_tier")
            
            # Check for provisional access first (24hr Standard Plan access)
            if provisional_until and provisional_tier:
                from datetime import datetime
                try:
                    expiry_time = datetime.fromisoformat(provisional_until.replace('Z', '+00:00'))
                    current_time = datetime.utcnow().replace(tzinfo=expiry_time.tzinfo)
                    
                    if current_time <= expiry_time:
                        self.logger.info(f"✅ User {user_id} has valid provisional {provisional_tier} access until {provisional_until}")
                        return {
                            "has_access": True,
                            "subscription_status": "active",  # Treat as active during provisional period
                            "plan_tier": provisional_tier,
                            "access_type": "provisional",
                            "provisional_until": provisional_until,
                            "stripe_customer_id": user_profile.get("stripe_customer_id")
                        }
                    else:
                        self.logger.info(f"⏰ User {user_id} provisional access expired at {provisional_until}")
                        # Provisional access expired - continue to regular subscription check
                except Exception as e:
                    self.logger.error(f"❌ Error parsing provisional access time for {user_id}: {str(e)}")
            
            # Check if user has active or trialing subscription
            if subscription_status not in ["active", "trialing"]:
                self.logger.info(f"User {user_id} blocked - subscription status: {subscription_status}")
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "subscription_required",
                        "message": f"Active subscription required. Current status: {subscription_status}",
                        "current_status": subscription_status,
                        "plan_tier": plan_tier,
                        "action": "subscribe"
                    }
                )
            
            # Get detailed subscription info for context
            subscription_response = supabase.rpc(
                "get_user_active_subscription",
                {"user_uuid": user_id}
            ).execute()
            
            return {
                "has_access": True,
                "subscription_status": subscription_status,
                "plan_tier": plan_tier,
                "access_type": "permanent",
                "stripe_customer_id": user_profile.get("stripe_customer_id"),
                "subscription_details": subscription_response.data[0] if subscription_response.data else None
            }
            
            self.logger.info(f"User {user_id} granted access - {plan_tier} plan, status: {subscription_status}")
            
        except HTTPException:
            # Re-raise HTTP exceptions (402 Payment Required)
            raise
        except Exception as e:
            self.logger.error(f"Error checking subscription for user {user_id}: {str(e)}")
            # On database errors, fail open with warning (don't block users)
            self.logger.warning(f"Allowing access due to subscription check error for user {user_id}")
            return {
                "has_access": True,
                "subscription_status": "unknown",
                "plan_tier": "unknown",
                "error": str(e)
            }
    
    async def enforce_subscription_middleware(self, request: Request, user_id: str):
        """
        Middleware function to enforce subscription access
        Attaches subscription info to request state for downstream use
        
        Args:
            request: FastAPI request object
            user_id: The user's UUID
            
        Raises:
            HTTPException: 402 Payment Required if no active subscription
        """
        subscription_info = await self.check_subscription_access(user_id)
        
        # Attach subscription info to request state for downstream use
        if not hasattr(request.state, "subscription"):
            request.state.subscription = subscription_info
        
        return subscription_info

# Global instance
subscription_middleware = SubscriptionMiddleware()

async def check_subscription_access(user_id: str) -> dict:
    """Convenience function for subscription checking"""
    return await subscription_middleware.check_subscription_access(user_id)

async def enforce_subscription(request: Request, user_id: str):
    """Convenience function for middleware enforcement"""
    return await subscription_middleware.enforce_subscription_middleware(request, user_id)
