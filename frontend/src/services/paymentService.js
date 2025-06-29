import { supabase } from '../supabaseClient';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

/**
 * Get current user's subscription status
 */
export async function getSubscriptionStatus() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE_URL}/payments/subscription-status`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching subscription status:', error);
    throw error;
  }
}

/**
 * Create Stripe checkout session for subscription
 */
export async function createCheckoutSession(planId, successUrl, cancelUrl) {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE_URL}/payments/create-checkout-session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        plan_id: planId,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating checkout session:', error);
    throw error;
  }
}

/**
 * Create Stripe customer portal session for subscription management
 */
export async function createPortalSession(returnUrl) {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE_URL}/payments/create-portal-session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        return_url: returnUrl,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating portal session:', error);
    throw error;
  }
}

/**
 * Manually sync subscription status from Stripe (for debugging/admin)
 */
export async function syncSubscriptionManually(email = null) {
  try {
    console.log('🔄 Starting subscription sync...');
    console.log('📍 API Base URL:', API_BASE_URL);
    
    // Check authentication
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.error('❌ No active session found');
      throw new Error('Not authenticated - please log in again');
    }
    
    console.log('✅ Session found, user:', session.user?.email);
    
    // Use current user's email if no specific email provided
    const targetEmail = email || session.user?.email;
    console.log('🎯 Target email for sync:', targetEmail);
    
    if (!targetEmail) {
      console.error('❌ No email available for sync');
      throw new Error('No email available for subscription sync');
    }
    
    const requestBody = {
      email: targetEmail, // Use current user's email or provided email
    };
    
    console.log('📤 Request details:');
    console.log('  URL:', `${API_BASE_URL}/payments/sync-subscription`);
    console.log('  Body:', requestBody);
    console.log('  Auth token length:', session.access_token?.length || 0);

    const response = await fetch(`${API_BASE_URL}/payments/sync-subscription`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    console.log('📥 Response status:', response.status);
    console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: await response.text() };
      }
      
      console.error('❌ Sync failed:', {
        status: response.status,
        error: errorData
      });
      
      // Provide specific error messages based on status code and error data
      if (response.status === 401 || response.status === 403) {
        throw new Error('Please log out and log back in to refresh your session');
      } else if (response.status === 404) {
        throw new Error('User account not found - please contact support');
      } else if (response.status === 503) {
        throw new Error('Payment system temporarily unavailable - please try again in a few minutes');
      } else if (errorData.error_code === 'STRIPE_ERROR') {
        throw new Error('Unable to connect to payment system - please try again later');
      } else if (errorData.message) {
        throw new Error(errorData.message);
      } else {
        throw new Error(`Sync failed with status ${response.status} - please try again or contact support`);
      }
    }

    const result = await response.json();
    console.log('✅ Sync completed successfully:', {
      success: result.success,
      status: result.subscription_status,
      plan: result.plan_tier,
      message: result.message
    });
    
    return result;
    
  } catch (error) {
    console.error('💥 Sync error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    });
    
    // Re-throw with more user-friendly message if needed
    if (error.message.includes('fetch') || error.name === 'TypeError') {
      throw new Error('Network connection failed - please check your internet and try again');
    }
    
    throw error;
  }
}
