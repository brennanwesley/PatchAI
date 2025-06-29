#!/usr/bin/env python3
"""
Phase 3 Production Hardening Validation Script
Comprehensive testing of all Phase 3 services and endpoints
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"  # Local development
# BASE_URL = "https://patchai-backend.onrender.com"  # Production

class Phase3Validator:
    """
    Comprehensive validation suite for Phase 3 production hardening
    """
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "response_data": response_data
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            
            self.log_result(
                "Basic Connectivity",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Connection error: {str(e)}")
    
    def test_phase3_health(self):
        """Test Phase 3 system health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/phase3/health")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                health_score = data.get("health", {}).get("overall_score", 0)
                details = f"Health Score: {health_score}, Status: {data.get('health', {}).get('status', 'unknown')}"
            else:
                details = f"Status: {response.status_code}"
                data = {"error": response.text}
            
            self.log_result(
                "Phase 3 System Health",
                success,
                details,
                data if success else None
            )
            
        except Exception as e:
            self.log_result("Phase 3 System Health", False, f"Error: {str(e)}")
    
    def test_webhook_redundancy(self):
        """Test webhook redundancy endpoints"""
        # Test webhook stats
        try:
            response = self.session.get(f"{self.base_url}/phase3/webhooks/stats")
            success = response.status_code == 200
            
            self.log_result(
                "Webhook Stats",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Webhook Stats", False, f"Error: {str(e)}")
        
        # Test webhook recovery
        try:
            response = self.session.post(f"{self.base_url}/phase3/webhooks/recover")
            success = response.status_code == 200
            
            self.log_result(
                "Webhook Recovery",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Webhook Recovery", False, f"Error: {str(e)}")
        
        # Test redundant webhook processing
        try:
            test_payload = {
                "event_data": {
                    "type": "test_event",
                    "data": {"test": True, "timestamp": datetime.utcnow().isoformat()}
                },
                "endpoint_id": "test_endpoint"
            }
            
            response = self.session.post(
                f"{self.base_url}/phase3/webhooks/redundant",
                json=test_payload
            )
            success = response.status_code == 200
            
            self.log_result(
                "Redundant Webhook Processing",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Redundant Webhook Processing", False, f"Error: {str(e)}")
    
    def test_integrity_validation(self):
        """Test integrity validation endpoints"""
        # Test integrity stats
        try:
            response = self.session.get(f"{self.base_url}/phase3/integrity/stats")
            success = response.status_code == 200
            
            self.log_result(
                "Integrity Stats",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Integrity Stats", False, f"Error: {str(e)}")
        
        # Test integrity validation
        try:
            test_payload = {
                "validation_type": "critical",
                "force_critical": True
            }
            
            response = self.session.post(
                f"{self.base_url}/phase3/integrity/validate",
                json=test_payload
            )
            success = response.status_code == 200
            
            self.log_result(
                "Integrity Validation",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Integrity Validation", False, f"Error: {str(e)}")
        
        # Test continuous validation start
        try:
            response = self.session.post(f"{self.base_url}/phase3/integrity/start-continuous")
            success = response.status_code == 200
            
            self.log_result(
                "Start Continuous Validation",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Start Continuous Validation", False, f"Error: {str(e)}")
    
    def test_performance_optimization(self):
        """Test performance optimization endpoints"""
        # Test performance stats
        try:
            response = self.session.get(f"{self.base_url}/phase3/performance/stats")
            success = response.status_code == 200
            
            self.log_result(
                "Performance Stats",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Performance Stats", False, f"Error: {str(e)}")
        
        # Test performance alerts
        try:
            response = self.session.get(f"{self.base_url}/phase3/performance/alerts?hours=24")
            success = response.status_code == 200
            
            self.log_result(
                "Performance Alerts",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Performance Alerts", False, f"Error: {str(e)}")
        
        # Test performance optimization
        try:
            test_payload = {
                "clear_cache": True,
                "reset_metrics": False
            }
            
            response = self.session.post(
                f"{self.base_url}/phase3/performance/optimize",
                json=test_payload
            )
            success = response.status_code == 200
            
            self.log_result(
                "Performance Optimization",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Performance Optimization", False, f"Error: {str(e)}")
    
    def test_monitoring_dashboard(self):
        """Test monitoring dashboard endpoints"""
        # Test dashboard data
        try:
            response = self.session.get(f"{self.base_url}/phase3/dashboard/data")
            success = response.status_code == 200
            
            self.log_result(
                "Dashboard Data",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Dashboard Data", False, f"Error: {str(e)}")
        
        # Test real-time alerts
        try:
            response = self.session.get(f"{self.base_url}/phase3/dashboard/alerts")
            success = response.status_code == 200
            
            self.log_result(
                "Real-time Alerts",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Real-time Alerts", False, f"Error: {str(e)}")
        
        # Test historical trends
        try:
            response = self.session.get(f"{self.base_url}/phase3/dashboard/trends/sync_success_rate?hours=24")
            success = response.status_code == 200
            
            self.log_result(
                "Historical Trends",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Historical Trends", False, f"Error: {str(e)}")
        
        # Test dashboard service start
        try:
            response = self.session.post(f"{self.base_url}/phase3/dashboard/start")
            success = response.status_code == 200
            
            self.log_result(
                "Start Dashboard Service",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Start Dashboard Service", False, f"Error: {str(e)}")
    
    def test_emergency_recovery(self):
        """Test emergency recovery endpoint"""
        try:
            response = self.session.post(f"{self.base_url}/phase3/emergency/recover")
            success = response.status_code == 200
            
            self.log_result(
                "Emergency Recovery",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Emergency Recovery", False, f"Error: {str(e)}")
    
    def test_existing_endpoints(self):
        """Test that existing endpoints still work"""
        # Test Phase 2 sync endpoints
        try:
            response = self.session.get(f"{self.base_url}/sync/health")
            success = response.status_code == 200
            
            self.log_result(
                "Phase 2 Sync Health",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Phase 2 Sync Health", False, f"Error: {str(e)}")
        
        # Test monitoring endpoints
        try:
            response = self.session.get(f"{self.base_url}/monitoring/health")
            success = response.status_code == 200
            
            self.log_result(
                "Monitoring Health",
                success,
                f"Status: {response.status_code}",
                response.json() if success else {"error": response.text}
            )
            
        except Exception as e:
            self.log_result("Monitoring Health", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting Phase 3 Production Hardening Validation")
        print("=" * 60)
        
        # Basic connectivity
        print("\n📡 Testing Basic Connectivity...")
        self.test_basic_connectivity()
        
        # Phase 3 system health
        print("\n🏥 Testing Phase 3 System Health...")
        self.test_phase3_health()
        
        # Webhook redundancy
        print("\n🔄 Testing Webhook Redundancy...")
        self.test_webhook_redundancy()
        
        # Integrity validation
        print("\n🔍 Testing Integrity Validation...")
        self.test_integrity_validation()
        
        # Performance optimization
        print("\n⚡ Testing Performance Optimization...")
        self.test_performance_optimization()
        
        # Monitoring dashboard
        print("\n📊 Testing Monitoring Dashboard...")
        self.test_monitoring_dashboard()
        
        # Emergency recovery
        print("\n🚨 Testing Emergency Recovery...")
        self.test_emergency_recovery()
        
        # Existing endpoints
        print("\n🔧 Testing Existing Endpoints...")
        self.test_existing_endpoints()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 PHASE 3 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n📄 Detailed Results:")
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        # Save results to file
        with open("phase3_validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: phase3_validation_results.json")

def main():
    """Main validation function"""
    import sys
    
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    
    print(f"🎯 Target URL: {base_url}")
    
    validator = Phase3Validator(base_url)
    validator.run_all_tests()

if __name__ == "__main__":
    main()
