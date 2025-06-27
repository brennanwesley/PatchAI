// Test script to validate referral system integration
// This script tests the frontend referral functionality

const testReferralIntegration = async () => {
  console.log('🧪 Testing Referral System Integration...');
  
  // Test 1: Environment Variables
  console.log('\n1. Testing Environment Variables:');
  const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'https://patchai-backend.onrender.com';
  console.log(`   API_URL: ${API_URL}`);
  
  // Test 2: Backend Connectivity
  console.log('\n2. Testing Backend Connectivity:');
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      console.log('   ✅ Backend is reachable');
    } else {
      console.log(`   ❌ Backend returned status: ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Backend connection failed: ${error.message}`);
  }
  
  // Test 3: Referral Code Validation Endpoint
  console.log('\n3. Testing Referral Code Validation:');
  try {
    const response = await fetch(`${API_URL}/referrals/validate-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ referral_code: 'TEST12' }),
    });
    
    const data = await response.json();
    console.log(`   Status: ${response.status}`);
    console.log(`   Response:`, data);
    
    if (response.status === 200 || response.status === 422) {
      console.log('   ✅ Validation endpoint is working');
    } else {
      console.log('   ❌ Unexpected response from validation endpoint');
    }
  } catch (error) {
    console.log(`   ❌ Validation endpoint test failed: ${error.message}`);
  }
  
  // Test 4: Component Import Test
  console.log('\n4. Testing Component Imports:');
  try {
    // Test if our components can be imported without errors
    const Profile = require('./components/Profile.js');
    console.log('   ✅ Profile component imports successfully');
  } catch (error) {
    console.log(`   ❌ Profile component import failed: ${error.message}`);
  }
  
  console.log('\n🎯 Referral Integration Test Complete!');
};

// Export for use in other files
export default testReferralIntegration;

// Auto-run if this file is executed directly
if (typeof window !== 'undefined') {
  // Browser environment
  window.testReferralIntegration = testReferralIntegration;
  console.log('Referral integration test function available as window.testReferralIntegration()');
}
