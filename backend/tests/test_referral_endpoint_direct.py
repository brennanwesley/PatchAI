"""
Direct test of referral validation endpoint to resolve 422 error
"""

import sys
import os
import asyncio
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_referral_validation_endpoint():
    """Test the referral validation endpoint directly"""
    logger.info("🧪 Testing Referral Validation Endpoint Directly...")
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Invalid referral code with form data
    logger.info("Testing with form data...")
    response = client.post(
        "/referrals/validate-code",
        data={"referral_code": "INVALID"}
    )
    
    logger.info(f"Form data response: {response.status_code} - {response.text}")
    
    # Test 2: Invalid referral code with JSON
    logger.info("Testing with JSON data...")
    response = client.post(
        "/referrals/validate-code",
        json={"referral_code": "INVALID"}
    )
    
    logger.info(f"JSON response: {response.status_code} - {response.text}")
    
    # Test 3: Query parameter
    logger.info("Testing with query parameter...")
    response = client.post(
        "/referrals/validate-code?referral_code=INVALID"
    )
    
    logger.info(f"Query param response: {response.status_code} - {response.text}")
    
    # Test 4: Check the actual endpoint signature
    logger.info("Checking OpenAPI schema...")
    response = client.get("/openapi.json")
    if response.status_code == 200:
        schema = response.json()
        validate_endpoint = schema.get("paths", {}).get("/referrals/validate-code", {})
        logger.info(f"Validate endpoint schema: {validate_endpoint}")
    
    logger.info("✅ Direct endpoint testing complete")

if __name__ == "__main__":
    test_referral_validation_endpoint()
