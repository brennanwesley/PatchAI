"""
High-performance memory-based rate limiter with subscription-tier awareness
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Tuple
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Supabase client for subscription lookups
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if supabase_url and supabase_service_role_key:
    supabase: Client = create_client(supabase_url, supabase_service_role_key)
else:
    supabase = None
    logger.warning("Supabase not configured - rate limiter will use fallback limits")


class RateLimiter:
    """High-performance memory-based rate limiter with subscription-tier awareness"""
    
    def __init__(self):
        # Memory-based counters for microsecond performance
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        self.ip_requests: Dict[str, deque] = defaultdict(deque)
        
        # Fallback tier limits (messages per day) - used when database is unavailable
        self.FALLBACK_TIER_LIMITS = {
            'free': 10,
            'standard': 1000,
            'premium': 5000,
            'default': 1000  # Default to standard tier (1000 messages/day)
        }
        
        # IP-based limits (per hour to prevent abuse)
        self.IP_LIMIT_PER_HOUR = 100
        
        logger.info("Rate limiter initialized with database-driven subscription limits")
    
    def _cleanup_old_requests(self, request_queue: deque, time_window: int):
        """Remove requests older than time_window seconds"""
        current_time = time.time()
        while request_queue and current_time - request_queue[0] > time_window:
            request_queue.popleft()
    
    def _get_user_tier_and_limit(self, user_id: str) -> Tuple[str, int]:
        """
        Get user's subscription tier and message limit from database
        
        Returns:
            Tuple[str, int]: (tier_name, daily_message_limit)
        """
        try:
            if not supabase:
                # Fallback to default limits if Supabase not configured
                return 'standard', self.FALLBACK_TIER_LIMITS['standard']
            
            # Get user's active subscription info
            response = supabase.rpc(
                "get_user_active_subscription",
                {"user_uuid": user_id}
            ).execute()
            
            if response.data and len(response.data) > 0:
                subscription = response.data[0]
                plan_tier = subscription.get('plan_id', 'standard')
                message_limit = subscription.get('message_limit', 1000)
                
                logger.debug(f"User {user_id} has {plan_tier} plan with {message_limit} messages/day")
                return plan_tier, message_limit
            else:
                # No active subscription found - check user_profiles for plan_tier
                user_response = supabase.table("user_profiles").select(
                    "plan_tier, subscription_status"
                ).eq("id", user_id).single().execute()
                
                if user_response.data:
                    plan_tier = user_response.data.get('plan_tier', 'standard')
                    subscription_status = user_response.data.get('subscription_status', 'inactive')
                    
                    # If user has no active subscription, use fallback limits
                    if subscription_status not in ['active', 'trialing']:
                        logger.info(f"User {user_id} has no active subscription, using fallback limits")
                        return 'standard', self.FALLBACK_TIER_LIMITS['standard']
                    
                    # Get message limit from subscription_plans table
                    plan_response = supabase.table("subscription_plans").select(
                        "message_limit"
                    ).eq("plan_id", plan_tier).single().execute()
                    
                    if plan_response.data:
                        message_limit = plan_response.data.get('message_limit', 1000)
                        return plan_tier, message_limit
                
                # Fallback to standard plan
                logger.warning(f"Could not determine subscription for user {user_id}, using standard fallback")
                return 'standard', self.FALLBACK_TIER_LIMITS['standard']
                
        except Exception as e:
            logger.error(f"Error getting subscription info for user {user_id}: {str(e)}")
            # Fallback to standard plan on error
            return 'standard', self.FALLBACK_TIER_LIMITS['standard']
    
    def check_user_limit(self, user_id: str) -> Tuple[bool, int, int]:
        """Check if user has exceeded their daily message limit"""
        current_time = time.time()
        
        # Clean up old requests (24 hours = 86400 seconds)
        self._cleanup_old_requests(self.user_requests[user_id], 86400)
        
        # Get user's subscription tier and limit
        tier, daily_limit = self._get_user_tier_and_limit(user_id)
        
        # Count current requests
        current_count = len(self.user_requests[user_id])
        
        # Check if limit exceeded
        if current_count >= daily_limit:
            return False, current_count, daily_limit
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        
        return True, current_count + 1, daily_limit
    
    def check_ip_limit(self, client_ip: str) -> Tuple[bool, int]:
        """Check if IP has exceeded hourly request limit"""
        current_time = time.time()
        
        # Clean up old requests (1 hour = 3600 seconds)
        self._cleanup_old_requests(self.ip_requests[client_ip], 3600)
        
        # Count current requests
        current_count = len(self.ip_requests[client_ip])
        
        # Check if limit exceeded
        if current_count >= self.IP_LIMIT_PER_HOUR:
            return False, current_count
        
        # Add current request
        self.ip_requests[client_ip].append(current_time)
        
        return True, current_count + 1
    
    def get_user_status(self, user_id: str) -> Dict:
        """Get current rate limit status for user"""
        current_time = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(self.user_requests[user_id], 86400)
        
        # Get user's subscription tier and limit
        tier, daily_limit = self._get_user_tier_and_limit(user_id)
        
        # Count current requests
        current_count = len(self.user_requests[user_id])
        
        # Calculate time until reset (next day at midnight UTC)
        import datetime
        now = datetime.datetime.utcnow()
        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        reset_time = int(next_midnight.timestamp())
        
        return {
            'user_id': user_id,
            'subscription_tier': tier,
            'requests_used': current_count,
            'requests_limit': daily_limit,
            'requests_remaining': max(0, daily_limit - current_count),
            'reset_time': reset_time,
            'reset_in_seconds': max(0, reset_time - int(current_time))
        }
    
    def get_ip_status(self, client_ip: str) -> Dict:
        """Get current rate limit status for IP"""
        current_time = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(self.ip_requests[client_ip], 3600)
        
        # Count current requests
        current_count = len(self.ip_requests[client_ip])
        
        # Calculate time until reset (next hour)
        reset_time = int(current_time) + (3600 - (int(current_time) % 3600))
        
        return {
            'client_ip': client_ip,
            'requests_used': current_count,
            'requests_limit': self.IP_LIMIT_PER_HOUR,
            'requests_remaining': max(0, self.IP_LIMIT_PER_HOUR - current_count),
            'reset_time': reset_time,
            'reset_in_seconds': max(0, reset_time - int(current_time))
        }
