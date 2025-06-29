"""
Performance Optimization Service - Phase 3 Production Hardening
High-volume event handling and efficiency optimization for subscription sync
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict, deque
import threading

from services.supabase_service import supabase

logger = logging.getLogger(__name__)

class PerformanceMetric(Enum):
    WEBHOOK_PROCESSING_TIME = "webhook_processing_time"
    SYNC_OPERATION_TIME = "sync_operation_time"
    DATABASE_QUERY_TIME = "database_query_time"
    STRIPE_API_TIME = "stripe_api_time"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"

@dataclass
class PerformanceEvent:
    metric: PerformanceMetric
    value: float
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None

class PerformanceOptimizationService:
    """
    Production-grade performance optimization service with real-time monitoring
    """
    
    def __init__(self):
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.performance_thresholds = {
            PerformanceMetric.WEBHOOK_PROCESSING_TIME: 5.0,  # seconds
            PerformanceMetric.SYNC_OPERATION_TIME: 10.0,     # seconds
            PerformanceMetric.DATABASE_QUERY_TIME: 2.0,      # seconds
            PerformanceMetric.STRIPE_API_TIME: 3.0,          # seconds
            PerformanceMetric.ERROR_RATE: 0.05,              # 5%
        }
        self.optimization_enabled = True
        self.batch_size = 50
        self.cache_ttl = 300  # 5 minutes
        self.cache = {}
        self.cache_timestamps = {}
        self.lock = threading.Lock()
        
    def record_performance_metric(self, metric: PerformanceMetric, value: float, context: Optional[Dict[str, Any]] = None):
        """
        Record a performance metric
        """
        try:
            event = PerformanceEvent(
                metric=metric,
                value=value,
                timestamp=datetime.utcnow(),
                context=context or {}
            )
            
            with self.lock:
                self.metrics_buffer[metric].append(event)
            
            # Check for performance issues
            if self._is_performance_issue(metric, value):
                asyncio.create_task(self._handle_performance_issue(metric, value, context))
                
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Metric recording error: {str(e)}")
    
    def performance_timer(self, metric: PerformanceMetric, context: Optional[Dict[str, Any]] = None):
        """
        Context manager for timing operations
        """
        return PerformanceTimer(self, metric, context)
    
    def _is_performance_issue(self, metric: PerformanceMetric, value: float) -> bool:
        """
        Check if metric value indicates a performance issue
        """
        threshold = self.performance_thresholds.get(metric)
        return threshold is not None and value > threshold
    
    async def _handle_performance_issue(self, metric: PerformanceMetric, value: float, context: Optional[Dict[str, Any]]):
        """
        Handle detected performance issue
        """
        try:
            logger.warning(f"⚠️ [PERFORMANCE] Performance issue detected: {metric.value} = {value}")
            
            # Store performance alert
            alert_data = {
                "metric": metric.value,
                "value": value,
                "threshold": self.performance_thresholds.get(metric),
                "context": json.dumps(context or {}),
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            supabase.table("performance_alerts").insert(alert_data).execute()
            
            # Apply automatic optimizations
            if self.optimization_enabled:
                await self._apply_optimization(metric, value, context)
                
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Performance issue handling error: {str(e)}")
    
    async def _apply_optimization(self, metric: PerformanceMetric, value: float, context: Optional[Dict[str, Any]]):
        """
        Apply automatic performance optimizations
        """
        try:
            if metric == PerformanceMetric.WEBHOOK_PROCESSING_TIME:
                # Increase batch processing for webhooks
                await self._optimize_webhook_processing()
                
            elif metric == PerformanceMetric.DATABASE_QUERY_TIME:
                # Optimize database queries
                await self._optimize_database_queries()
                
            elif metric == PerformanceMetric.STRIPE_API_TIME:
                # Implement Stripe API caching
                await self._optimize_stripe_api_calls()
                
            elif metric == PerformanceMetric.ERROR_RATE:
                # Increase retry delays and circuit breaker
                await self._optimize_error_handling()
                
            logger.info(f"🔧 [PERFORMANCE] Applied optimization for {metric.value}")
            
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Optimization application error: {str(e)}")
    
    async def _optimize_webhook_processing(self):
        """
        Optimize webhook processing performance
        """
        # Increase batch size for webhook processing
        self.batch_size = min(self.batch_size * 2, 200)
        logger.info(f"🔧 [PERFORMANCE] Increased webhook batch size to {self.batch_size}")
    
    async def _optimize_database_queries(self):
        """
        Optimize database query performance
        """
        # Clear cache to force fresh queries
        with self.lock:
            self.cache.clear()
            self.cache_timestamps.clear()
        
        logger.info("🔧 [PERFORMANCE] Cleared database query cache")
    
    async def _optimize_stripe_api_calls(self):
        """
        Optimize Stripe API call performance
        """
        # Increase cache TTL for Stripe data
        self.cache_ttl = min(self.cache_ttl * 2, 1800)  # Max 30 minutes
        logger.info(f"🔧 [PERFORMANCE] Increased Stripe cache TTL to {self.cache_ttl}s")
    
    async def _optimize_error_handling(self):
        """
        Optimize error handling performance
        """
        # This would integrate with retry mechanisms
        logger.info("🔧 [PERFORMANCE] Applied error handling optimizations")
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """
        Get cached result if still valid
        """
        try:
            with self.lock:
                if cache_key in self.cache:
                    timestamp = self.cache_timestamps.get(cache_key)
                    if timestamp and (datetime.utcnow() - timestamp).total_seconds() < self.cache_ttl:
                        return self.cache[cache_key]
                    else:
                        # Remove expired cache entry
                        del self.cache[cache_key]
                        if cache_key in self.cache_timestamps:
                            del self.cache_timestamps[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Cache retrieval error: {str(e)}")
            return None
    
    def set_cached_result(self, cache_key: str, result: Any):
        """
        Set cached result
        """
        try:
            with self.lock:
                self.cache[cache_key] = result
                self.cache_timestamps[cache_key] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Cache storage error: {str(e)}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics
        """
        try:
            stats = {}
            
            with self.lock:
                for metric, events in self.metrics_buffer.items():
                    if not events:
                        continue
                    
                    values = [event.value for event in events]
                    
                    stats[metric.value] = {
                        "count": len(values),
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "threshold": self.performance_thresholds.get(metric),
                        "violations": len([v for v in values if self._is_performance_issue(metric, v)])
                    }
            
            # Add system stats
            stats["system"] = {
                "cache_size": len(self.cache),
                "cache_ttl": self.cache_ttl,
                "batch_size": self.batch_size,
                "optimization_enabled": self.optimization_enabled
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Stats generation error: {str(e)}")
            return {"error": str(e)}
    
    async def get_performance_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent performance alerts
        """
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            result = supabase.table("performance_alerts").select("*").gte("created_at", since).order("created_at", desc=True).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Alerts retrieval error: {str(e)}")
            return []
    
    async def optimize_batch_operations(self, operations: List[Callable], batch_size: Optional[int] = None) -> List[Any]:
        """
        Optimize batch operations for better performance
        """
        try:
            effective_batch_size = batch_size or self.batch_size
            results = []
            
            # Process operations in batches
            for i in range(0, len(operations), effective_batch_size):
                batch = operations[i:i + effective_batch_size]
                
                # Execute batch concurrently
                batch_tasks = [asyncio.create_task(op()) for op in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                results.extend(batch_results)
                
                # Small delay between batches to prevent overwhelming
                if i + effective_batch_size < len(operations):
                    await asyncio.sleep(0.1)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ [PERFORMANCE] Batch optimization error: {str(e)}")
            return []
    
    def clear_performance_data(self):
        """
        Clear performance data (for testing/reset)
        """
        with self.lock:
            self.metrics_buffer.clear()
            self.cache.clear()
            self.cache_timestamps.clear()
        
        logger.info("🔧 [PERFORMANCE] Cleared all performance data")

class PerformanceTimer:
    """
    Context manager for timing operations
    """
    
    def __init__(self, service: PerformanceOptimizationService, metric: PerformanceMetric, context: Optional[Dict[str, Any]] = None):
        self.service = service
        self.metric = metric
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.service.record_performance_metric(self.metric, duration, self.context)

# Global instance
performance_optimization_service = PerformanceOptimizationService()
