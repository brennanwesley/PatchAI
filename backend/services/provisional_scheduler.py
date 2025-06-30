"""
Provisional Access Scheduler
Handles automatic scheduling and verification of provisional access expiry and payment confirmation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading
import time
from services.provisional_access_service import provisional_access_service

logger = logging.getLogger(__name__)

class ProvisionalScheduler:
    """Background scheduler for provisional access verification and cleanup"""
    
    def __init__(self):
        self.logger = logger
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.verification_interval = 3600  # 1 hour in seconds
        self.last_verification = None
        
    def start(self):
        """Start the background scheduler"""
        if self.running:
            self.logger.warning("⚠️ Provisional scheduler already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("🚀 Provisional access scheduler started")
        
    def stop(self):
        """Stop the background scheduler"""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("🛑 Provisional access scheduler stopped")
        
    def _run_scheduler(self):
        """Main scheduler loop"""
        self.logger.info("🔄 Provisional scheduler loop started")
        
        while self.running:
            try:
                # Check if it's time for verification
                if self._should_run_verification():
                    self.logger.info("⏰ Running scheduled provisional access verification")
                    asyncio.run(self._run_verification())
                    self.last_verification = datetime.utcnow()
                    
                # Sleep for 5 minutes before checking again
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"💥 Error in provisional scheduler loop: {str(e)}")
                # Continue running even if one iteration fails
                time.sleep(60)  # Wait 1 minute before retrying
                
    def _should_run_verification(self) -> bool:
        """Determine if verification should run now"""
        if not self.last_verification:
            return True  # First run
            
        time_since_last = datetime.utcnow() - self.last_verification
        return time_since_last.total_seconds() >= self.verification_interval
        
    async def _run_verification(self):
        """Run the verification process"""
        try:
            summary = await provisional_access_service.verify_provisional_payments()
            self.logger.info(f"✅ Scheduled verification complete: {summary}")
            
            # Log detailed results
            verified = summary.get('verified', 0)
            expired = summary.get('expired', 0)
            errors = summary.get('errors', 0)
            
            if verified > 0:
                self.logger.info(f"🎉 {verified} provisional access(es) converted to permanent")
            if expired > 0:
                self.logger.info(f"⏰ {expired} provisional access(es) expired and reverted")
            if errors > 0:
                self.logger.warning(f"⚠️ {errors} error(s) during verification")
                
        except Exception as e:
            self.logger.error(f"💥 Failed to run scheduled verification: {str(e)}")
            
    def force_verification(self):
        """Force an immediate verification (for testing/admin use)"""
        self.logger.info("🔧 Forcing immediate provisional access verification")
        try:
            asyncio.run(self._run_verification())
            self.last_verification = datetime.utcnow()
            self.logger.info("✅ Forced verification completed")
        except Exception as e:
            self.logger.error(f"💥 Forced verification failed: {str(e)}")
            
    def get_status(self) -> dict:
        """Get scheduler status for monitoring"""
        return {
            "running": self.running,
            "last_verification": self.last_verification.isoformat() if self.last_verification else None,
            "verification_interval_hours": self.verification_interval / 3600,
            "next_verification_in_seconds": self._seconds_until_next_verification()
        }
        
    def _seconds_until_next_verification(self) -> Optional[int]:
        """Calculate seconds until next verification"""
        if not self.last_verification:
            return 0  # Will run immediately
            
        time_since_last = datetime.utcnow() - self.last_verification
        remaining = self.verification_interval - time_since_last.total_seconds()
        return max(0, int(remaining))

# Global scheduler instance
provisional_scheduler = ProvisionalScheduler()
