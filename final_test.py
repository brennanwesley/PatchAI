#!/usr/bin/env python3
"""
Final PatchAI Testing Suite
Tests both frontend and backend with correct URLs
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

class PatchAITester:
    def __init__(self):
        # Correct URLs based on diagnostics
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
    
    async def test_backend_health(self):
        """Test backend health and basic endpoints"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Test root endpoint
                response = await client.get(self.backend_url)
                
                if response.status_code == 200:
                    data = response.json()
                    version = data.get("version", "unknown")
                    self.log_result("Backend Health", "PASS", f"Version: {version}")
                    
                    # Test health endpoint
                    health_response = await client.get(f"{self.backend_url}/health")
                    if health_response.status_code == 200:
                        self.log_result("Backend Health Endpoint", "PASS", "Health check working")
                    else:
                        self.log_result("Backend Health Endpoint", "WARN", f"Status: {health_response.status_code}")
                    
                    return True
                else:
                    self.log_result("Backend Health", "FAIL", f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("Backend Health", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_backend_cors(self):
        """Test CORS configuration"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Origin": self.frontend_url,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
                
                response = await client.options(f"{self.backend_url}/prompt", headers=headers)
                
                cors_origin = response.headers.get("access-control-allow-origin")
                cors_methods = response.headers.get("access-control-allow-methods")
                cors_credentials = response.headers.get("access-control-allow-credentials")
                
                if cors_origin:
                    self.log_result("CORS Configuration", "PASS", f"Origin: {cors_origin}, Methods: {cors_methods}")
                else:
                    self.log_result("CORS Configuration", "FAIL", "No CORS headers found")
                    
        except Exception as e:
            self.log_result("CORS Configuration", "FAIL", f"Error: {str(e)}")
    
    async def test_protected_endpoints(self):
        """Test that protected endpoints require authentication"""
        endpoints = ["/prompt", "/history"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    
                    if endpoint == "/prompt":
                        # Test POST without auth
                        response = await client.post(url, json={"messages": [{"role": "user", "content": "test"}]})
                    else:
                        # Test GET without auth
                        response = await client.get(url)
                    
                    if response.status_code in [401, 403]:
                        self.log_result(f"Auth Protection {endpoint}", "PASS", f"Properly protected (HTTP {response.status_code})")
                    elif response.status_code == 422:
                        self.log_result(f"Auth Protection {endpoint}", "PASS", "Validation error (expected without auth)")
                    else:
                        self.log_result(f"Auth Protection {endpoint}", "WARN", f"Unexpected status: {response.status_code}")
                        
                except Exception as e:
                    self.log_result(f"Auth Protection {endpoint}", "FAIL", f"Error: {str(e)}")
    
    async def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.frontend_url)
                
                if response.status_code == 200:
                    content = response.text.lower()
                    
                    # Check for key indicators
                    has_react = "react" in content
                    has_patchai = "patchai" in content
                    has_js_bundle = ".js" in content and ("bundle" in content or "chunk" in content)
                    
                    if has_patchai or has_js_bundle:
                        self.log_result("Frontend Accessibility", "PASS", "Frontend loaded successfully")
                    elif has_react:
                        self.log_result("Frontend Accessibility", "WARN", "React detected but PatchAI branding unclear")
                    else:
                        self.log_result("Frontend Accessibility", "WARN", "Frontend loaded but content unclear")
                else:
                    self.log_result("Frontend Accessibility", "FAIL", f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Frontend Accessibility", "FAIL", f"Error: {str(e)}")
    
    async def test_api_docs(self):
        """Test API documentation availability"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backend_url}/docs")
                
                if response.status_code == 200:
                    self.log_result("API Documentation", "PASS", "Swagger docs available")
                else:
                    self.log_result("API Documentation", "WARN", f"Docs status: {response.status_code}")
                    
        except Exception as e:
            self.log_result("API Documentation", "FAIL", f"Error: {str(e)}")
    
    async def run_comprehensive_tests(self):
        """Run all tests"""
        print("PATCHAI COMPREHENSIVE TEST SUITE")
        print("=" * 50)
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 50)
        
        # Backend tests
        print("\nBACKEND TESTS:")
        print("-" * 20)
        await self.test_backend_health()
        await self.test_backend_cors()
        await self.test_protected_endpoints()
        await self.test_api_docs()
        
        # Frontend tests
        print("\nFRONTEND TESTS:")
        print("-" * 20)
        await self.test_frontend_accessibility()
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"WARNINGS: {warnings}")
        print(f"TOTAL: {len(self.results)}")
        
        # Show critical issues
        if failed > 0:
            print("\nCRITICAL ISSUES:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
        
        if warnings > 0:
            print("\nWARNINGS:")
            for result in self.results:
                if result["status"] == "WARN":
                    print(f"  - {result['test']}: {result['details']}")
        
        # Save results
        report = {
            "timestamp": datetime.now().isoformat(),
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "summary": {
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "total": len(self.results)
            },
            "results": self.results
        }
        
        with open("patchai_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: patchai_test_report.json")
        
        # Overall status
        if failed == 0:
            print("\nOVERALL STATUS: HEALTHY")
            if warnings > 0:
                print("Note: Some warnings detected but no critical failures")
        else:
            print("\nOVERALL STATUS: ISSUES DETECTED")
            print("Action required: Fix critical failures before deployment")
        
        return failed == 0

async def main():
    tester = PatchAITester()
    success = await tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
