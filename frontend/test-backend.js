const https = require('https');

const testBackend = async () => {
  console.log('🧪 Testing Backend Connectivity...\n');
  
  // Test 1: Health check
  console.log('1. Testing Health Endpoint:');
  try {
    const healthResponse = await makeRequest('https://patchai-backend.onrender.com/health');
    console.log('   ✅ Health endpoint working');
    console.log('   Status:', healthResponse.status);
  } catch (error) {
    console.log('   ❌ Health endpoint failed:', error.message);
  }
  
  // Test 2: Referral validation endpoint
  console.log('\n2. Testing Referral Validation Endpoint:');
  try {
    const validationResponse = await makePostRequest(
      'https://patchai-backend.onrender.com/referrals/validate-code',
      { referral_code: 'TEST12' }
    );
    console.log('   ✅ Validation endpoint working');
    console.log('   Response:', validationResponse);
  } catch (error) {
    console.log('   ❌ Validation endpoint failed:', error.message);
  }
  
  console.log('\n🎯 Backend Test Complete!');
};

function makeRequest(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    }).on('error', reject);
  });
}

function makePostRequest(url, body) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(body);
    const urlObj = new URL(url);
    
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 443,
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

testBackend().catch(console.error);
