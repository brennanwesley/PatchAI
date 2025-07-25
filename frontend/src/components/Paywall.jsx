import React, { useState } from 'react';
import { createCheckoutSession, grantProvisionalAccess } from '../services/paymentService';
import stripePromise from '../lib/stripe';

export default function Paywall({ onClose }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpgrade = async () => {
    let provisionalAccessGranted = false;
    
    try {
      setLoading(true);
      setError(null);

      console.log('🚀 Starting provisional access upgrade flow...');
      
      // STEP 1: Grant immediate provisional Standard Plan access (24 hours)
      console.log('🎯 Granting provisional access...');
      await grantProvisionalAccess();
      provisionalAccessGranted = true;
      console.log('✅ Provisional access granted - user now has Standard Plan!');
      
      // STEP 2: Close paywall immediately (user gets instant access)
      console.log('🎉 Closing paywall - user can start using Standard features!');
      onClose(); // This gives immediate access to the app
      
      // STEP 3: Create checkout session for actual payment
      console.log('💳 Creating Stripe checkout session...');
      const { checkout_url } = await createCheckoutSession(
        'standard', // plan_id
        `${window.location.origin}/dashboard?payment=success`,
        `${window.location.origin}/dashboard?payment=cancelled`
      );

      // STEP 4: Redirect to Stripe Checkout (user already has access)
      console.log('🔄 Redirecting to Stripe for payment...');
      window.location.href = checkout_url;
      
    } catch (err) {
      console.error('💥 Error in provisional access upgrade flow:', err);
      
      // Enhanced error recovery based on what succeeded
      if (provisionalAccessGranted) {
        // Provisional access was granted but checkout failed
        console.log('⚠️ Provisional access granted but checkout failed - user still has 24hr access');
        setError(
          'You now have 24-hour Standard Plan access! Payment setup failed, but you can try upgrading again later or contact support.'
        );
        // Still close paywall since user has provisional access
        setTimeout(() => onClose(), 3000);
      } else {
        // Provisional access failed - user gets no access
        console.log('❌ Provisional access failed - user has no access');
        setError(
          `Upgrade failed: ${err.message}. Please try again or contact support if the problem persists.`
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Upgrade to Standard Plan</h2>
          <p className="text-gray-600">Get instant access + unlimited conversations and advanced features</p>
        </div>

        {/* Plan Details */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Standard Plan</h3>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">$4.99</div>
              <div className="text-sm text-gray-500">per month</div>
            </div>
          </div>
          
          <ul className="space-y-3">
            <li className="flex items-center text-sm text-gray-700">
              <svg className="w-4 h-4 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              1,000 messages per day
            </li>
            <li className="flex items-center text-sm text-gray-700">
              <svg className="w-4 h-4 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Full chat history
            </li>
            <li className="flex items-center text-sm text-gray-700">
              <svg className="w-4 h-4 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Advanced AI features
            </li>
            <li className="flex items-center text-sm text-gray-700">
              <svg className="w-4 h-4 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Cancel anytime
            </li>
          </ul>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex">
              <svg className="w-5 h-5 text-red-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              'Upgrade to Standard Plan'
            )}
          </button>
          
          <p className="text-xs text-gray-500 text-center">
            Secure payment powered by Stripe • Cancel anytime
          </p>
        </div>
      </div>
    </div>
  );
}
