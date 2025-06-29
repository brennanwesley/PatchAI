"""
Monitoring Routes
Provides endpoints for subscription sync monitoring and manual recovery
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.auth import verify_jwt_token
from services.subscription_monitor import subscription_monitor
from services.background_monitor import background_monitor

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

class ConsistencyCheckRequest(BaseModel):
    force: bool = False

class RecoveryResetRequest(BaseModel):
    user_email: str

@router.get("/subscription-status")
async def get_subscription_monitoring_status(current_user: dict = Depends(verify_jwt_token)):
    """
    Get current subscription monitoring status
    """
    try:
        status = subscription_monitor.get_monitoring_status()
        return {
            "status": "success",
            "monitoring": status
        }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consistency-check")
async def run_consistency_check(
    request: ConsistencyCheckRequest,
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Run subscription consistency check
    """
    try:
        logger.info(f"🔍 Manual consistency check requested by user {current_user.get('email', 'unknown')}")
        
        result = await subscription_monitor.run_consistency_check(force=request.force)
        
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error running consistency check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-recovery-attempts")
async def reset_recovery_attempts(
    request: RecoveryResetRequest,
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Reset recovery attempts for a specific user (admin function)
    """
    try:
        logger.info(f"🔄 Recovery reset requested for {request.user_email} by {current_user.get('email', 'unknown')}")
        
        success = subscription_monitor.reset_recovery_attempts(request.user_email)
        
        return {
            "status": "success",
            "reset": success,
            "message": f"Recovery attempts {'reset' if success else 'not found'} for {request.user_email}"
        }
    except Exception as e:
        logger.error(f"Error resetting recovery attempts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook-failures")
async def get_recent_webhook_failures(current_user: dict = Depends(verify_jwt_token)):
    """
    Get recent webhook failures for debugging
    """
    try:
        # Get recent failures (last 24 hours)
        from datetime import datetime, timedelta
        
        recent_failures = [
            {
                "timestamp": f["timestamp"].isoformat(),
                "event_type": f["event_type"],
                "user_email": f["user_email"],
                "error": f["error"]
            }
            for f in subscription_monitor.webhook_failures
            if (datetime.utcnow() - f["timestamp"]).total_seconds() < 86400  # 24 hours
        ]
        
        return {
            "status": "success",
            "failures": recent_failures,
            "count": len(recent_failures)
        }
    except Exception as e:
        logger.error(f"Error getting webhook failures: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/background-status")
async def get_background_monitor_status(current_user: dict = Depends(verify_jwt_token)):
    """
    Get background monitor status
    """
    try:
        status = background_monitor.get_status()
        return {
            "status": "success",
            "background_monitor": status
        }
    except Exception as e:
        logger.error(f"Error getting background monitor status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def monitoring_health():
    """
    Health check for monitoring service
    """
    try:
        status = subscription_monitor.get_monitoring_status()
        background_status = background_monitor.get_status()
        
        # Basic health indicators
        health_status = "healthy"
        issues = []
        
        # Check for excessive active recoveries
        if status["active_recoveries"] >= subscription_monitor.MAX_CONCURRENT_RECOVERIES:
            health_status = "degraded"
            issues.append("Maximum concurrent recoveries reached")
        
        # Check for recent failures
        recent_failures = status["recent_webhook_failures"]
        if recent_failures > 10:  # More than 10 failures in last hour
            health_status = "degraded"
            issues.append(f"High webhook failure rate: {recent_failures} in last hour")
        
        # Check background monitor
        if not background_status["is_running"]:
            health_status = "degraded"
            issues.append("Background monitor not running")
        
        return {
            "status": health_status,
            "issues": issues,
            "monitoring": status,
            "background_monitor": background_status
        }
    except Exception as e:
        logger.error(f"Error checking monitoring health: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
