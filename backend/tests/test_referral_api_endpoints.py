"""
API Endpoint Testing for Referral System
Tests all referral API endpoints to ensure they're working correctly
"""

import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferralAPITester:
    """Test all referral API endpoints"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_all_endpoints(self):
        """Test all referral API endpoints"""
        logger.info("🚀 Starting Referral API Endpoint Tests")
        
        try:
            # Test 1: Health check
            self.test_health_check()
            
            # Test 2: Public referral code validation
            self.test_referral_code_validation()
            
            # Test 3: API documentation
            self.test_api_documentation()
            
            logger.info("✅ All Referral API Endpoint Tests Completed Successfully!")
            
        except Exception as e:
            logger.error(f"❌ API Test Suite Failed: {e}")
            raise
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        logger.info("🧪 Testing Health Check...")
        
        response = self.session.get(f"{self.base_url}/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Health check response missing status"
        assert data["status"] == "healthy", f"Service not healthy: {data['status']}"
        
        logger.info("✅ Health check endpoint working correctly")
    
    def test_referral_code_validation(self):
        """Test public referral code validation endpoint"""
        logger.info("🧪 Testing Referral Code Validation Endpoint...")
        
        # Test invalid referral code using JSON (proper Pydantic model format)
        response = self.session.post(
            f"{self.base_url}/referrals/validate-code",
            json={"referral_code": "INVALID"},
            headers={"Content-Type": "application/json"}
        )
        
        # Log response details for debugging
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        # Should return 200 with valid=false for non-existent codes
        assert response.status_code == 200, f"Validation endpoint failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "valid" in data, "Validation response missing 'valid' field"
        assert data["valid"] is False, "Invalid code should return valid=false"
        
        # Test with properly formatted but non-existent code
        response = self.session.post(
            f"{self.base_url}/referrals/validate-code",
            json={"referral_code": "ABC123"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Valid format code validation failed: {response.status_code}"
        data = response.json()
        assert data["valid"] is False, "Non-existent code should return valid=false"
        
        # Test with invalid format (too short)
        response = self.session.post(
            f"{self.base_url}/referrals/validate-code",
            json={"referral_code": "ABC"},
            headers={"Content-Type": "application/json"}
        )
        
        # This should return 422 due to validation error
        assert response.status_code == 422, f"Invalid format should return 422: {response.status_code}"
        
        logger.info("✅ Referral code validation endpoint working correctly")
    
    def test_api_documentation(self):
        """Test API documentation endpoints"""
        logger.info("🧪 Testing API Documentation...")
        
        # Test OpenAPI docs
        response = self.session.get(f"{self.base_url}/docs")
        assert response.status_code == 200, f"API docs failed: {response.status_code}"
        
        # Test OpenAPI JSON schema
        response = self.session.get(f"{self.base_url}/openapi.json")
        assert response.status_code == 200, f"OpenAPI schema failed: {response.status_code}"
        
        schema = response.json()
        assert "paths" in schema, "OpenAPI schema missing paths"
        
        # Check that referral endpoints are documented
        paths = schema["paths"]
        referral_endpoints = [path for path in paths.keys() if "/referrals/" in path]
        assert len(referral_endpoints) > 0, "No referral endpoints found in API documentation"
        
        logger.info(f"✅ API documentation working correctly, found {len(referral_endpoints)} referral endpoints")
    
    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication"""
        logger.info("🧪 Testing Protected Endpoint Authentication...")
        
        protected_endpoints = [
            "/referrals/profile",
            "/referrals/info", 
            "/referrals/rewards",
            "/referrals/generate-code"
        ]
        
        for endpoint in protected_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            # Should return 401 or 403 for unauthenticated requests
            assert response.status_code in [401, 403, 422], f"Endpoint {endpoint} should require auth, got {response.status_code}"
        
        logger.info("✅ Protected endpoints correctly require authentication")
    
    def print_api_summary(self):
        """Print summary of available API endpoints"""
        logger.info("📋 API Endpoint Summary:")
        
        try:
            response = self.session.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                paths = schema.get("paths", {})
                
                referral_endpoints = [(path, methods) for path, methods in paths.items() if "/referrals/" in path]
                
                logger.info("🔗 Referral System Endpoints:")
                for path, methods in referral_endpoints:
                    method_list = ", ".join(methods.keys())
                    logger.info(f"  {method_list} {path}")
                
        except Exception as e:
            logger.warning(f"Could not retrieve API summary: {e}")


def main():
    """Run the API endpoint tests"""
    tester = ReferralAPITester()
    
    # Print API summary first
    tester.print_api_summary()
    
    # Run all tests
    tester.test_all_endpoints()
    tester.test_protected_endpoints_require_auth()


if __name__ == "__main__":
    main()
