import { useState } from 'react';
import { createPortalSession } from '@/services/paymentService';
import { useSubscription } from '@/hooks/useSubscription';

export default function SubscriptionStatus() {
  const { subscription, hasActiveSubscription, isTrialing, isPastDue, loading } = useSubscription();
  const [portalLoading, setPortalLoading] = useState(false);

  const handleManageSubscription = async () => {
    try {
      setPortalLoading(true);
      const { portal_url } = await createPortalSession(window.location.href);
      window.location.href = portal_url;
    } catch (error) {
      console.error('Error opening customer portal:', error);
    } finally {
      setPortalLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!hasActiveSubscription && !isTrialing) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="text-sm font-medium text-yellow-800">No Active Subscription</p>
            <p className="text-xs text-yellow-700">Upgrade to continue using PatchAI</p>
          </div>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    if (hasActiveSubscription) return 'green';
    if (isTrialing) return 'blue';
    if (isPastDue) return 'red';
    return 'gray';
  };

  const getStatusText = () => {
    if (hasActiveSubscription) return 'Active';
    if (isTrialing) return 'Trial';
    if (isPastDue) return 'Past Due';
    return 'Inactive';
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center mb-1">
            <div className={`w-2 h-2 rounded-full mr-2 bg-${statusColor}-500`}></div>
            <p className="text-sm font-medium text-gray-900">Standard Plan</p>
            <span className={`ml-2 px-2 py-1 text-xs rounded-full bg-${statusColor}-100 text-${statusColor}-800`}>
              {statusText}
            </span>
          </div>
          <p className="text-xs text-gray-500">
            {subscription?.subscription?.current_period_end && (
              `Next billing: ${new Date(subscription.subscription.current_period_end).toLocaleDateString()}`
            )}
          </p>
        </div>
        
        <button
          onClick={handleManageSubscription}
          disabled={portalLoading}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
        >
          {portalLoading ? 'Loading...' : 'Manage'}
        </button>
      </div>
    </div>
  );
}
