"""
Background Monitoring Service
Runs periodic subscription consistency checks with safe scheduling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from services.subscription_monitor import subscription_monitor

logger = logging.getLogger(__name__)

class BackgroundMonitor:
    """
    Safe background monitoring service with built-in loop prevention
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        # SAFETY: Conservative scheduling to prevent resource exhaustion
        self.CHECK_INTERVAL_HOURS = 6  # Run every 6 hours
        self.MAX_RUNTIME_MINUTES = 30  # Kill if running too long
        
        self.logger.info("🕐 BackgroundMonitor initialized")
        self.logger.info(f"   Check interval: {self.CHECK_INTERVAL_HOURS} hours")
        self.logger.info(f"   Max runtime: {self.MAX_RUNTIME_MINUTES} minutes")
    
    async def start(self):
        """Start background monitoring"""
        if self.is_running:
            self.logger.warning("⚠️ Background monitor already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._monitor_loop())
        self.logger.info("🚀 Background monitor started")
    
    async def stop(self):
        """Stop background monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("🛑 Background monitor stopped")
    
    async def _monitor_loop(self):
        """
        Main monitoring loop with safety checks
        """
        try:
            while self.is_running:
                try:
                    self.logger.info("🔍 Starting scheduled consistency check")
                    start_time = datetime.utcnow()
                    
                    # Run consistency check with timeout
                    try:
                        result = await asyncio.wait_for(
                            subscription_monitor.run_consistency_check(),
                            timeout=self.MAX_RUNTIME_MINUTES * 60
                        )
                        
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        self.logger.info(f"✅ Consistency check completed in {duration:.1f}s: {result}")
                        
                    except asyncio.TimeoutError:
                        self.logger.error(f"⏰ Consistency check timed out after {self.MAX_RUNTIME_MINUTES} minutes")
                    except Exception as e:
                        self.logger.error(f"❌ Consistency check failed: {str(e)}")
                    
                    # SAFETY: Wait for next interval
                    if self.is_running:
                        wait_seconds = self.CHECK_INTERVAL_HOURS * 3600
                        self.logger.info(f"⏸️ Waiting {self.CHECK_INTERVAL_HOURS} hours until next check")
                        await asyncio.sleep(wait_seconds)
                
                except asyncio.CancelledError:
                    self.logger.info("🛑 Monitor loop cancelled")
                    break
                except Exception as e:
                    self.logger.error(f"💥 Unexpected error in monitor loop: {str(e)}")
                    # SAFETY: Wait before retrying to prevent tight error loops
                    if self.is_running:
                        await asyncio.sleep(300)  # 5 minutes
        
        except Exception as e:
            self.logger.error(f"💥 Fatal error in monitor loop: {str(e)}")
        finally:
            self.is_running = False
    
    def get_status(self) -> dict:
        """Get current background monitor status"""
        return {
            "is_running": self.is_running,
            "check_interval_hours": self.CHECK_INTERVAL_HOURS,
            "max_runtime_minutes": self.MAX_RUNTIME_MINUTES,
            "task_status": "running" if self.task and not self.task.done() else "stopped"
        }

# Global instance
background_monitor = BackgroundMonitor()
