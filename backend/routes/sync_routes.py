"""
Enhanced Sync Routes - Phase 2/3 Implementation
Provides robust API endpoints for subscription synchronization
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from services.subscription_sync_service import subscription_sync_service
from core.auth import get_current_user
from models.schemas import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/subscription/{email}")
async def sync_user_subscription(
    email: str,
    current_user: User = Depends(get_current_user)
):
    """
    Enhanced subscription sync endpoint with comprehensive error handling
    """
    try:
        logger.info(f"🔄 Manual sync requested for {email} by {current_user.email}")
        
        # Perform comprehensive sync
        result = await subscription_sync_service.comprehensive_user_sync(email)
        
        if result["success"]:
            logger.info(f"✅ Manual sync successful for {email}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result.get("message", "Subscription synchronized successfully"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "synced_subscriptions": result.get("synced_subscriptions", 0)
                }
            )
        else:
            logger.warning(f"⚠️ Manual sync failed for {email}: {result.get('error', 'Unknown error')}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result.get("error", "Sync failed"),
                    "error_code": result.get("error_code", "SYNC_FAILED"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Manual sync exception for {email}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error during sync",
                "error_code": "INTERNAL_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.post("/proactive-check")
async def run_proactive_sync_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Run proactive sync check to find and fix sync issues
    """
    try:
        logger.info(f"🔍 Proactive sync check requested by {current_user.email}")
        
        # Run in background to avoid timeout
        background_tasks.add_task(subscription_sync_service.proactive_sync_check)
        
        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "message": "Proactive sync check started in background",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Proactive sync check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to start proactive sync check",
                "error_code": "PROACTIVE_CHECK_FAILED",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/health")
async def sync_service_health():
    """
    Health check endpoint for sync service
    """
    try:
        health_result = await subscription_sync_service.health_check()
        
        status_code = 200 if health_result["success"] else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_result
        )
        
    except Exception as e:
        logger.error(f"❌ Sync service health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/status")
async def sync_service_status(current_user: User = Depends(get_current_user)):
    """
    Get detailed sync service status and statistics
    """
    try:
        # Get basic health
        health = await subscription_sync_service.health_check()
        
        # Add additional status info
        status_info = {
            "service_health": health,
            "service_version": "2.0.0",
            "features": [
                "comprehensive_user_sync",
                "proactive_sync_check", 
                "webhook_failure_recovery",
                "real_time_monitoring"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(
            status_code=200,
            content=status_info
        )
        
    except Exception as e:
        logger.error(f"❌ Sync service status failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
