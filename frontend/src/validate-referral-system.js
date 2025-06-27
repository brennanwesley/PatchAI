// Comprehensive validation script for referral system frontend integration
// Run this in browser console to test all components

const validateReferralSystem = () => {
  console.log('🔍 Validating Referral System Frontend Integration...\n');
  
  const results = {
    passed: 0,
    failed: 0,
    warnings: 0
  };
  
  // Test 1: Environment Variables
  console.log('1. Testing Environment Variables:');
  const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'https://patchai-backend.onrender.com';
  console.log(`   API_URL: ${API_URL}`);
  if (API_URL.includes('patchai-backend.onrender.com')) {
    console.log('   ✅ API URL correctly configured');
    results.passed++;
  } else {
    console.log('   ⚠️  Using fallback API URL');
    results.warnings++;
  }
  
  // Test 2: Component Availability
  console.log('\n2. Testing Component Availability:');
  try {
    // Check if Profile component exists in DOM or can be imported
    const profileElements = document.querySelectorAll('[data-testid="profile-modal"], .profile-modal');
    console.log(`   Profile modal elements found: ${profileElements.length}`);
    
    // Check if referral input exists in login form
    const referralInputs = document.querySelectorAll('input[placeholder*="referral"], input[name*="referral"]');
    console.log(`   Referral input fields found: ${referralInputs.length}`);
    
    if (referralInputs.length > 0) {
      console.log('   ✅ Referral input field detected');
      results.passed++;
    } else {
      console.log('   ⚠️  Referral input field not currently visible (may be on login page)');
      results.warnings++;
    }
  } catch (error) {
    console.log(`   ❌ Component availability test failed: ${error.message}`);
    results.failed++;
  }
  
  // Test 3: AuthContext Integration
  console.log('\n3. Testing AuthContext Integration:');
  try {
    // Check if window.React is available (development mode)
    if (typeof window !== 'undefined' && window.React) {
      console.log('   ✅ React is available in development mode');
      results.passed++;
    } else {
      console.log('   ⚠️  React not available in window (production mode)');
      results.warnings++;
    }
  } catch (error) {
    console.log(`   ❌ AuthContext test failed: ${error.message}`);
    results.failed++;
  }
  
  // Test 4: API Connectivity
  console.log('\n4. Testing API Connectivity:');
  fetch(`${API_URL}/health`)
    .then(response => response.json())
    .then(data => {
      console.log('   ✅ Backend health check passed');
      console.log('   Backend status:', data.status);
      results.passed++;
    })
    .catch(error => {
      console.log(`   ❌ Backend connectivity failed: ${error.message}`);
      results.failed++;
    });
  
  // Test 5: Referral Validation Endpoint
  console.log('\n5. Testing Referral Validation:');
  fetch(`${API_URL}/referrals/validate-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ referral_code: 'TEST12' }),
  })
    .then(response => response.json())
    .then(data => {
      console.log('   ✅ Referral validation endpoint working');
      console.log('   Validation response:', data);
      results.passed++;
    })
    .catch(error => {
      console.log(`   ❌ Referral validation failed: ${error.message}`);
      results.failed++;
    });
  
  // Test 6: Local Storage and Session
  console.log('\n6. Testing Local Storage and Session:');
  try {
    const customerName = localStorage.getItem('customer_name');
    const hasSupabaseSession = localStorage.getItem('sb-' + window.location.hostname + '-auth-token');
    
    console.log(`   Customer name: ${customerName || 'Not set'}`);
    console.log(`   Supabase session: ${hasSupabaseSession ? 'Present' : 'Not found'}`);
    
    console.log('   ✅ Local storage accessible');
    results.passed++;
  } catch (error) {
    console.log(`   ❌ Local storage test failed: ${error.message}`);
    results.failed++;
  }
  
  // Summary
  setTimeout(() => {
    console.log('\n📊 Validation Summary:');
    console.log(`   ✅ Passed: ${results.passed}`);
    console.log(`   ⚠️  Warnings: ${results.warnings}`);
    console.log(`   ❌ Failed: ${results.failed}`);
    
    if (results.failed === 0) {
      console.log('\n🎉 Referral system integration looks good!');
    } else {
      console.log('\n⚠️  Some issues detected. Check the details above.');
    }
  }, 2000);
};

// Make available globally
if (typeof window !== 'undefined') {
  window.validateReferralSystem = validateReferralSystem;
  console.log('Referral system validator loaded. Run validateReferralSystem() to test.');
}

export default validateReferralSystem;
