import React from 'react';
import { useSubscription } from '../hooks/useSubscription';
import { createPortalSession } from '../services/paymentService';

export default function SubscriptionStatus() {
  const { 
    subscription, 
    hasActiveSubscription, 
    isTrialing, 
    isPastDue, 
    loading, 
    error,
    refetch 
  } = useSubscription();

  const handleManageSubscription = async () => {
    try {
      const { portal_url } = await createPortalSession(
        window.location.origin
      );
      window.open(portal_url, '_blank');
    } catch (error) {
      console.error('Error opening customer portal:', error);
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 rounded-lg border border-red-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-red-800">Subscription Error</p>
            <p className="text-xs text-red-600">Unable to load subscription status</p>
          </div>
          <button
            onClick={refetch}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Format next billing date
  const formatDate = (dateString) => {
    if (!dateString) return null;
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return null;
    }
  };

  const nextBillingDate = subscription?.current_period_end 
    ? formatDate(subscription.current_period_end)
    : null;

  if (hasActiveSubscription) {
    return (
      <div className="p-4 bg-green-50 rounded-lg border border-green-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-semibold text-green-800">
                {isTrialing ? 'Trial Active' : 'Pro Plan Active'}
              </span>
            </div>
            
            <p className="text-xs text-green-700 mb-2">
              {subscription?.plan_tier || 'Standard'} • Unlimited messages
            </p>
            
            {nextBillingDate && (
              <p className="text-xs text-green-600">
                {isTrialing ? 'Trial ends' : 'Next billing'}: {nextBillingDate}
              </p>
            )}
            
            {subscription?.cancel_at_period_end && (
              <p className="text-xs text-orange-600 mt-1">
                ⚠️ Cancels at period end
              </p>
            )}
          </div>
          
          <button
            onClick={handleManageSubscription}
            className="text-xs text-green-700 hover:text-green-900 font-medium border border-green-300 hover:border-green-400 px-2 py-1 rounded transition-colors"
          >
            Manage
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
            <span className="text-sm font-semibold text-yellow-800">
              {isPastDue ? 'Payment Past Due' : 'Free Plan'}
            </span>
          </div>
          
          <p className="text-xs text-yellow-700 mb-2">
            {isPastDue 
              ? 'Please update your payment method' 
              : 'Limited messages • Upgrade for unlimited access'
            }
          </p>
          
          {subscription?.subscription_status && (
            <p className="text-xs text-yellow-600 capitalize">
              Status: {subscription.subscription_status}
            </p>
          )}
        </div>
        
        {subscription?.stripe_customer_id && (
          <button
            onClick={handleManageSubscription}
            className="text-xs text-yellow-700 hover:text-yellow-900 font-medium border border-yellow-300 hover:border-yellow-400 px-2 py-1 rounded transition-colors"
          >
            {isPastDue ? 'Update Payment' : 'Manage'}
          </button>
        )}
      </div>
    </div>
  );
}
