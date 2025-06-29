"""
Automated Integrity Validation Service - Phase 3 Production Hardening
Real-time data consistency checks and automated correction mechanisms
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from services.supabase_service import supabase
from services.subscription_sync_service import subscription_sync_service
from core.stripe_config import stripe

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    issue_id: str
    user_email: str
    issue_type: str
    severity: ValidationSeverity
    description: str
    stripe_data: Optional[Dict[str, Any]] = None
    db_data: Optional[Dict[str, Any]] = None
    auto_correctable: bool = False
    corrected: bool = False
    created_at: Optional[datetime] = None

class IntegrityValidationService:
    """
    Production-grade integrity validation service with automated correction
    """
    
    def __init__(self):
        self.validation_interval = 300  # 5 minutes
        self.critical_validation_interval = 60  # 1 minute for critical checks
        self.max_auto_corrections_per_hour = 10
        self.correction_count = 0
        self.last_correction_reset = datetime.utcnow()
        
    async def start_continuous_validation(self):
        """
        Start continuous integrity validation in background
        """
        logger.info("🔍 [INTEGRITY] Starting continuous validation service")
        
        # Start both regular and critical validation loops
        asyncio.create_task(self._regular_validation_loop())
        asyncio.create_task(self._critical_validation_loop())
    
    async def _regular_validation_loop(self):
        """
        Regular validation loop for comprehensive checks
        """
        while True:
            try:
                await asyncio.sleep(self.validation_interval)
                await self.run_comprehensive_validation()
                
            except Exception as e:
                logger.error(f"❌ [INTEGRITY] Regular validation loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _critical_validation_loop(self):
        """
        Critical validation loop for urgent checks
        """
        while True:
            try:
                await asyncio.sleep(self.critical_validation_interval)
                await self.run_critical_validation()
                
            except Exception as e:
                logger.error(f"❌ [INTEGRITY] Critical validation loop error: {str(e)}")
                await asyncio.sleep(30)  # Shorter wait for critical checks
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive integrity validation
        """
        try:
            correlation_id = f"VALIDATION-{int(time.time())}"
            logger.info(f"🔍 [INTEGRITY-{correlation_id}] Starting comprehensive validation")
            
            issues = []
            
            # 1. Subscription Status Validation
            subscription_issues = await self._validate_subscription_status()
            issues.extend(subscription_issues)
            
            # 2. Payment Record Validation
            payment_issues = await self._validate_payment_records()
            issues.extend(payment_issues)
            
            # 3. Stripe-DB Consistency Validation
            consistency_issues = await self._validate_stripe_db_consistency()
            issues.extend(consistency_issues)
            
            # 4. User Profile Validation
            profile_issues = await self._validate_user_profiles()
            issues.extend(profile_issues)
            
            # Store validation results
            await self._store_validation_results(issues, correlation_id)
            
            # Auto-correct issues where possible
            corrections = await self._auto_correct_issues(issues, correlation_id)
            
            result = {
                "success": True,
                "correlation_id": correlation_id,
                "total_issues": len(issues),
                "issues_by_severity": self._group_issues_by_severity(issues),
                "auto_corrections": corrections,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if issues:
                logger.warning(f"⚠️ [INTEGRITY-{correlation_id}] Found {len(issues)} integrity issues")
            else:
                logger.info(f"✅ [INTEGRITY-{correlation_id}] No integrity issues found")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Comprehensive validation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_critical_validation(self) -> Dict[str, Any]:
        """
        Run critical validation for urgent issues
        """
        try:
            correlation_id = f"CRITICAL-{int(time.time())}"
            
            issues = []
            
            # Check for users with recent payments but inactive status
            recent_payment_issues = await self._validate_recent_payments()
            issues.extend(recent_payment_issues)
            
            # Check for subscription mismatches
            critical_mismatches = await self._validate_critical_mismatches()
            issues.extend(critical_mismatches)
            
            if issues:
                logger.warning(f"🚨 [INTEGRITY-{correlation_id}] Found {len(issues)} critical issues")
                
                # Auto-correct critical issues immediately
                corrections = await self._auto_correct_issues(issues, correlation_id, force_critical=True)
                
                return {
                    "success": True,
                    "correlation_id": correlation_id,
                    "critical_issues": len(issues),
                    "auto_corrections": corrections
                }
            
            return {"success": True, "critical_issues": 0}
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Critical validation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _validate_subscription_status(self) -> List[ValidationIssue]:
        """
        Validate subscription status consistency
        """
        issues = []
        
        try:
            # Get all user profiles with subscription data
            result = supabase.table("user_profiles").select("*").execute()
            
            for user in result.data:
                user_email = user.get("email")
                subscription_status = user.get("subscription_status")
                plan_tier = user.get("plan_tier")
                
                if not user_email:
                    continue
                
                # Check for inconsistent status/tier combinations
                if subscription_status == "active" and plan_tier == "free":
                    issues.append(ValidationIssue(
                        issue_id=f"status_tier_mismatch_{user_email}",
                        user_email=user_email,
                        issue_type="status_tier_mismatch",
                        severity=ValidationSeverity.ERROR,
                        description=f"User has active subscription but free plan tier",
                        db_data={"subscription_status": subscription_status, "plan_tier": plan_tier},
                        auto_correctable=True
                    ))
                
                elif subscription_status == "inactive" and plan_tier in ["standard", "premium"]:
                    issues.append(ValidationIssue(
                        issue_id=f"inactive_paid_tier_{user_email}",
                        user_email=user_email,
                        issue_type="inactive_paid_tier",
                        severity=ValidationSeverity.WARNING,
                        description=f"User has inactive subscription but paid plan tier",
                        db_data={"subscription_status": subscription_status, "plan_tier": plan_tier},
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Subscription status validation error: {str(e)}")
        
        return issues
    
    async def _validate_payment_records(self) -> List[ValidationIssue]:
        """
        Validate payment record consistency
        """
        issues = []
        
        try:
            # Get users with recent payments but no subscription records
            recent_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            profiles_result = supabase.table("user_profiles").select("email, last_payment_at, subscription_status").gte("last_payment_at", recent_date).execute()
            
            for user in profiles_result.data:
                user_email = user.get("email")
                last_payment_at = user.get("last_payment_at")
                subscription_status = user.get("subscription_status")
                
                if not user_email or not last_payment_at:
                    continue
                
                # Check if user has subscription record
                sub_result = supabase.table("user_subscriptions").select("*").eq("user_email", user_email).execute()
                
                if not sub_result.data and subscription_status == "active":
                    issues.append(ValidationIssue(
                        issue_id=f"missing_subscription_record_{user_email}",
                        user_email=user_email,
                        issue_type="missing_subscription_record",
                        severity=ValidationSeverity.CRITICAL,
                        description=f"User has recent payment and active status but no subscription record",
                        db_data={"last_payment_at": last_payment_at, "subscription_status": subscription_status},
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Payment records validation error: {str(e)}")
        
        return issues
    
    async def _validate_stripe_db_consistency(self) -> List[ValidationIssue]:
        """
        Validate consistency between Stripe and database
        """
        issues = []
        
        try:
            # Get active subscriptions from database
            result = supabase.table("user_subscriptions").select("*").eq("status", "active").execute()
            
            for subscription in result.data:
                user_email = subscription.get("user_email")
                stripe_subscription_id = subscription.get("stripe_subscription_id")
                
                if not stripe_subscription_id:
                    continue
                
                try:
                    # Check Stripe subscription status
                    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                    
                    if stripe_sub.status != "active":
                        issues.append(ValidationIssue(
                            issue_id=f"stripe_db_status_mismatch_{user_email}",
                            user_email=user_email,
                            issue_type="stripe_db_status_mismatch",
                            severity=ValidationSeverity.ERROR,
                            description=f"DB shows active subscription but Stripe shows {stripe_sub.status}",
                            stripe_data={"status": stripe_sub.status},
                            db_data={"status": "active"},
                            auto_correctable=True
                        ))
                
                except Exception as stripe_error:
                    if "No such subscription" in str(stripe_error):
                        issues.append(ValidationIssue(
                            issue_id=f"orphaned_subscription_{user_email}",
                            user_email=user_email,
                            issue_type="orphaned_subscription",
                            severity=ValidationSeverity.ERROR,
                            description=f"DB subscription references non-existent Stripe subscription",
                            db_data={"stripe_subscription_id": stripe_subscription_id},
                            auto_correctable=True
                        ))
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Stripe-DB consistency validation error: {str(e)}")
        
        return issues
    
    async def _validate_user_profiles(self) -> List[ValidationIssue]:
        """
        Validate user profile data integrity
        """
        issues = []
        
        try:
            # Get all user profiles
            result = supabase.table("user_profiles").select("*").execute()
            
            for user in result.data:
                user_email = user.get("email")
                
                if not user_email:
                    issues.append(ValidationIssue(
                        issue_id=f"missing_email_{user.get('id', 'unknown')}",
                        user_email="unknown",
                        issue_type="missing_email",
                        severity=ValidationSeverity.CRITICAL,
                        description="User profile missing email address",
                        db_data=user,
                        auto_correctable=False
                    ))
                    continue
                
                # Check for missing required fields
                if not user.get("subscription_status"):
                    issues.append(ValidationIssue(
                        issue_id=f"missing_subscription_status_{user_email}",
                        user_email=user_email,
                        issue_type="missing_subscription_status",
                        severity=ValidationSeverity.WARNING,
                        description="User profile missing subscription status",
                        db_data=user,
                        auto_correctable=True
                    ))
                
                if not user.get("plan_tier"):
                    issues.append(ValidationIssue(
                        issue_id=f"missing_plan_tier_{user_email}",
                        user_email=user_email,
                        issue_type="missing_plan_tier",
                        severity=ValidationSeverity.WARNING,
                        description="User profile missing plan tier",
                        db_data=user,
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] User profiles validation error: {str(e)}")
        
        return issues
    
    async def _validate_recent_payments(self) -> List[ValidationIssue]:
        """
        Validate users with recent payments for critical issues
        """
        issues = []
        
        try:
            # Check last 30 minutes for critical issues
            recent_date = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
            
            result = supabase.table("user_profiles").select("*").gte("last_payment_at", recent_date).execute()
            
            for user in result.data:
                user_email = user.get("email")
                subscription_status = user.get("subscription_status")
                
                if subscription_status != "active":
                    issues.append(ValidationIssue(
                        issue_id=f"recent_payment_inactive_{user_email}",
                        user_email=user_email,
                        issue_type="recent_payment_inactive",
                        severity=ValidationSeverity.CRITICAL,
                        description="User has recent payment but inactive subscription status",
                        db_data=user,
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Recent payments validation error: {str(e)}")
        
        return issues
    
    async def _validate_critical_mismatches(self) -> List[ValidationIssue]:
        """
        Validate critical data mismatches
        """
        issues = []
        
        try:
            # Check for users with payments but no subscription records
            result = supabase.table("user_profiles").select("email, subscription_status, last_payment_at").eq("subscription_status", "active").execute()
            
            for user in result.data:
                user_email = user.get("email")
                
                # Check if subscription record exists
                sub_result = supabase.table("user_subscriptions").select("*").eq("user_email", user_email).execute()
                
                if not sub_result.data:
                    issues.append(ValidationIssue(
                        issue_id=f"active_no_subscription_{user_email}",
                        user_email=user_email,
                        issue_type="active_no_subscription",
                        severity=ValidationSeverity.CRITICAL,
                        description="User marked as active but has no subscription record",
                        db_data=user,
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Critical mismatches validation error: {str(e)}")
        
        return issues
    
    async def _auto_correct_issues(self, issues: List[ValidationIssue], correlation_id: str, force_critical: bool = False) -> Dict[str, Any]:
        """
        Automatically correct issues where possible
        """
        corrections = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        try:
            # Check rate limiting
            if not force_critical and not self._can_auto_correct():
                logger.warning(f"⚠️ [INTEGRITY-{correlation_id}] Auto-correction rate limit reached")
                corrections["skipped"] = len([i for i in issues if i.auto_correctable])
                return corrections
            
            for issue in issues:
                if not issue.auto_correctable:
                    continue
                
                if not force_critical and issue.severity == ValidationSeverity.INFO:
                    corrections["skipped"] += 1
                    continue
                
                corrections["attempted"] += 1
                
                try:
                    success = await self._correct_issue(issue, correlation_id)
                    
                    if success:
                        corrections["successful"] += 1
                        corrections["details"].append({
                            "issue_id": issue.issue_id,
                            "user_email": issue.user_email,
                            "issue_type": issue.issue_type,
                            "status": "corrected"
                        })
                        
                        # Update correction count
                        self.correction_count += 1
                        
                    else:
                        corrections["failed"] += 1
                        corrections["details"].append({
                            "issue_id": issue.issue_id,
                            "user_email": issue.user_email,
                            "issue_type": issue.issue_type,
                            "status": "failed"
                        })
                
                except Exception as e:
                    logger.error(f"❌ [INTEGRITY-{correlation_id}] Auto-correction error for {issue.issue_id}: {str(e)}")
                    corrections["failed"] += 1
            
            if corrections["successful"] > 0:
                logger.info(f"✅ [INTEGRITY-{correlation_id}] Auto-corrected {corrections['successful']} issues")
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Auto-correction process error: {str(e)}")
        
        return corrections
    
    async def _correct_issue(self, issue: ValidationIssue, correlation_id: str) -> bool:
        """
        Correct a specific integrity issue
        """
        try:
            logger.info(f"🔧 [INTEGRITY-{correlation_id}] Correcting {issue.issue_type} for {issue.user_email}")
            
            if issue.issue_type == "missing_subscription_record":
                # Sync subscription from Stripe
                result = await subscription_sync_service.sync_user_subscription(issue.user_email)
                return result.get("success", False)
            
            elif issue.issue_type == "status_tier_mismatch":
                # Fix status/tier mismatch
                if issue.db_data.get("subscription_status") == "active":
                    # Update plan tier to standard
                    supabase.table("user_profiles").update({"plan_tier": "standard"}).eq("email", issue.user_email).execute()
                    return True
            
            elif issue.issue_type == "inactive_paid_tier":
                # Check if should be active
                sub_result = supabase.table("user_subscriptions").select("*").eq("user_email", issue.user_email).eq("status", "active").execute()
                if sub_result.data:
                    # Update to active
                    supabase.table("user_profiles").update({"subscription_status": "active"}).eq("email", issue.user_email).execute()
                    return True
                else:
                    # Update to free tier
                    supabase.table("user_profiles").update({"plan_tier": "free"}).eq("email", issue.user_email).execute()
                    return True
            
            elif issue.issue_type == "missing_subscription_status":
                # Set default subscription status
                supabase.table("user_profiles").update({"subscription_status": "inactive"}).eq("email", issue.user_email).execute()
                return True
            
            elif issue.issue_type == "missing_plan_tier":
                # Set default plan tier
                supabase.table("user_profiles").update({"plan_tier": "free"}).eq("email", issue.user_email).execute()
                return True
            
            elif issue.issue_type == "recent_payment_inactive":
                # Sync subscription status
                result = await subscription_sync_service.sync_user_subscription(issue.user_email)
                return result.get("success", False)
            
            elif issue.issue_type == "active_no_subscription":
                # Sync subscription from Stripe
                result = await subscription_sync_service.sync_user_subscription(issue.user_email)
                return result.get("success", False)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Issue correction error: {str(e)}")
            return False
    
    def _can_auto_correct(self) -> bool:
        """
        Check if auto-correction is within rate limits
        """
        now = datetime.utcnow()
        
        # Reset counter if hour has passed
        if (now - self.last_correction_reset).total_seconds() >= 3600:
            self.correction_count = 0
            self.last_correction_reset = now
        
        return self.correction_count < self.max_auto_corrections_per_hour
    
    def _group_issues_by_severity(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        """
        Group issues by severity level
        """
        groups = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for issue in issues:
            groups[issue.severity.value] += 1
        
        return groups
    
    async def _store_validation_results(self, issues: List[ValidationIssue], correlation_id: str):
        """
        Store validation results for tracking
        """
        try:
            validation_data = {
                "correlation_id": correlation_id,
                "total_issues": len(issues),
                "issues_by_severity": json.dumps(self._group_issues_by_severity(issues)),
                "issues_detail": json.dumps([{
                    "issue_id": issue.issue_id,
                    "user_email": issue.user_email,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "auto_correctable": issue.auto_correctable
                } for issue in issues]),
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("integrity_validation_results").insert(validation_data).execute()
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Store validation results error: {str(e)}")
    
    async def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics
        """
        try:
            # Get stats from last 24 hours
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            result = supabase.table("integrity_validation_results").select("*").gte("created_at", since).execute()
            
            total_validations = len(result.data)
            total_issues = sum(r.get("total_issues", 0) for r in result.data)
            
            stats = {
                "total_validations": total_validations,
                "total_issues": total_issues,
                "average_issues_per_validation": round(total_issues / max(total_validations, 1), 2),
                "period": "24h",
                "last_validation": result.data[0].get("created_at") if result.data else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Validation stats error: {str(e)}")
            return {"error": str(e)}

# Global instance
integrity_validation_service = IntegrityValidationService()
