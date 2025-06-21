#!/usr/bin/env python3
"""
Complete PatchAI Testing Suite
Combines backend API tests with frontend accessibility checks
No external dependencies required beyond httpx
"""

import asyncio
import httpx
import json
import sys
import re
from datetime import datetime

class CompleteTester:
    def __init__(self):
        self.backend_url = "https://patchai-backend.onrender.com"
        self.frontend_url = "https://patchai-frontend.vercel.app"
        self.results = []
    
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_symbol = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[WARN]"
        print(f"{status_symbol} {test_name}")
        if details:
            print(f"    {details}")
    
    async def test_backend_comprehensive(self):
        """Comprehensive backend testing"""
        print("\nBACKEND TESTS:")
        print("-" * 30)
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Test 1: Backend Health
                response = await client.get(self.backend_url)
                if response.status_code == 200:
                    data = response.json()
                    version = data.get("version", "unknown")
                    self.log_result("Backend Health", "PASS", f"Version: {version}")
                else:
                    self.log_result("Backend Health", "FAIL", f"Status: {response.status_code}")
                    return False
                
                # Test 2: Health Endpoint
                health_response = await client.get(f"{self.backend_url}/health")
                if health_response.status_code == 200:
                    self.log_result("Health Endpoint", "PASS", "Working")
                else:
                    self.log_result("Health Endpoint", "WARN", f"Status: {health_response.status_code}")
                
                # Test 3: CORS Configuration
                headers = {
                    "Origin": self.frontend_url,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
                cors_response = await client.options(f"{self.backend_url}/prompt", headers=headers)
                cors_origin = cors_response.headers.get("access-control-allow-origin")
                
                if cors_origin and self.frontend_url in cors_origin:
                    self.log_result("CORS Configuration", "PASS", f"Frontend origin allowed")
                elif cors_origin:
                    self.log_result("CORS Configuration", "WARN", f"Origin: {cors_origin}")
                else:
                    self.log_result("CORS Configuration", "FAIL", "No CORS headers")
                
                # Test 4: Authentication Protection
                auth_test = await client.post(f"{self.backend_url}/prompt", 
                                            json={"messages": [{"role": "user", "content": "test"}]})
                if auth_test.status_code in [401, 403]:
                    self.log_result("Authentication Protection", "PASS", f"Protected (HTTP {auth_test.status_code})")
                else:
                    self.log_result("Authentication Protection", "WARN", f"Status: {auth_test.status_code}")
                
                # Test 5: API Documentation
                docs_response = await client.get(f"{self.backend_url}/docs")
                if docs_response.status_code == 200:
                    self.log_result("API Documentation", "PASS", "Swagger docs available")
                else:
                    self.log_result("API Documentation", "WARN", f"Status: {docs_response.status_code}")
                
                return True
                
        except Exception as e:
            self.log_result("Backend Tests", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_frontend_comprehensive(self):
        """Comprehensive frontend testing"""
        print("\nFRONTEND TESTS:")
        print("-" * 30)
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Test 1: Frontend Accessibility
                response = await client.get(self.frontend_url)
                
                if response.status_code != 200:
                    self.log_result("Frontend Accessibility", "FAIL", f"Status: {response.status_code}")
                    return False
                
                content = response.text.lower()
                
                # Test 2: React Application Detection
                react_indicators = ["react", "reactdom", "_react", "jsx"]
                has_react = any(indicator in content for indicator in react_indicators)
                
                if has_react:
                    self.log_result("React Application", "PASS", "React framework detected")
                else:
                    self.log_result("React Application", "WARN", "React not clearly detected")
                
                # Test 3: JavaScript Bundle Detection
                js_patterns = [
                    r'<script[^>]+src="[^"]*\.js"',
                    r'<script[^>]+src="[^"]*bundle',
                    r'<script[^>]+src="[^"]*chunk'
                ]
                
                has_js_bundle = any(re.search(pattern, content) for pattern in js_patterns)
                
                if has_js_bundle:
                    self.log_result("JavaScript Bundle", "PASS", "JS bundles detected")
                else:
                    self.log_result("JavaScript Bundle", "WARN", "No clear JS bundles found")
                
                # Test 4: PatchAI Branding
                patchai_indicators = ["patchai", "patch ai", "patch-ai"]
                has_branding = any(indicator in content for indicator in patchai_indicators)
                
                if has_branding:
                    self.log_result("PatchAI Branding", "PASS", "PatchAI branding found")
                else:
                    self.log_result("PatchAI Branding", "WARN", "PatchAI branding not detected")
                
                # Test 5: Meta Tags and SEO
                has_title = "<title>" in content
                has_meta_description = 'name="description"' in content
                has_viewport = 'name="viewport"' in content
                
                if has_title and has_viewport:
                    self.log_result("HTML Structure", "PASS", "Proper HTML structure")
                else:
                    self.log_result("HTML Structure", "WARN", "Missing some HTML meta tags")
                
                # Test 6: CSS Framework Detection
                css_frameworks = ["tailwind", "bootstrap", "material", "chakra"]
                has_css_framework = any(framework in content for framework in css_frameworks)
                
                if has_css_framework:
                    self.log_result("CSS Framework", "PASS", "CSS framework detected")
                else:
                    self.log_result("CSS Framework", "WARN", "No clear CSS framework detected")
                
                return True
                
        except Exception as e:
            self.log_result("Frontend Tests", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_integration(self):
        """Test frontend-backend integration"""
        print("\nINTEGRATION TESTS:")
        print("-" * 30)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test CORS from frontend perspective
                headers = {
                    "Origin": self.frontend_url,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                # Simulate frontend API call
                response = await client.post(
                    f"{self.backend_url}/prompt",
                    headers=headers,
                    json={"messages": [{"role": "user", "content": "test integration"}]}
                )
                
                # Should get 403 (auth required) but with proper CORS headers
                if response.status_code == 403:
                    cors_header = response.headers.get("access-control-allow-origin")
                    if cors_header:
                        self.log_result("Frontend-Backend Integration", "PASS", "CORS working, auth required")
                    else:
                        self.log_result("Frontend-Backend Integration", "FAIL", "Missing CORS headers")
                else:
                    self.log_result("Frontend-Backend Integration", "WARN", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Integration Tests", "FAIL", f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("PATCHAI COMPLETE TEST SUITE")
        print("=" * 60)
        print(f"Backend: {self.backend_url}")
        print(f"Frontend: {self.frontend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Run all test categories
        backend_ok = await self.test_backend_comprehensive()
        frontend_ok = await self.test_frontend_comprehensive()
        await self.test_integration()
        
        # Generate comprehensive report
        self.generate_final_report()
        
        return backend_ok and frontend_ok
    
    def generate_final_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("FINAL TEST REPORT")
        print("=" * 60)
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"WARNINGS: {warnings}")
        print(f"TOTAL: {len(self.results)}")
        
        # Calculate health score
        total_tests = len(self.results)
        health_score = (passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"HEALTH SCORE: {health_score:.1f}%")
        
        # Show issues
        if failed > 0:
            print("\nCRITICAL FAILURES:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  X {result['test']}: {result['details']}")
        
        if warnings > 0:
            print("\nWARNINGS:")
            for result in self.results:
                if result["status"] == "WARN":
                    print(f"  ! {result['test']}: {result['details']}")
        
        # Overall status
        if failed == 0:
            if warnings == 0:
                print("\nOVERALL STATUS: EXCELLENT")
                print("All systems operational, no issues detected.")
            else:
                print("\nOVERALL STATUS: GOOD")
                print("No critical failures, minor warnings detected.")
        else:
            print("\nOVERALL STATUS: NEEDS ATTENTION")
            print("Critical failures detected, immediate action required.")
        
        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "urls": {
                "backend": self.backend_url,
                "frontend": self.frontend_url
            },
            "summary": {
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "total": total_tests,
                "health_score": health_score
            },
            "results": self.results
        }
        
        with open("complete_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report: complete_test_report.json")
        
        # Quick start guide
        print("\nQUICK START:")
        print("- Run this test before any deployment")
        print("- Check for FAILED tests and fix immediately")
        print("- Warnings are optional improvements")
        print("- Health score >90% = production ready")

async def main():
    tester = CompleteTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
