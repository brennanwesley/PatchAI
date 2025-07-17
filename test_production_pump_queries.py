"""
PatchAI Production Pump Data Test Script
---------------------------------------
This script tests the production backend for pump data queries and helps identify 500 errors.
"""

import os
import sys
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional
import logging
from datetime import datetime
import getpass
from supabase import create_client, Client

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pump_test_log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Production API endpoint
PRODUCTION_URL = "https://patchai-backend.onrender.com"

# Supabase configuration (from frontend .env)
SUPABASE_URL = "https://iyacqcylnunndcswaeri.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5YWNxY3lsbnVubmRjc3dhZXJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzOTIzMzAsImV4cCI6MjA2NTk2ODMzMH0.ZvdEPVYXCdHOByJF3cHJswqYYXmNFpB8Bmd03tzwHko"

class PumpTester:
    def __init__(self, base_url: str = PRODUCTION_URL):
        self.base_url = base_url
        self.session = None
        self.supabase: Optional[Client] = None
        self.jwt_token: Optional[str] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        # Initialize Supabase client
        self.supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self, email: str = None, password: str = None) -> bool:
        """Authenticate with Supabase and get JWT token."""
        try:
            if not email:
                email = input("Enter your PatchAI email: ")
            if not password:
                password = getpass.getpass("Enter your PatchAI password: ")
            
            logger.info(f"Authenticating with email: {email}")
            
            # Sign in with Supabase
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                self.jwt_token = response.session.access_token
                logger.info("✅ Authentication successful")
                logger.info(f"Token preview: {self.jwt_token[:50]}...")
                return True
            else:
                logger.error("[ERROR] Authentication failed: No user or session returned")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Authentication error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with JWT authentication."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
            
        return headers
    
    async def test_endpoint_health(self) -> bool:
        """Check if the production endpoint is reachable and healthy."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                logger.info(f"Health check response: {json.dumps(data, indent=2)}")
                
                # Check for both 'status' and 'application.errors_total'
                is_healthy = data.get('status') in ['ok', 'healthy']
                error_count = data.get('application', {}).get('errors_total', 0)
                
                if error_count > 0:
                    logger.warning(f"Found {error_count} error(s) in application logs")
                    if 'errors_by_type' in data.get('application', {}):
                        for error_type, count in data['application']['errors_by_type'].items():
                            logger.warning(f"  - {error_type}: {count} error(s)")
                
                return is_healthy
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            logger.error(f"Response content: {await response.text() if 'response' in locals() else 'No response'}")
            return False
    
    async def test_pump_query(self, query: str, description: str) -> Dict:
        """Test a specific pump query against the production backend."""
        try:
            logger.info(f"Testing: {description}")
            logger.info(f"Query: {query}")
            
            # Check if we have authentication
            if not self.jwt_token:
                logger.error("[ERROR] No JWT token available. Please authenticate first.")
                return {
                    "success": False,
                    "error": "Not authenticated",
                    "description": description,
                    "query": query
                }
            
            # Prepare the payload matching frontend format
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            }
            
            # Send request to /prompt endpoint with authentication
            async with self.session.post(
                f"{self.base_url}/prompt",
                json=payload,
                headers=self.get_auth_headers()
            ) as response:
                response_data = await response.json() if response.status == 200 else {
                    "error": await response.text(),
                    "status_code": response.status
                }
                
                # Log the full response for debugging
                logger.info(f"Response status: {response.status}")
                
                if response.status != expected_status:
                    logger.error(f"Unexpected status code: {response.status}")
                    logger.error(f"Response: {json.dumps(response_data, indent=2)}")
                else:
                    logger.info("Request completed successfully")
                    
                    # Check if the response contains pump data
                    content = (response_data.get('content') or '').lower()
                    has_pump_data = any(term in content for term in [
                        'pump', 'head', 'flow', 'efficiency', 'npsh', 'rpm', 'gpm', 'psi'
                    ])
                    
                    if has_pump_data:
                        logger.info("✅ Response contains pump-related data")
                    else:
                        logger.warning("⚠️ Response does not appear to contain pump data")
                
                return {
                    "query": query,
                    "status": response.status,
                    "response": response_data,
                    "success": response.status == expected_status,
                    "has_pump_data": has_pump_data if response.status == 200 else None
                }
                
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {
                "query": query,
                "status": 0,
                "error": str(e),
                "success": False
            }

async def run_tests():
    """Run all pump data tests against production."""
    test_queries = [
        ("What's the flowrate vs pressure for a 4x6-13 pump?", "4x6-13 Flowrate vs Pressure Query"),
        ("Show me the performance curve for a 2x3-13 pump at 1750 RPM", "2x3-13 Performance Curve Query"),
        ("What's the efficiency of a 3x4-13 pump at 100 GPM and 100 ft?", "3x4-13 Efficiency Query"),
        ("Compare the performance of 4x6-13 and 6x8-15 pumps", "Pump Performance Comparison Query"),
        ("What's the NPSHr for a 8x10-17 pump at 2000 GPM?", "8x10-17 NPSHr Query")
    ]
    
    results = []
    
    try:
        async with PumpTester() as tester:
            # First, authenticate with Supabase
            logger.info("\n[AUTH] AUTHENTICATION STEP")
            logger.info("="*50)
            
            # Check for command line arguments for email/password
            email = sys.argv[1] if len(sys.argv) > 1 else None
            password = sys.argv[2] if len(sys.argv) > 2 else None
            
            auth_success = await tester.authenticate(email, password)
            
            if not auth_success:
                logger.error("[ERROR] Authentication failed. Cannot proceed with tests.")
                return []
            
            # Check if the endpoint is reachable
            logger.info("\n[HEALTH] HEALTH CHECK")
            logger.info("="*50)
            is_healthy = await tester.test_endpoint_health()
            
            if not is_healthy:
                logger.warning("Production endpoint reported potential issues, but continuing with tests...")
            
            # Run all test queries
            logger.info("\n[TESTS] PUMP DATA TESTS")
            logger.info("="*50)
            for query, description in test_queries:
                try:
                    logger.info("\n" + "="*80)
                    logger.info(f"TESTING: {description}")
                    logger.info("="*80)
                    
                    result = await tester.test_pump_query(query, description)
                    results.append(result)
                    
                    # Log detailed results
                    if result.get('success'):
                        logger.info("✅ Test passed")
                        if result.get('has_pump_data'):
                            logger.info("   - Contains pump data")
                        else:
                            logger.warning("   - No pump data found in response")
                    else:
                        logger.error(f"❌ Test failed with status: {result.get('status')}")
                        logger.error(f"   - Error: {result.get('error', 'No error details')}")
                    
                    # Add a small delay between tests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Unexpected error during test: {str(e)}")
                    results.append({
                        "query": query,
                        "error": str(e),
                        "success": False
                    })
    
    except Exception as e:
        logger.error(f"Fatal error in test execution: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return results

def generate_report(results: List[Dict]):
    """Generate a test report."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"pump_test_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("=== PatchAI Pump Data Test Report ===\n")
        f.write(f"Generated at: {datetime.now()}\n\n")
        
        total = len(results)
        success = sum(1 for r in results if r.get('success', False))
        has_pump_data = sum(1 for r in results if r.get('has_pump_data', False))
        
        f.write(f"Test Results Summary:\n")
        f.write(f"- Total queries: {total}\n")
        success_pct = (success/total*100) if total > 0 else 0
        pump_data_pct = (has_pump_data/total*100) if total > 0 else 0
        f.write(f"- Successful responses: {success}/{total} ({success_pct:.1f}%)\n")
        f.write(f"- Responses with pump data: {has_pump_data}/{total} ({pump_data_pct:.1f}%)\n\n")
        
        f.write("\n=== Detailed Results ===\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"Query {i}: {result['query']}\n")
            f.write(f"Status: {result['status']} {'✅' if result.get('success') else '❌'}\n")
            
            if 'error' in result:
                f.write(f"Error: {result['error']}\n")
            
            if 'has_pump_data' in result and result['has_pump_data'] is not None:
                f.write(f"Pump Data: {'✅ Found' if result['has_pump_data'] else '❌ Not Found'}\n")
            
            f.write("-" * 80 + "\n")
    
    logger.info(f"\nTest report generated: {report_file}")
    return report_file

if __name__ == "__main__":
    logger.info("=== Starting PatchAI Pump Data Tests ===\n")
    
    # Run the tests
    results = asyncio.run(run_tests())
    
    # Generate and display the report
    report_file = generate_report(results)
    
    logger.info("\n=== Test Summary ===")
    logger.info(f"Total queries: {len(results)}")
    logger.info(f"Successful: {sum(1 for r in results if r.get('success', False))}")
    logger.info(f"With pump data: {sum(1 for r in results if r.get('has_pump_data', False))}")
    logger.info(f"\nView full report in: {report_file}")
    
    # Exit with error code if any tests failed
    if any(not r.get('success', False) for r in results):
        sys.exit(1)
