Starting subscription sync from UI...
paymentService.js:98 🔄 Starting subscription sync...
paymentService.js:99 📍 API Base URL: https://patchai-backend.onrender.com
paymentService.js:108 ✅ Session found, user: brennan.testuser6@email.com
paymentService.js:112 🎯 Target email for sync: brennan.testuser6@email.com
paymentService.js:123 📤 Request details:
paymentService.js:124   URL: https://patchai-backend.onrender.com/payments/sync-subscription
paymentService.js:125   Body: {email: 'brennan.testuser6@email.com'}
paymentService.js:126   Auth token length: 881
paymentService.js:128 
            
            
           POST https://patchai-backend.onrender.com/payments/sync-subscription 500 (Internal Server Error)
(anonymous) @ paymentService.js:128
await in (anonymous)
m @ SubscriptionStatus.jsx:29
Lc @ react-dom-client.production.js:11858
(anonymous) @ react-dom-client.production.js:12410
Lt @ react-dom-client.production.js:1470
Hc @ react-dom-client.production.js:11996
ah @ react-dom-client.production.js:14699
rh @ react-dom-client.production.js:14667Understand this error
paymentService.js:137 📥 Response status: 500
paymentService.js:138 📥 Response headers: {content-length: '135', content-type: 'application/json'}
paymentService.js:142 ❌ Response error: {"success":false,"message":"An unexpected error occurred. Please try again or contact support.","error_code":"UNEXPECTED_ERROR","timestamp":"2025-06-29T23:49:42.369689"}
(anonymous) @ paymentService.js:142
await in (anonymous)
m @ SubscriptionStatus.jsx:29
Lc @ react-dom-client.production.js:11858
(anonymous) @ react-dom-client.production.js:12410
Lt @ react-dom-client.production.js:1470
Hc @ react-dom-client.production.js:11996
ah @ react-dom-client.production.js:14699
rh @ react-dom-client.production.js:14667Understand this error
paymentService.js:161 💥 Sync error details: {message: 'Server error - please try again later', stack: 'Error: Server error - please try again later\n    a….patchai.app/static/js/main.4cf288ad.js:2:590912)', name: 'Error'}
(anonymous) @ paymentService.js:161
await in (anonymous)
m @ SubscriptionStatus.jsx:29
Lc @ react-dom-client.production.js:11858
(anonymous) @ react-dom-client.production.js:12410
Lt @ react-dom-client.production.js:1470
Hc @ react-dom-client.production.js:11996
ah @ react-dom-client.production.js:14699
rh @ react-dom-client.production.js:14667Understand this error
SubscriptionStatus.jsx:50 ❌ Sync failed: 