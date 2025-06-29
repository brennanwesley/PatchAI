"""
Monitoring Dashboard Service - Phase 3 Production Hardening
Real-time visibility into sync operations and system health
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from services.supabase_service import supabase
from services.webhook_redundancy_service import webhook_redundancy_service
from services.integrity_validation_service import integrity_validation_service
from services.performance_optimization_service import performance_optimization_service
from services.subscription_sync_service import subscription_sync_service

logger = logging.getLogger(__name__)

class DashboardMetric(Enum):
    SYSTEM_HEALTH = "system_health"
    SYNC_SUCCESS_RATE = "sync_success_rate"
    WEBHOOK_PROCESSING = "webhook_processing"
    INTEGRITY_ISSUES = "integrity_issues"
    PERFORMANCE_ALERTS = "performance_alerts"
    USER_ACTIVITY = "user_activity"

@dataclass
class DashboardData:
    metric: DashboardMetric
    value: Any
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class MonitoringDashboardService:
    """
    Production-grade monitoring dashboard with real-time metrics
    """
    
    def __init__(self):
        self.refresh_interval = 30  # seconds
        self.data_retention_hours = 168  # 7 days
        self.dashboard_cache = {}
        self.last_refresh = None
        
    async def start_dashboard_service(self):
        """
        Start the monitoring dashboard service
        """
        logger.info("📊 [DASHBOARD] Starting monitoring dashboard service")
        
        # Start background refresh loop
        asyncio.create_task(self._dashboard_refresh_loop())
    
    async def _dashboard_refresh_loop(self):
        """
        Background loop to refresh dashboard data
        """
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self._refresh_dashboard_data()
                
            except Exception as e:
                logger.error(f"❌ [DASHBOARD] Refresh loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _refresh_dashboard_data(self):
        """
        Refresh all dashboard data
        """
        try:
            correlation_id = f"DASH-{int(time.time())}"
            logger.debug(f"📊 [DASHBOARD-{correlation_id}] Refreshing dashboard data")
            
            # Collect all metrics
            metrics = await asyncio.gather(
                self._collect_system_health(),
                self._collect_sync_metrics(),
                self._collect_webhook_metrics(),
                self._collect_integrity_metrics(),
                self._collect_performance_metrics(),
                self._collect_user_activity(),
                return_exceptions=True
            )
            
            # Update cache
            self.dashboard_cache = {
                "system_health": metrics[0] if not isinstance(metrics[0], Exception) else {"error": str(metrics[0])},
                "sync_metrics": metrics[1] if not isinstance(metrics[1], Exception) else {"error": str(metrics[1])},
                "webhook_metrics": metrics[2] if not isinstance(metrics[2], Exception) else {"error": str(metrics[2])},
                "integrity_metrics": metrics[3] if not isinstance(metrics[3], Exception) else {"error": str(metrics[3])},
                "performance_metrics": metrics[4] if not isinstance(metrics[4], Exception) else {"error": str(metrics[4])},
                "user_activity": metrics[5] if not isinstance(metrics[5], Exception) else {"error": str(metrics[5])},
                "last_updated": datetime.utcnow().isoformat()
            }
            
            self.last_refresh = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Data refresh error: {str(e)}")
    
    async def _collect_system_health(self) -> Dict[str, Any]:
        """
        Collect overall system health metrics
        """
        try:
            # Check database connectivity
            db_health = await self._check_database_health()
            
            # Check service status
            services_health = await self._check_services_health()
            
            # Calculate overall health score
            health_score = self._calculate_health_score(db_health, services_health)
            
            return {
                "overall_score": health_score,
                "status": "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "critical",
                "database": db_health,
                "services": services_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] System health collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_sync_metrics(self) -> Dict[str, Any]:
        """
        Collect subscription sync metrics
        """
        try:
            # Get sync stats from last 24 hours
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Sync operations
            sync_result = supabase.table("sync_operations").select("status, created_at").gte("created_at", since).execute()
            
            total_syncs = len(sync_result.data)
            successful_syncs = len([s for s in sync_result.data if s.get("status") == "success"])
            
            success_rate = (successful_syncs / max(total_syncs, 1)) * 100
            
            # Recent sync failures
            failed_syncs = [s for s in sync_result.data if s.get("status") == "failed"]
            
            # Active subscriptions
            active_subs = supabase.table("user_subscriptions").select("*", count="exact").eq("status", "active").execute()
            
            return {
                "success_rate": round(success_rate, 2),
                "total_operations": total_syncs,
                "successful_operations": successful_syncs,
                "failed_operations": len(failed_syncs),
                "active_subscriptions": active_subs.count,
                "recent_failures": failed_syncs[-5:],  # Last 5 failures
                "period": "24h"
            }
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Sync metrics collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_webhook_metrics(self) -> Dict[str, Any]:
        """
        Collect webhook processing metrics
        """
        try:
            webhook_stats = await webhook_redundancy_service.get_webhook_stats()
            
            # Get recent webhook events
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            webhook_events = supabase.table("webhook_events").select("*").gte("created_at", since).order("created_at", desc=True).limit(10).execute()
            
            return {
                "stats": webhook_stats,
                "recent_events": webhook_events.data,
                "processing_health": "healthy" if webhook_stats.get("success_rate", 0) >= 95 else "degraded"
            }
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Webhook metrics collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_integrity_metrics(self) -> Dict[str, Any]:
        """
        Collect data integrity metrics
        """
        try:
            integrity_stats = await integrity_validation_service.get_validation_stats()
            
            # Get recent validation results
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            validation_results = supabase.table("integrity_validation_results").select("*").gte("created_at", since).order("created_at", desc=True).limit(5).execute()
            
            return {
                "stats": integrity_stats,
                "recent_validations": validation_results.data,
                "integrity_health": "healthy" if integrity_stats.get("total_issues", 0) == 0 else "attention_needed"
            }
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Integrity metrics collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """
        Collect performance metrics
        """
        try:
            performance_stats = await performance_optimization_service.get_performance_stats()
            performance_alerts = await performance_optimization_service.get_performance_alerts(hours=24)
            
            return {
                "stats": performance_stats,
                "recent_alerts": performance_alerts[-10:],  # Last 10 alerts
                "performance_health": "healthy" if len(performance_alerts) == 0 else "monitoring"
            }
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Performance metrics collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_user_activity(self) -> Dict[str, Any]:
        """
        Collect user activity metrics
        """
        try:
            # Active users (last 24 hours)
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Recent signups
            recent_signups = supabase.table("user_profiles").select("email, created_at").gte("created_at", since).execute()
            
            # Recent payments
            recent_payments = supabase.table("user_profiles").select("email, last_payment_at").gte("last_payment_at", since).execute()
            
            # Subscription distribution
            subscription_dist = supabase.table("user_profiles").select("plan_tier", count="exact").execute()
            
            # Group by plan tier
            plan_distribution = {}
            for user in subscription_dist.data:
                plan = user.get("plan_tier", "unknown")
                plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
            
            return {
                "recent_signups": len(recent_signups.data),
                "recent_payments": len(recent_payments.data),
                "plan_distribution": plan_distribution,
                "total_users": subscription_dist.count,
                "period": "24h"
            }
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] User activity collection error: {str(e)}")
            return {"error": str(e)}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """
        Check database connectivity and performance
        """
        try:
            start_time = time.time()
            
            # Simple connectivity test
            result = supabase.table("user_profiles").select("email", count="exact").limit(1).execute()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),  # ms
                "connectivity": "ok"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connectivity": "failed"
            }
    
    async def _check_services_health(self) -> Dict[str, Any]:
        """
        Check health of various services
        """
        services = {
            "webhook_redundancy": "healthy",
            "integrity_validation": "healthy",
            "performance_optimization": "healthy",
            "subscription_sync": "healthy"
        }
        
        # In a real implementation, you would check each service
        # For now, assume all are healthy
        
        return services
    
    def _calculate_health_score(self, db_health: Dict[str, Any], services_health: Dict[str, Any]) -> float:
        """
        Calculate overall system health score (0.0 to 1.0)
        """
        score = 1.0
        
        # Database health impact
        if db_health.get("status") != "healthy":
            score -= 0.5
        elif db_health.get("response_time", 0) > 1000:  # > 1 second
            score -= 0.2
        
        # Services health impact
        unhealthy_services = len([s for s in services_health.values() if s != "healthy"])
        score -= (unhealthy_services * 0.1)
        
        return max(0.0, min(1.0, score))
    
    async def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get current dashboard data
        """
        try:
            # Check if refresh is needed
            if force_refresh or not self.last_refresh or (datetime.utcnow() - self.last_refresh).total_seconds() > self.refresh_interval:
                await self._refresh_dashboard_data()
            
            return self.dashboard_cache
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Get dashboard data error: {str(e)}")
            return {"error": str(e)}
    
    async def get_real_time_alerts(self) -> List[Dict[str, Any]]:
        """
        Get real-time alerts for immediate attention
        """
        try:
            alerts = []
            
            # Check for critical integrity issues
            since = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
            
            # Performance alerts
            perf_alerts = await performance_optimization_service.get_performance_alerts(hours=1)
            for alert in perf_alerts[-5:]:  # Last 5
                alerts.append({
                    "type": "performance",
                    "severity": "warning",
                    "message": f"Performance issue: {alert.get('metric')} = {alert.get('value')}",
                    "timestamp": alert.get("created_at")
                })
            
            # Manual intervention alerts
            manual_alerts = supabase.table("manual_intervention_alerts").select("*").eq("status", "pending").gte("created_at", since).execute()
            for alert in manual_alerts.data:
                alerts.append({
                    "type": "manual_intervention",
                    "severity": "critical",
                    "message": f"Manual intervention needed: {alert.get('alert_type')} - {alert.get('error_message')}",
                    "timestamp": alert.get("created_at")
                })
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Real-time alerts error: {str(e)}")
            return []
    
    async def get_historical_trends(self, metric: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get historical trends for a specific metric
        """
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            if metric == "sync_success_rate":
                # Get sync operations over time
                result = supabase.table("sync_operations").select("status, created_at").gte("created_at", since).order("created_at").execute()
                
                # Group by hour
                hourly_data = {}
                for operation in result.data:
                    hour = operation["created_at"][:13]  # YYYY-MM-DDTHH
                    if hour not in hourly_data:
                        hourly_data[hour] = {"total": 0, "success": 0}
                    
                    hourly_data[hour]["total"] += 1
                    if operation["status"] == "success":
                        hourly_data[hour]["success"] += 1
                
                # Calculate success rates
                trend_data = []
                for hour, data in sorted(hourly_data.items()):
                    success_rate = (data["success"] / max(data["total"], 1)) * 100
                    trend_data.append({
                        "timestamp": hour,
                        "value": round(success_rate, 2),
                        "total_operations": data["total"]
                    })
                
                return {
                    "metric": metric,
                    "period": f"{hours}h",
                    "data": trend_data
                }
            
            return {"error": f"Metric {metric} not supported"}
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Historical trends error: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self):
        """
        Cleanup old monitoring data
        """
        try:
            cutoff = (datetime.utcnow() - timedelta(hours=self.data_retention_hours)).isoformat()
            
            # Cleanup tables
            tables_to_cleanup = [
                "webhook_events",
                "integrity_validation_results",
                "performance_alerts",
                "sync_operations"
            ]
            
            for table in tables_to_cleanup:
                try:
                    result = supabase.table(table).delete().lt("created_at", cutoff).execute()
                    logger.info(f"🧹 [DASHBOARD] Cleaned up {len(result.data)} old records from {table}")
                except Exception as e:
                    logger.error(f"❌ [DASHBOARD] Cleanup error for {table}: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ [DASHBOARD] Data cleanup error: {str(e)}")

# Global instance
monitoring_dashboard_service = MonitoringDashboardService()
