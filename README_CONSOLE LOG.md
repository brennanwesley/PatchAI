Starting subscription sync from UI...
paymentService.js:98 🔄 Starting subscription sync...
paymentService.js:99 📍 API Base URL: https://patchai-backend.onrender.com
paymentService.js:108 ✅ Session found, user: brennan.testuser1@email.com
paymentService.js:114 📤 Request details:
paymentService.js:115   URL: https://patchai-backend.onrender.com/payments/sync-subscription
paymentService.js:116   Body: {email: null}
paymentService.js:117   Auth token length: 881
/chat:1 Access to fetch at 'https://patchai-backend.onrender.com/payments/sync-subscription' from origin 'https://www.patchai.app' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.Understand this error
paymentService.js:119 
            
            
           POST https://patchai-backend.onrender.com/payments/sync-subscription net::ERR_FAILED 500 (Internal Server Error)
(anonymous) @ paymentService.js:119
await in (anonymous)
f @ SubscriptionStatus.jsx:35
Rc @ react-dom-client.production.js:11858
(anonymous) @ react-dom-client.production.js:12410
Rt @ react-dom-client.production.js:1470
Hc @ react-dom-client.production.js:11996
ah @ react-dom-client.production.js:14699
rh @ react-dom-client.production.js:14667Understand this error
paymentService.js:152 💥 Sync error details: {message: 'Failed to fetch', stack: 'TypeError: Failed to fetch\n    at https://www.patc….patchai.app/static/js/main.3494a9bf.js:2:581036)', name: 'TypeError'}
(anonymous) @ paymentService.js:152
await in (anonymous)
f @ SubscriptionStatus.jsx:35
Rc @ react-dom-client.production.js:11858
(anonymous) @ react-dom-client.production.js:12410
Rt @ react-dom-client.production.js:1470
Hc @ react-dom-client.production.js:11996
ah @ react-dom-client.production.js:14699
rh @ react-dom-client.production.js:14667Understand this error
SubscriptionStatus.jsx:56 ❌ Sync failed: Error: Network error - please check your connection and try again
    at paymentService.js:160:13
    at async f (SubscriptionStatus.jsx:35:13)