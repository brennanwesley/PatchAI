// Debug script to test Profile modal functionality
console.log('=== PROFILE MODAL DEBUG ===');

// Check if Profile component exists
import('./components/Profile.js').then(module => {
  console.log('✅ Profile component loaded successfully:', module.default);
}).catch(error => {
  console.error('❌ Profile component failed to load:', error);
});

// Check if Sidebar component has proper state management
import('./components/Sidebar.js').then(module => {
  console.log('✅ Sidebar component loaded successfully:', module.default);
}).catch(error => {
  console.error('❌ Sidebar component failed to load:', error);
});

// Test localStorage data
console.log('📊 LocalStorage data:');
console.log('- customer_name:', localStorage.getItem('customer_name'));
console.log('- userEmail:', localStorage.getItem('userEmail'));

// Test Supabase session
import('./supabaseClient.js').then(({ supabase }) => {
  supabase.auth.getSession().then(({ data: { session }, error }) => {
    if (error) {
      console.error('❌ Supabase session error:', error);
    } else if (session) {
      console.log('✅ Supabase session active:', session.user.email);
    } else {
      console.log('⚠️ No active Supabase session');
    }
  });
}).catch(error => {
  console.error('❌ Supabase client error:', error);
});

// Test API connectivity
const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'https://patchai-backend.onrender.com';
console.log('🌐 API URL:', API_URL);

fetch(`${API_URL}/health`)
  .then(response => response.json())
  .then(data => console.log('✅ Backend health check:', data))
  .catch(error => console.error('❌ Backend connectivity error:', error));
