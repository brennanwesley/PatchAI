"""
High-performance memory-based rate limiter with subscription-tier awareness
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """High-performance memory-based rate limiter with subscription-tier awareness"""
    
    def __init__(self):
        # Memory-based counters for microsecond performance
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        self.ip_requests: Dict[str, deque] = defaultdict(deque)
        
        # Subscription tier limits (messages per day)
        self.TIER_LIMITS = {
            'free': 10,
            'standard': 1000,
            'premium': 5000,
            'default': 1000  # Default to standard tier (1000 messages/day)
        }
        
        # IP-based limits (per hour to prevent abuse)
        self.IP_LIMIT_PER_HOUR = 100
        
        logger.info("Rate limiter initialized with subscription-tier awareness")
    
    def _cleanup_old_requests(self, request_queue: deque, time_window: int):
        """Remove requests older than time_window seconds"""
        current_time = time.time()
        while request_queue and current_time - request_queue[0] > time_window:
            request_queue.popleft()
    
    def _get_user_tier(self, user_id: str) -> str:
        """Get user's subscription tier - placeholder for future subscription system"""
        # TODO: Replace with actual subscription tier lookup from database
        
        # For now, return 'standard' for all users (1000 messages per day)
        # This gives all users the standard plan by default
        return 'standard'
    
    def check_user_limit(self, user_id: str) -> Tuple[bool, int, int]:
        """Check if user has exceeded their daily message limit"""
        current_time = time.time()
        
        # Clean up old requests (24 hours = 86400 seconds)
        self._cleanup_old_requests(self.user_requests[user_id], 86400)
        
        # Get user's subscription tier and limit
        tier = self._get_user_tier(user_id)
        daily_limit = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['default'])
        
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
        tier = self._get_user_tier(user_id)
        daily_limit = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['default'])
        
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
