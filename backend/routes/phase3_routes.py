"""
Phase 3 Production Hardening Routes
Advanced monitoring, webhook redundancy, and integrity validation endpoints
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from services.webhook_redundancy_service import webhook_redundancy_service
from services.integrity_validation_service import integrity_validation_service
from services.performance_optimization_service import performance_optimization_service
from services.monitoring_dashboard_service import monitoring_dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phase3", tags=["Phase 3 Production Hardening"])

# Request/Response Models
class WebhookRedundancyRequest(BaseModel):
    event_data: Dict[str, Any]
    endpoint_id: Optional[str] = "primary"

class IntegrityValidationRequest(BaseModel):
    validation_type: Optional[str] = "comprehensive"
    force_critical: Optional[bool] = False

class PerformanceOptimizationRequest(BaseModel):
    clear_cache: Optional[bool] = False
    reset_metrics: Optional[bool] = False

# Webhook Redundancy Endpoints
@router.post("/webhooks/redundant")
async def process_redundant_webhook(request: WebhookRedundancyRequest):
    """
    Process webhook with redundancy and failover mechanisms
    """
    try:
        logger.info(f"🔄 [PHASE3] Processing redundant webhook via {request.endpoint_id}")
        
        result = await webhook_redundancy_service.receive_webhook(
            request.event_data, 
            request.endpoint_id
        )
        
        return {
            "success": True,
            "message": "Webhook processed with redundancy",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Redundant webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks/stats")
async def get_webhook_stats():
    """
    Get webhook processing statistics
    """
    try:
        stats = await webhook_redundancy_service.get_webhook_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Webhook stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/recover")
async def recover_failed_webhooks(background_tasks: BackgroundTasks):
    """
    Attempt to recover failed webhooks
    """
    try:
        logger.info("🔄 [PHASE3] Starting webhook recovery process")
        
        # Run recovery in background
        background_tasks.add_task(webhook_redundancy_service.recover_failed_webhooks)
        
        return {
            "success": True,
            "message": "Webhook recovery process started in background"
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Webhook recovery error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Integrity Validation Endpoints
@router.post("/integrity/validate")
async def run_integrity_validation(request: IntegrityValidationRequest):
    """
    Run integrity validation checks
    """
    try:
        logger.info(f"🔍 [PHASE3] Running {request.validation_type} integrity validation")
        
        if request.validation_type == "critical" or request.force_critical:
            result = await integrity_validation_service.run_critical_validation()
        else:
            result = await integrity_validation_service.run_comprehensive_validation()
        
        return {
            "success": True,
            "message": f"Integrity validation completed ({request.validation_type})",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Integrity validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrity/stats")
async def get_integrity_stats():
    """
    Get integrity validation statistics
    """
    try:
        stats = await integrity_validation_service.get_validation_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Integrity stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrity/start-continuous")
async def start_continuous_validation(background_tasks: BackgroundTasks):
    """
    Start continuous integrity validation service
    """
    try:
        logger.info("🔍 [PHASE3] Starting continuous integrity validation")
        
        # Start continuous validation in background
        background_tasks.add_task(integrity_validation_service.start_continuous_validation)
        
        return {
            "success": True,
            "message": "Continuous integrity validation started"
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Continuous validation start error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Performance Optimization Endpoints
@router.get("/performance/stats")
async def get_performance_stats():
    """
    Get performance optimization statistics
    """
    try:
        stats = await performance_optimization_service.get_performance_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Performance stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/alerts")
async def get_performance_alerts(hours: int = Query(24, ge=1, le=168)):
    """
    Get recent performance alerts
    """
    try:
        alerts = await performance_optimization_service.get_performance_alerts(hours)
        return {
            "success": True,
            "alerts": alerts,
            "period": f"{hours}h"
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Performance alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance/optimize")
async def optimize_performance(request: PerformanceOptimizationRequest):
    """
    Apply performance optimizations
    """
    try:
        logger.info("🔧 [PHASE3] Applying performance optimizations")
        
        if request.clear_cache:
            # Clear performance cache
            performance_optimization_service.cache.clear()
            performance_optimization_service.cache_timestamps.clear()
        
        if request.reset_metrics:
            # Clear performance metrics
            performance_optimization_service.clear_performance_data()
        
        return {
            "success": True,
            "message": "Performance optimizations applied",
            "actions": {
                "cache_cleared": request.clear_cache,
                "metrics_reset": request.reset_metrics
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Performance optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring Dashboard Endpoints
@router.get("/dashboard/data")
async def get_dashboard_data(force_refresh: bool = Query(False)):
    """
    Get monitoring dashboard data
    """
    try:
        data = await monitoring_dashboard_service.get_dashboard_data(force_refresh)
        return {
            "success": True,
            "dashboard": data
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Dashboard data error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/alerts")
async def get_real_time_alerts():
    """
    Get real-time alerts for immediate attention
    """
    try:
        alerts = await monitoring_dashboard_service.get_real_time_alerts()
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Real-time alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/trends/{metric}")
async def get_historical_trends(metric: str, hours: int = Query(24, ge=1, le=168)):
    """
    Get historical trends for a specific metric
    """
    try:
        trends = await monitoring_dashboard_service.get_historical_trends(metric, hours)
        return {
            "success": True,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Historical trends error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dashboard/start")
async def start_dashboard_service(background_tasks: BackgroundTasks):
    """
    Start the monitoring dashboard service
    """
    try:
        logger.info("📊 [PHASE3] Starting monitoring dashboard service")
        
        # Start dashboard service in background
        background_tasks.add_task(monitoring_dashboard_service.start_dashboard_service)
        
        return {
            "success": True,
            "message": "Monitoring dashboard service started"
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Dashboard service start error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dashboard/cleanup")
async def cleanup_old_data(background_tasks: BackgroundTasks):
    """
    Cleanup old monitoring data
    """
    try:
        logger.info("🧹 [PHASE3] Starting data cleanup process")
        
        # Run cleanup in background
        background_tasks.add_task(monitoring_dashboard_service.cleanup_old_data)
        
        return {
            "success": True,
            "message": "Data cleanup process started in background"
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Data cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# System Health Endpoint
@router.get("/health")
async def get_system_health():
    """
    Get overall Phase 3 system health
    """
    try:
        # Get health from all services
        webhook_stats = await webhook_redundancy_service.get_webhook_stats()
        integrity_stats = await integrity_validation_service.get_validation_stats()
        performance_stats = await performance_optimization_service.get_performance_stats()
        dashboard_data = await monitoring_dashboard_service.get_dashboard_data()
        
        # Calculate overall health
        health_score = 1.0
        
        # Webhook health
        webhook_success_rate = webhook_stats.get("success_rate", 0)
        if webhook_success_rate < 95:
            health_score -= 0.2
        
        # Integrity health
        integrity_issues = integrity_stats.get("total_issues", 0)
        if integrity_issues > 0:
            health_score -= 0.3
        
        # Performance health
        performance_violations = sum(
            stats.get("violations", 0) 
            for stats in performance_stats.values() 
            if isinstance(stats, dict)
        )
        if performance_violations > 5:
            health_score -= 0.2
        
        health_status = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "critical"
        
        return {
            "success": True,
            "health": {
                "overall_score": round(health_score, 2),
                "status": health_status,
                "components": {
                    "webhook_redundancy": "healthy" if webhook_success_rate >= 95 else "degraded",
                    "integrity_validation": "healthy" if integrity_issues == 0 else "attention_needed",
                    "performance_optimization": "healthy" if performance_violations <= 5 else "degraded",
                    "monitoring_dashboard": "healthy"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] System health error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Emergency Recovery Endpoint
@router.post("/emergency/recover")
async def emergency_recovery(background_tasks: BackgroundTasks):
    """
    Emergency recovery process for all Phase 3 systems
    """
    try:
        logger.warning("🚨 [PHASE3] Starting emergency recovery process")
        
        # Run all recovery processes in background
        background_tasks.add_task(webhook_redundancy_service.recover_failed_webhooks)
        background_tasks.add_task(integrity_validation_service.run_critical_validation)
        background_tasks.add_task(performance_optimization_service.clear_performance_data)
        
        return {
            "success": True,
            "message": "Emergency recovery process initiated",
            "actions": [
                "Webhook recovery started",
                "Critical integrity validation started",
                "Performance data reset"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ [PHASE3] Emergency recovery error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
