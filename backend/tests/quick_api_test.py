"""
Quick test to validate the fixed referral validation endpoint
"""

import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fixed_endpoint():
    """Test the fixed referral validation endpoint"""
    logger.info("🧪 Testing Fixed Referral Validation Endpoint...")
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Valid format but non-existent code (should return 200 with valid=false)
    logger.info("Test 1: Valid format, non-existent code...")
    response = client.post(
        "/referrals/validate-code",
        json={"referral_code": "ABC123"}
    )
    
    logger.info(f"Response: {response.status_code} - {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["valid"] is False, "Non-existent code should be invalid"
    logger.info("✅ Test 1 passed")
    
    # Test 2: Invalid format (too short) - should return 422
    logger.info("Test 2: Invalid format (too short)...")
    response = client.post(
        "/referrals/validate-code",
        json={"referral_code": "ABC"}
    )
    
    logger.info(f"Response: {response.status_code} - {response.text}")
    assert response.status_code == 422, f"Expected 422 for invalid format, got {response.status_code}"
    logger.info("✅ Test 2 passed")
    
    # Test 3: Invalid format (too long) - should return 422
    logger.info("Test 3: Invalid format (too long)...")
    response = client.post(
        "/referrals/validate-code",
        json={"referral_code": "ABCDEFG"}
    )
    
    logger.info(f"Response: {response.status_code} - {response.text}")
    assert response.status_code == 422, f"Expected 422 for invalid format, got {response.status_code}"
    logger.info("✅ Test 3 passed")
    
    # Test 4: Empty code - should return 422
    logger.info("Test 4: Empty code...")
    response = client.post(
        "/referrals/validate-code",
        json={"referral_code": ""}
    )
    
    logger.info(f"Response: {response.status_code} - {response.text}")
    assert response.status_code == 422, f"Expected 422 for empty code, got {response.status_code}"
    logger.info("✅ Test 4 passed")
    
    logger.info("🎉 All tests passed! The 422 error issue has been resolved!")

if __name__ == "__main__":
    test_fixed_endpoint()
