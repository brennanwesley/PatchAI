"""
Webhook Redundancy Service - Phase 3 Production Hardening
Provides multiple webhook endpoints and failover mechanisms for maximum reliability
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

from services.supabase_service import supabase
from core.stripe_webhooks import StripeWebhookHandler

logger = logging.getLogger(__name__)

class WebhookStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class WebhookEvent:
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    received_at: datetime
    status: WebhookStatus
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    processed_by: Optional[str] = None

class WebhookRedundancyService:
    """
    Production-grade webhook redundancy service with multiple failover mechanisms
    """
    
    def __init__(self):
        self.webhook_handler = StripeWebhookHandler()
        self.max_retries = 5
        self.retry_delays = [1, 2, 5, 10, 30]  # seconds
        self.event_cache: Dict[str, WebhookEvent] = {}
        self.processing_lock = asyncio.Lock()
        
    async def receive_webhook(self, event_data: Dict[str, Any], endpoint_id: str = "primary") -> Dict[str, Any]:
        """
        Receive and process webhook with redundancy handling
        """
        try:
            event_id = event_data.get('id', '')
            event_type = event_data.get('type', '')
            
            correlation_id = f"WH-{event_id[:8]}-{int(time.time())}"
            logger.info(f"🔄 [WEBHOOK-{correlation_id}] Received {event_type} via {endpoint_id}")
            
            # Check for duplicate events
            if await self._is_duplicate_event(event_id):
                logger.info(f"⚠️ [WEBHOOK-{correlation_id}] Duplicate event {event_id} ignored")
                return {"success": True, "message": "Duplicate event ignored", "correlation_id": correlation_id}
            
            # Create webhook event record
            webhook_event = WebhookEvent(
                event_id=event_id,
                event_type=event_type,
                payload=event_data,
                received_at=datetime.utcnow(),
                status=WebhookStatus.PENDING
            )
            
            # Store event for tracking
            await self._store_webhook_event(webhook_event)
            self.event_cache[event_id] = webhook_event
            
            # Process webhook with redundancy
            result = await self._process_with_redundancy(webhook_event, correlation_id)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Webhook receive error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _is_duplicate_event(self, event_id: str) -> bool:
        """
        Check if event has already been processed
        """
        try:
            # Check cache first
            if event_id in self.event_cache:
                return True
            
            # Check database
            result = supabase.table("webhook_events").select("event_id").eq("event_id", event_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Duplicate check error: {str(e)}")
            return False
    
    async def _store_webhook_event(self, webhook_event: WebhookEvent):
        """
        Store webhook event for tracking and recovery
        """
        try:
            event_data = {
                "event_id": webhook_event.event_id,
                "event_type": webhook_event.event_type,
                "payload": json.dumps(webhook_event.payload),
                "received_at": webhook_event.received_at.isoformat(),
                "status": webhook_event.status.value,
                "attempts": webhook_event.attempts,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("webhook_events").insert(event_data).execute()
            logger.info(f"📝 [WEBHOOK] Stored event {webhook_event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Store event error: {str(e)}")
    
    async def _process_with_redundancy(self, webhook_event: WebhookEvent, correlation_id: str) -> Dict[str, Any]:
        """
        Process webhook with retry logic and redundancy
        """
        async with self.processing_lock:
            try:
                webhook_event.status = WebhookStatus.PROCESSING
                webhook_event.attempts += 1
                webhook_event.last_attempt = datetime.utcnow()
                
                logger.info(f"🔄 [WEBHOOK-{correlation_id}] Processing attempt {webhook_event.attempts}")
                
                # Process the webhook
                success = await self.webhook_handler.process_webhook_event(webhook_event.payload)
                
                if success:
                    webhook_event.status = WebhookStatus.SUCCESS
                    webhook_event.processed_by = "primary_handler"
                    
                    # Update database
                    await self._update_webhook_status(webhook_event)
                    
                    logger.info(f"✅ [WEBHOOK-{correlation_id}] Successfully processed {webhook_event.event_type}")
                    return {
                        "success": True,
                        "message": f"Webhook {webhook_event.event_type} processed successfully",
                        "correlation_id": correlation_id,
                        "attempts": webhook_event.attempts
                    }
                else:
                    # Failed - schedule retry if attempts remaining
                    return await self._handle_webhook_failure(webhook_event, correlation_id, "Primary handler failed")
                    
            except Exception as e:
                logger.error(f"❌ [WEBHOOK-{correlation_id}] Processing error: {str(e)}")
                return await self._handle_webhook_failure(webhook_event, correlation_id, str(e))
    
    async def _handle_webhook_failure(self, webhook_event: WebhookEvent, correlation_id: str, error_message: str) -> Dict[str, Any]:
        """
        Handle webhook processing failure with retry logic
        """
        webhook_event.error_message = error_message
        
        if webhook_event.attempts < self.max_retries:
            webhook_event.status = WebhookStatus.RETRY
            
            # Schedule retry
            retry_delay = self.retry_delays[min(webhook_event.attempts - 1, len(self.retry_delays) - 1)]
            logger.warning(f"⚠️ [WEBHOOK-{correlation_id}] Scheduling retry {webhook_event.attempts}/{self.max_retries} in {retry_delay}s")
            
            # Update database
            await self._update_webhook_status(webhook_event)
            
            # Schedule async retry
            asyncio.create_task(self._retry_webhook_after_delay(webhook_event, correlation_id, retry_delay))
            
            return {
                "success": False,
                "message": f"Webhook failed, retry scheduled in {retry_delay}s",
                "correlation_id": correlation_id,
                "attempts": webhook_event.attempts,
                "max_retries": self.max_retries
            }
        else:
            webhook_event.status = WebhookStatus.FAILED
            
            logger.error(f"❌ [WEBHOOK-{correlation_id}] Webhook failed permanently after {webhook_event.attempts} attempts")
            
            # Update database
            await self._update_webhook_status(webhook_event)
            
            # Trigger manual intervention alert
            await self._trigger_manual_intervention_alert(webhook_event)
            
            return {
                "success": False,
                "message": f"Webhook failed permanently after {webhook_event.attempts} attempts",
                "correlation_id": correlation_id,
                "error": error_message
            }
    
    async def _retry_webhook_after_delay(self, webhook_event: WebhookEvent, correlation_id: str, delay: int):
        """
        Retry webhook processing after delay
        """
        try:
            await asyncio.sleep(delay)
            logger.info(f"🔄 [WEBHOOK-{correlation_id}] Retrying webhook after {delay}s delay")
            
            # Retry processing
            await self._process_with_redundancy(webhook_event, correlation_id)
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK-{correlation_id}] Retry error: {str(e)}")
    
    async def _update_webhook_status(self, webhook_event: WebhookEvent):
        """
        Update webhook event status in database
        """
        try:
            update_data = {
                "status": webhook_event.status.value,
                "attempts": webhook_event.attempts,
                "last_attempt": webhook_event.last_attempt.isoformat() if webhook_event.last_attempt else None,
                "error_message": webhook_event.error_message,
                "processed_by": webhook_event.processed_by,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("webhook_events").update(update_data).eq("event_id", webhook_event.event_id).execute()
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Update status error: {str(e)}")
    
    async def _trigger_manual_intervention_alert(self, webhook_event: WebhookEvent):
        """
        Trigger alert for manual intervention when webhook fails permanently
        """
        try:
            alert_data = {
                "alert_type": "webhook_failure",
                "event_id": webhook_event.event_id,
                "event_type": webhook_event.event_type,
                "attempts": webhook_event.attempts,
                "error_message": webhook_event.error_message,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending"
            }
            
            supabase.table("manual_intervention_alerts").insert(alert_data).execute()
            logger.error(f"🚨 [WEBHOOK] Manual intervention alert created for {webhook_event.event_id}")
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Alert creation error: {str(e)}")
    
    async def get_webhook_stats(self) -> Dict[str, Any]:
        """
        Get webhook processing statistics
        """
        try:
            # Get stats from last 24 hours
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            result = supabase.table("webhook_events").select("status, event_type").gte("created_at", since).execute()
            
            stats = {
                "total_events": len(result.data),
                "success_rate": 0,
                "by_status": {},
                "by_type": {},
                "period": "24h"
            }
            
            if result.data:
                for event in result.data:
                    status = event.get("status", "unknown")
                    event_type = event.get("event_type", "unknown")
                    
                    stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                    stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
                
                success_count = stats["by_status"].get("success", 0)
                stats["success_rate"] = round((success_count / len(result.data)) * 100, 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Stats error: {str(e)}")
            return {"error": str(e)}
    
    async def recover_failed_webhooks(self) -> Dict[str, Any]:
        """
        Attempt to recover failed webhooks
        """
        try:
            # Get failed webhooks from last 24 hours
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            result = supabase.table("webhook_events").select("*").eq("status", "failed").gte("created_at", since).execute()
            
            recovered = 0
            failed = 0
            
            for event_data in result.data:
                try:
                    webhook_event = WebhookEvent(
                        event_id=event_data["event_id"],
                        event_type=event_data["event_type"],
                        payload=json.loads(event_data["payload"]),
                        received_at=datetime.fromisoformat(event_data["received_at"]),
                        status=WebhookStatus.RETRY,
                        attempts=0  # Reset attempts for recovery
                    )
                    
                    correlation_id = f"RECOVERY-{webhook_event.event_id[:8]}"
                    result = await self._process_with_redundancy(webhook_event, correlation_id)
                    
                    if result.get("success"):
                        recovered += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"❌ [WEBHOOK] Recovery error for {event_data.get('event_id')}: {str(e)}")
                    failed += 1
            
            return {
                "success": True,
                "recovered": recovered,
                "failed": failed,
                "total_attempted": len(result.data)
            }
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Recovery process error: {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance
webhook_redundancy_service = WebhookRedundancyService()
