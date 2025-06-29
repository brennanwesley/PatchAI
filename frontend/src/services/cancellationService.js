import { supabase } from '../supabaseClient';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

/**
 * Request subscription cancellation (logs intent, doesn't actually cancel)
 */
export async function requestSubscriptionCancellation(reason = null) {
  try {
    console.log('🚫 Requesting subscription cancellation...');
    
    // Check authentication
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.error('❌ No active session found');
      throw new Error('Not authenticated - please log in again');
    }
    
    console.log('✅ Session found, user:', session.user?.email);
    
    const requestBody = {
      reason: reason
    };
    
    console.log('📤 Cancellation request details:');
    console.log('  URL:', `${API_BASE_URL}/payments/request-cancellation`);
    console.log('  Body:', requestBody);

    const response = await fetch(`${API_BASE_URL}/payments/request-cancellation`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    console.log('📥 Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Response error:', errorText);
      
      // Provide specific error messages based on status code
      if (response.status === 401 || response.status === 403) {
        throw new Error('Authentication failed - please log out and log back in');
      } else if (response.status === 404) {
        throw new Error('Cancellation service not found - please contact support');
      } else if (response.status >= 500) {
        throw new Error('Server error - please try again later');
      } else {
        throw new Error(`Cancellation request failed (${response.status}): ${errorText}`);
      }
    }

    const result = await response.json();
    console.log('✅ Cancellation request response:', result);
    return result;
    
  } catch (error) {
    console.error('💥 Cancellation request error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    });
    
    // Re-throw with more user-friendly message if needed
    if (error.message.includes('fetch')) {
      throw new Error('Network error - please check your connection and try again');
    }
    
    throw error;
  }
}
