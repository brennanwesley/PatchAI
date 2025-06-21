#!/usr/bin/env python3
"""
Simple PatchAI Backend Test
Tests basic API connectivity without complex dependencies
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

class SimpleTester:
    def __init__(self):
        self.backend_url = "https://patchai-backend-latest.onrender.com"
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
        """Test if backend is accessible"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backend_url}/health")
                
                if response.status_code == 200:
                    self.log_result("Backend Health Check", "PASS", f"Status: {response.status_code}")
                    return True
                else:
                    self.log_result("Backend Health Check", "FAIL", f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("Backend Health Check", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_backend_cors(self):
        """Test CORS headers"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Origin": self.frontend_url,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
                
                response = await client.options(f"{self.backend_url}/prompt", headers=headers)
                
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                    "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                    "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
                    "access-control-allow-credentials": response.headers.get("access-control-allow-credentials")
                }
                
                if cors_headers["access-control-allow-origin"]:
                    self.log_result("CORS Configuration", "PASS", f"Origin allowed: {cors_headers['access-control-allow-origin']}")
                else:
                    self.log_result("CORS Configuration", "FAIL", "No CORS headers found")
                    
        except Exception as e:
            self.log_result("CORS Configuration", "FAIL", f"Error: {str(e)}")
    
    async def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.frontend_url)
                
                if response.status_code == 200:
                    content = response.text
                    if "PatchAI" in content or "react" in content.lower():
                        self.log_result("Frontend Accessibility", "PASS", f"Status: {response.status_code}")
                    else:
                        self.log_result("Frontend Accessibility", "WARN", "Frontend loaded but content unclear")
                else:
                    self.log_result("Frontend Accessibility", "FAIL", f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Frontend Accessibility", "FAIL", f"Error: {str(e)}")
    
    async def test_api_endpoints(self):
        """Test key API endpoints"""
        endpoints = [
            ("/health", "GET"),
            ("/prompt", "POST"),
            ("/history", "GET")
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint, method in endpoints:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    
                    if method == "GET":
                        response = await client.get(url)
                    elif method == "POST":
                        # Test without auth - should get 401/403
                        response = await client.post(url, json={"messages": [{"role": "user", "content": "test"}]})
                    
                    # For protected endpoints, 401/403 is expected
                    if endpoint in ["/prompt", "/history"] and response.status_code in [401, 403]:
                        self.log_result(f"Endpoint {endpoint}", "PASS", f"Protected endpoint returns {response.status_code}")
                    elif endpoint == "/health" and response.status_code == 200:
                        self.log_result(f"Endpoint {endpoint}", "PASS", f"Health check returns {response.status_code}")
                    else:
                        self.log_result(f"Endpoint {endpoint}", "WARN", f"Unexpected status: {response.status_code}")
                        
                except Exception as e:
                    self.log_result(f"Endpoint {endpoint}", "FAIL", f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("PATCHAI SIMPLE TEST SUITE")
        print("=" * 40)
        
        # Test backend
        await self.test_backend_health()
        await self.test_backend_cors()
        await self.test_api_endpoints()
        
        # Test frontend
        await self.test_frontend_accessibility()
        
        # Summary
        print("\n" + "=" * 40)
        print("TEST SUMMARY")
        print("=" * 40)
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"WARNINGS: {warnings}")
        print(f"TOTAL: {len(self.results)}")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
        
        # Save results
        with open("simple_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: simple_test_results.json")
        return failed == 0

async def main():
    tester = SimpleTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
