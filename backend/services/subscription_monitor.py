"""
Subscription Monitoring Service
Provides safe automatic recovery and consistency checks for Stripe subscriptions
with built-in infinite loop prevention
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import stripe
from services.supabase_service import supabase
from core.stripe_webhooks import webhook_handler

logger = logging.getLogger(__name__)

class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class RecoveryAttempt:
    user_email: str
    attempt_count: int
    last_attempt: datetime
    status: RecoveryStatus
    error_message: Optional[str] = None

class SubscriptionMonitor:
    """
    Safe subscription monitoring with infinite loop prevention
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # SAFETY: Prevent infinite loops with strict limits
        self.MAX_RECOVERY_ATTEMPTS = 3  # Maximum attempts per user
        self.RECOVERY_COOLDOWN_HOURS = 24  # Hours between recovery attempts
        self.MAX_CONCURRENT_RECOVERIES = 5  # Prevent resource exhaustion
        self.CONSISTENCY_CHECK_INTERVAL = 3600  # 1 hour minimum between checks
        
        # Track recovery attempts to prevent loops
        self.recovery_attempts: Dict[str, RecoveryAttempt] = {}
        self.active_recoveries: Set[str] = set()
        self.last_consistency_check: Optional[datetime] = None
        
        # Webhook failure tracking
        self.webhook_failures: List[Dict] = []
        self.MAX_FAILURE_HISTORY = 100  # Limit memory usage
        
        self.logger.info("🛡️ SubscriptionMonitor initialized with safety limits")
        self.logger.info(f"   Max recovery attempts: {self.MAX_RECOVERY_ATTEMPTS}")
        self.logger.info(f"   Recovery cooldown: {self.RECOVERY_COOLDOWN_HOURS}h")
        self.logger.info(f"   Max concurrent recoveries: {self.MAX_CONCURRENT_RECOVERIES}")
    
    def record_webhook_failure(self, event_type: str, user_email: str, error: str):
        """Record webhook failure for monitoring"""
        failure_record = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "user_email": user_email,
            "error": error
        }
        
        self.webhook_failures.append(failure_record)
        
        # SAFETY: Limit memory usage
        if len(self.webhook_failures) > self.MAX_FAILURE_HISTORY:
            self.webhook_failures = self.webhook_failures[-self.MAX_FAILURE_HISTORY:]
        
        self.logger.warning(f"🚨 Webhook failure recorded: {event_type} for {user_email}")
        
        # Trigger safe recovery attempt
        asyncio.create_task(self._safe_recovery_attempt(user_email, f"webhook_failure_{event_type}"))
    
    async def _safe_recovery_attempt(self, user_email: str, trigger_reason: str):
        """
        Attempt recovery with comprehensive safety checks
        """
        try:
            # SAFETY CHECK 1: Prevent concurrent recoveries for same user
            if user_email in self.active_recoveries:
                self.logger.info(f"⏸️ Recovery already in progress for {user_email}, skipping")
                return
            
            # SAFETY CHECK 2: Check attempt limits
            if not self._can_attempt_recovery(user_email):
                self.logger.info(f"⏸️ Recovery attempt limit reached for {user_email}, skipping")
                return
            
            # SAFETY CHECK 3: Limit concurrent recoveries system-wide
            if len(self.active_recoveries) >= self.MAX_CONCURRENT_RECOVERIES:
                self.logger.warning(f"⏸️ Max concurrent recoveries reached ({self.MAX_CONCURRENT_RECOVERIES}), queuing")
                return
            
            # Mark as active to prevent concurrent attempts
            self.active_recoveries.add(user_email)
            
            # Update attempt tracking
            attempt = self.recovery_attempts.get(user_email, RecoveryAttempt(
                user_email=user_email,
                attempt_count=0,
                last_attempt=datetime.utcnow(),
                status=RecoveryStatus.PENDING
            ))
            
            attempt.attempt_count += 1
            attempt.last_attempt = datetime.utcnow()
            attempt.status = RecoveryStatus.IN_PROGRESS
            self.recovery_attempts[user_email] = attempt
            
            self.logger.info(f"🔄 Starting recovery attempt {attempt.attempt_count}/{self.MAX_RECOVERY_ATTEMPTS} for {user_email}")
            self.logger.info(f"   Trigger: {trigger_reason}")
            
            # Perform the actual recovery
            success = await webhook_handler.sync_subscription_from_stripe(user_email)
            
            if success:
                attempt.status = RecoveryStatus.SUCCESS
                attempt.error_message = None
                self.logger.info(f"✅ Recovery successful for {user_email}")
            else:
                attempt.status = RecoveryStatus.FAILED
                attempt.error_message = "Sync returned False"
                self.logger.error(f"❌ Recovery failed for {user_email}")
            
        except Exception as e:
            # Update failure status
            if user_email in self.recovery_attempts:
                self.recovery_attempts[user_email].status = RecoveryStatus.FAILED
                self.recovery_attempts[user_email].error_message = str(e)
            
            self.logger.error(f"💥 Recovery attempt failed for {user_email}: {str(e)}")
            
        finally:
            # SAFETY: Always remove from active set to prevent deadlock
            self.active_recoveries.discard(user_email)
    
    def _can_attempt_recovery(self, user_email: str) -> bool:
        """
        Check if recovery attempt is allowed (prevents infinite loops)
        """
        attempt = self.recovery_attempts.get(user_email)
        
        if not attempt:
            return True  # First attempt
        
        # Check attempt limit
        if attempt.attempt_count >= self.MAX_RECOVERY_ATTEMPTS:
            self.logger.info(f"⛔ Max attempts ({self.MAX_RECOVERY_ATTEMPTS}) reached for {user_email}")
            return False
        
        # Check cooldown period
        time_since_last = datetime.utcnow() - attempt.last_attempt
        cooldown_hours = timedelta(hours=self.RECOVERY_COOLDOWN_HOURS)
        
        if time_since_last < cooldown_hours:
            remaining = cooldown_hours - time_since_last
            self.logger.info(f"⏰ Cooldown active for {user_email}, {remaining} remaining")
            return False
        
        return True
    
    async def run_consistency_check(self, force: bool = False) -> Dict:
        """
        Run database consistency check with throttling to prevent loops
        """
        try:
            # SAFETY CHECK: Throttle consistency checks
            if not force and self.last_consistency_check:
                time_since_last = datetime.utcnow() - self.last_consistency_check
                min_interval = timedelta(seconds=self.CONSISTENCY_CHECK_INTERVAL)
                
                if time_since_last < min_interval:
                    remaining = min_interval - time_since_last
                    self.logger.info(f"⏰ Consistency check throttled, {remaining} remaining")
                    return {"status": "throttled", "remaining_seconds": remaining.total_seconds()}
            
            self.last_consistency_check = datetime.utcnow()
            
            self.logger.info("🔍 Starting subscription consistency check...")
            
            # Get all users with Stripe customer IDs
            users_response = supabase.table("user_profiles").select(
                "id, email, stripe_customer_id, subscription_status"
            ).not_.is_("stripe_customer_id", "null").execute()
            
            if not users_response.data:
                return {"status": "no_users", "message": "No users with Stripe customer IDs found"}
            
            results = {
                "total_users": len(users_response.data),
                "checked": 0,
                "inconsistencies_found": 0,
                "recovery_triggered": 0,
                "errors": 0
            }
            
            for user in users_response.data:
                try:
                    results["checked"] += 1
                    user_email = user["email"]
                    stripe_customer_id = user["stripe_customer_id"]
                    db_status = user["subscription_status"]
                    
                    # Check if user has active Stripe subscription
                    stripe_subs = stripe.Subscription.list(
                        customer=stripe_customer_id,
                        status="active",
                        limit=1
                    )
                    
                    has_active_stripe = len(stripe_subs.data) > 0
                    has_active_db = db_status == "active"
                    
                    # Check for inconsistency
                    if has_active_stripe and not has_active_db:
                        self.logger.warning(f"🔍 Inconsistency found: {user_email} has active Stripe but inactive DB")
                        results["inconsistencies_found"] += 1
                        
                        # Trigger safe recovery
                        if self._can_attempt_recovery(user_email):
                            await self._safe_recovery_attempt(user_email, "consistency_check")
                            results["recovery_triggered"] += 1
                    
                    # SAFETY: Add small delay to prevent API rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    results["errors"] += 1
                    self.logger.error(f"❌ Error checking user {user.get('email', 'unknown')}: {str(e)}")
            
            self.logger.info(f"✅ Consistency check complete: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"💥 Consistency check failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "active_recoveries": len(self.active_recoveries),
            "total_recovery_attempts": len(self.recovery_attempts),
            "recent_webhook_failures": len([
                f for f in self.webhook_failures 
                if (datetime.utcnow() - f["timestamp"]).total_seconds() < 3600
            ]),
            "last_consistency_check": self.last_consistency_check.isoformat() if self.last_consistency_check else None,
            "safety_limits": {
                "max_recovery_attempts": self.MAX_RECOVERY_ATTEMPTS,
                "recovery_cooldown_hours": self.RECOVERY_COOLDOWN_HOURS,
                "max_concurrent_recoveries": self.MAX_CONCURRENT_RECOVERIES,
                "consistency_check_interval": self.CONSISTENCY_CHECK_INTERVAL
            }
        }
    
    def reset_recovery_attempts(self, user_email: str) -> bool:
        """Reset recovery attempts for a user (admin function)"""
        if user_email in self.recovery_attempts:
            del self.recovery_attempts[user_email]
            self.logger.info(f"🔄 Reset recovery attempts for {user_email}")
            return True
        return False

# Global instance
subscription_monitor = SubscriptionMonitor()
