#!/usr/bin/env python3
"""
Backend Debug Script
Checks backend deployment status and provides detailed diagnostics
"""

import asyncio
import httpx
import json
from datetime import datetime

class BackendDebugger:
    def __init__(self):
        self.backend_urls = [
            "https://patchai-backend-latest.onrender.com",
            "https://patchai-backend.onrender.com",
            "https://patchai-backend-latest.onrender.com/docs",
            "https://patchai-backend-latest.onrender.com/health"
        ]
        self.results = []
    
    async def check_url(self, url, description=""):
        """Check a specific URL"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                print(f"Checking: {url}")
                response = await client.get(url)
                
                result = {
                    "url": url,
                    "description": description,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_preview": response.text[:200] if response.text else "",
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"  Status: {response.status_code}")
                print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                if response.status_code == 200:
                    print(f"  Content Preview: {response.text[:100]}...")
                elif response.status_code in [301, 302, 307, 308]:
                    print(f"  Redirect to: {response.headers.get('location', 'N/A')}")
                
                self.results.append(result)
                return result
                
        except Exception as e:
            error_result = {
                "url": url,
                "description": description,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"  ERROR: {str(e)}")
            self.results.append(error_result)
            return error_result
    
    async def check_render_service(self):
        """Check Render service status"""
        print("\n" + "=" * 50)
        print("RENDER SERVICE DIAGNOSTICS")
        print("=" * 50)
        
        # Check main backend URL
        await self.check_url("https://patchai-backend-latest.onrender.com", "Main Backend")
        
        # Check health endpoint
        await self.check_url("https://patchai-backend-latest.onrender.com/health", "Health Check")
        
        # Check docs endpoint
        await self.check_url("https://patchai-backend-latest.onrender.com/docs", "API Documentation")
        
        # Check root with different paths
        await self.check_url("https://patchai-backend-latest.onrender.com/", "Root Path")
        
        # Try alternative backend URL
        await self.check_url("https://patchai-backend.onrender.com", "Alternative Backend URL")
    
    async def test_cors_preflight(self):
        """Test CORS preflight request"""
        print("\n" + "=" * 50)
        print("CORS PREFLIGHT TEST")
        print("=" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Origin": "https://patchai-frontend.vercel.app",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
                
                response = await client.options(
                    "https://patchai-backend-latest.onrender.com/prompt", 
                    headers=headers
                )
                
                print(f"CORS Preflight Status: {response.status_code}")
                print("CORS Headers:")
                for header, value in response.headers.items():
                    if "access-control" in header.lower():
                        print(f"  {header}: {value}")
                        
        except Exception as e:
            print(f"CORS Test Error: {str(e)}")
    
    async def run_diagnostics(self):
        """Run all diagnostics"""
        print("PATCHAI BACKEND DIAGNOSTICS")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        await self.check_render_service()
        await self.test_cors_preflight()
        
        # Save detailed results
        with open("backend_diagnostics.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, indent=2)
        
        print(f"\n" + "=" * 50)
        print("DIAGNOSTICS COMPLETE")
        print("=" * 50)
        print("Detailed results saved to: backend_diagnostics.json")
        
        # Summary
        working_urls = [r for r in self.results if r.get("status_code") == 200]
        error_urls = [r for r in self.results if "error" in r]
        
        print(f"Working URLs: {len(working_urls)}")
        print(f"Error URLs: {len(error_urls)}")
        print(f"Total Checked: {len(self.results)}")
        
        if working_urls:
            print("\nWorking URLs:")
            for result in working_urls:
                print(f"  ✓ {result['url']}")
        
        if error_urls:
            print("\nError URLs:")
            for result in error_urls:
                print(f"  ✗ {result['url']} - {result.get('error', 'Unknown error')}")

async def main():
    debugger = BackendDebugger()
    await debugger.run_diagnostics()

if __name__ == "__main__":
    asyncio.run(main())
