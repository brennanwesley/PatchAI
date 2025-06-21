#!/usr/bin/env python3
"""
PatchAI Testing Suite - Comprehensive API and Integration Testing
Detects issues before production deployment
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import httpx
import subprocess
import os

class PatchAITestSuite:
    def __init__(self):
        self.backend_url = "https://patchai-backend.onrender.com"
        self.frontend_url = "https://patchai-frontend.vercel.app"
        self.local_backend = "http://localhost:8000"
        self.local_frontend = "http://localhost:3000"
        
        self.test_results = []
        self.errors = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "√" if status == "PASS" else "×" if status == "FAIL" else "!"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
            
    async def test_cors_policy(self):
        """Test CORS configuration"""
        try:
            async with httpx.AsyncClient() as client:
                # Test preflight request
                response = await client.options(
                    f"{self.backend_url}/history",
                    headers={
                        "Origin": self.frontend_url,
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "authorization,content-type"
                    }
                )
                
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                    "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
                    "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                }
                
                if cors_headers["access-control-allow-origin"] == self.frontend_url:
                    self.log_test("CORS Origin", "PASS", f"Allows {self.frontend_url}")
                else:
                    self.log_test("CORS Origin", "FAIL", f"Expected {self.frontend_url}, got {cors_headers['access-control-allow-origin']}")
                    
                if cors_headers["access-control-allow-credentials"] == "true":
                    self.log_test("CORS Credentials", "PASS", "Credentials allowed")
                else:
                    self.log_test("CORS Credentials", "FAIL", "Credentials not allowed")
                    
        except Exception as e:
            self.log_test("CORS Policy", "FAIL", str(e))
            
    async def test_backend_endpoints(self):
        """Test all backend API endpoints"""
        endpoints = [
            ("GET", "/health", None),
            ("GET", "/metrics", None),
            ("GET", "/rate-limit-status", None),
        ]
        
        async with httpx.AsyncClient() as client:
            for method, endpoint, data in endpoints:
                try:
                    if method == "GET":
                        response = await client.get(f"{self.backend_url}{endpoint}")
                    elif method == "POST":
                        response = await client.post(f"{self.backend_url}{endpoint}", json=data)
                        
                    if response.status_code < 400:
                        self.log_test(f"Backend {method} {endpoint}", "PASS", f"Status: {response.status_code}")
                    else:
                        self.log_test(f"Backend {method} {endpoint}", "FAIL", f"Status: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Backend {method} {endpoint}", "FAIL", str(e))
                    
    async def test_authenticated_endpoints(self):
        """Test endpoints that require authentication"""
        # This would need a valid JWT token - for now just test the response
        endpoints = [
            ("GET", "/history"),
            ("POST", "/prompt"),
        ]
        
        async with httpx.AsyncClient() as client:
            for method, endpoint in endpoints:
                try:
                    headers = {"Authorization": "Bearer invalid_token"}
                    
                    if method == "GET":
                        response = await client.get(f"{self.backend_url}{endpoint}", headers=headers)
                    elif method == "POST":
                        response = await client.post(
                            f"{self.backend_url}{endpoint}", 
                            headers=headers,
                            json={"messages": [{"role": "user", "content": "test"}]}
                        )
                        
                    # Should return 401 for invalid token
                    if response.status_code == 401:
                        self.log_test(f"Auth {method} {endpoint}", "PASS", "Properly rejects invalid token")
                    else:
                        self.log_test(f"Auth {method} {endpoint}", "WARN", f"Unexpected status: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Auth {method} {endpoint}", "FAIL", str(e))
                    
    async def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.frontend_url)
                
                if response.status_code == 200:
                    self.log_test("Frontend Accessibility", "PASS", "Frontend loads successfully")
                    
                    # Check for common errors in HTML
                    html = response.text
                    if "Application error" in html:
                        self.log_test("Frontend Errors", "FAIL", "Application error detected in HTML")
                    elif "Runtime Error" in html:
                        self.log_test("Frontend Errors", "FAIL", "Runtime error detected in HTML")
                    else:
                        self.log_test("Frontend Errors", "PASS", "No obvious errors in HTML")
                        
                else:
                    self.log_test("Frontend Accessibility", "FAIL", f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Frontend Accessibility", "FAIL", str(e))
            
    def test_local_setup(self):
        """Test local development setup"""
        # Check if backend dependencies are installed
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import fastapi, openai, supabase"],
                capture_output=True,
                text=True,
                cwd="backend"
            )
            
            if result.returncode == 0:
                self.log_test("Backend Dependencies", "PASS", "All Python packages available")
            else:
                self.log_test("Backend Dependencies", "FAIL", result.stderr)
                
        except Exception as e:
            self.log_test("Backend Dependencies", "FAIL", str(e))
            
        # Check if frontend dependencies exist
        if os.path.exists("frontend/node_modules"):
            self.log_test("Frontend Dependencies", "PASS", "node_modules exists")
        else:
            self.log_test("Frontend Dependencies", "FAIL", "node_modules missing - run npm install")
            
    async def run_integration_test(self):
        """Run a full integration test simulating frontend behavior"""
        try:
            async with httpx.AsyncClient() as client:
                # Simulate the exact request the frontend makes
                response = await client.get(
                    f"{self.backend_url}/history",
                    headers={
                        "Origin": self.frontend_url,
                        "Authorization": "Bearer test_token",
                        "Content-Type": "application/json"
                    }
                )
                
                # Check response headers for CORS
                cors_origin = response.headers.get("access-control-allow-origin")
                cors_credentials = response.headers.get("access-control-allow-credentials")
                
                if cors_origin == self.frontend_url and cors_credentials == "true":
                    self.log_test("Integration CORS", "PASS", "CORS headers correct for frontend")
                else:
                    self.log_test("Integration CORS", "FAIL", f"Origin: {cors_origin}, Credentials: {cors_credentials}")
                    
                # Check if it's an auth error (expected) vs CORS error
                if response.status_code == 401:
                    self.log_test("Integration Auth", "PASS", "Authentication properly required")
                elif response.status_code == 200:
                    self.log_test("Integration Auth", "WARN", "No authentication required - check security")
                else:
                    self.log_test("Integration Auth", "FAIL", f"Unexpected status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Integration Test", "FAIL", str(e))
            
    async def run_all_tests(self):
        """Run all tests"""
        print("STARTING PATCHAI TEST SUITE")
        print("=" * 50)
        
        # Local setup tests
        self.test_local_setup()
        
        # Backend tests
        await self.test_backend_endpoints()
        await self.test_authenticated_endpoints()
        
        # CORS tests
        await self.test_cors_policy()
        
        # Frontend tests
        await self.test_frontend_accessibility()
        
        # Integration tests
        await self.run_integration_test()
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"WARNINGS: {warnings}")
        print(f"TOTAL: {len(self.test_results)}")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   FAIL {result['test']}: {result['details']}")
                    
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\nDetailed results saved to: test_results.json")
        
        return failed == 0

if __name__ == "__main__":
    async def main():
        suite = PatchAITestSuite()
        success = await suite.run_all_tests()
        sys.exit(0 if success else 1)
        
    asyncio.run(main())
