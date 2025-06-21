"""
System monitoring and health check utilities
"""

import os
import time
import logging
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Application start time for uptime calculation
APP_START_TIME = time.time()


def get_system_metrics() -> Dict[str, Any]:
    """Get current system resource metrics"""
    if not PSUTIL_AVAILABLE:
        return {
            "cpu_percent": "unavailable",
            "memory_percent": "unavailable", 
            "disk_percent": "unavailable",
            "note": "psutil not available"
        }
    
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {
            "cpu_percent": "error",
            "memory_percent": "error",
            "disk_percent": "error",
            "error": str(e)
        }


def check_service_health(openai_client, supabase_client, rate_limiter) -> Dict[str, str]:
    """Check health of critical services"""
    services = {}
    
    # Check OpenAI client
    try:
        if openai_client and hasattr(openai_client, 'api_key'):
            services["openai"] = "healthy"
        else:
            services["openai"] = "not_initialized"
    except Exception as e:
        services["openai"] = f"error: {str(e)}"
    
    # Check Supabase client
    try:
        if supabase_client and hasattr(supabase_client, 'auth'):
            services["supabase"] = "healthy"
        else:
            services["supabase"] = "not_initialized"
    except Exception as e:
        services["supabase"] = f"error: {str(e)}"
    
    # Check Rate Limiter
    try:
        if rate_limiter and hasattr(rate_limiter, 'check_user_limit'):
            services["rate_limiter"] = "healthy"
        else:
            services["rate_limiter"] = "not_initialized"
    except Exception as e:
        services["rate_limiter"] = f"error: {str(e)}"
    
    return services


def get_health_status(openai_client, supabase_client, rate_limiter, structured_logger) -> Dict[str, Any]:
    """Get comprehensive health status"""
    current_time = time.time()
    uptime_seconds = int(current_time - APP_START_TIME)
    
    # Get system metrics
    system_metrics = get_system_metrics()
    
    # Get service health
    services = check_service_health(openai_client, supabase_client, rate_limiter)
    
    # Get application metrics
    app_metrics = structured_logger.get_metrics() if structured_logger else {}
    
    # Determine overall status
    status = "healthy"
    warnings = []
    
    # Check for degraded conditions
    if PSUTIL_AVAILABLE and isinstance(system_metrics.get("cpu_percent"), (int, float)):
        if system_metrics["cpu_percent"] > 90:
            status = "degraded"
            warnings.append("High CPU usage")
        if system_metrics["memory_percent"] > 90:
            status = "degraded"
            warnings.append("High memory usage")
        if system_metrics["disk_percent"] > 95:
            status = "degraded"
            warnings.append("High disk usage")
    
    # Check for service issues
    for service, health in services.items():
        if health != "healthy":
            if "error" in health or "not_initialized" in health:
                status = "degraded"
                warnings.append(f"{service} service issue: {health}")
    
    return {
        "status": status,
        "timestamp": current_time,
        "uptime_seconds": uptime_seconds,
        "system": system_metrics,
        "services": services,
        "application": app_metrics,
        "warnings": warnings
    }
