import React, { useState } from 'react';
import { useSubscription } from '../hooks/useSubscription';
import { createPortalSession, syncSubscriptionManually } from '../services/paymentService';

export default function SubscriptionStatus() {
  const { 
    subscription, 
    hasActiveSubscription, 
    isLoading, 
    error,
    refetch 
  } = useSubscription();
  
  const [isCreatingPortal, setIsCreatingPortal] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const handleManageSubscription = async () => {
    try {
      setIsCreatingPortal(true);
      const { url } = await createPortalSession(window.location.href);
      window.location.href = url;
    } catch (error) {
      console.error('Error opening customer portal:', error);
      alert('Failed to open subscription management. Please try again.');
    } finally {
      setIsCreatingPortal(false);
    }
  };

  const handleSyncSubscription = async () => {
    try {
      setIsSyncing(true);
      console.log('🔄 Manually syncing subscription from Stripe...');
      const result = await syncSubscriptionManually();
      console.log('✅ Sync result:', result);
      
      // Refresh subscription data after sync
      await refetch();
      
      if (result.success) {
        alert('Subscription synced successfully!');
      } else {
        alert('Sync completed, but no changes detected.');
      }
    } catch (error) {
      console.error('❌ Error syncing subscription:', error);
      alert('Failed to sync subscription. Please try again or contact support.');
    } finally {
      setIsSyncing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="animate-pulse flex space-x-4">
          <div className="rounded-full bg-gray-200 h-10 w-10"></div>
          <div className="flex-1 space-y-2 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-red-800">Subscription Error</h3>
            <p className="text-sm text-red-600 mt-1">
              Unable to load subscription status
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleSyncSubscription}
              disabled={isSyncing}
              className="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
            >
              {isSyncing ? '⏳ Syncing...' : '🔄 Sync'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!hasActiveSubscription) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-yellow-800">No Active Subscription</h3>
            <p className="text-sm text-yellow-600 mt-1">
              Subscribe to access premium features
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleSyncSubscription}
              disabled={isSyncing}
              className="inline-flex items-center px-3 py-1.5 border border-yellow-300 text-xs font-medium rounded text-yellow-700 bg-white hover:bg-yellow-50 disabled:opacity-50"
              title="Sync subscription status from Stripe"
            >
              {isSyncing ? '⏳ Syncing...' : '🔄 Sync'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50 border-green-200';
      case 'trialing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'past_due': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'canceled': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor(subscription?.status)}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-current rounded-full"></div>
          <h3 className="text-sm font-medium">
            {subscription?.plan_tier?.charAt(0).toUpperCase() + subscription?.plan_tier?.slice(1)} Plan
          </h3>
        </div>
        <span className="text-xs font-medium px-2 py-1 rounded-full bg-current bg-opacity-20">
          {subscription?.status?.toUpperCase()}
        </span>
      </div>
      
      {subscription?.next_billing_date && (
        <p className="text-xs mb-3">
          Next billing: {formatDate(subscription.next_billing_date)}
        </p>
      )}
      
      {subscription?.cancel_at_period_end && (
        <p className="text-xs text-orange-600 mb-3">
          ⚠️ Subscription will cancel at period end
        </p>
      )}
      
      <div className="flex space-x-2">
        <button
          onClick={handleManageSubscription}
          disabled={isCreatingPortal}
          className="flex-1 inline-flex items-center justify-center px-3 py-1.5 border border-current text-xs font-medium rounded hover:bg-current hover:bg-opacity-10 disabled:opacity-50"
        >
          {isCreatingPortal ? '⏳ Loading...' : '⚙️ Manage'}
        </button>
        
        <button
          onClick={handleSyncSubscription}
          disabled={isSyncing}
          className="inline-flex items-center px-3 py-1.5 border border-current text-xs font-medium rounded hover:bg-current hover:bg-opacity-10 disabled:opacity-50"
          title="Sync subscription status from Stripe"
        >
          {isSyncing ? '⏳' : '🔄'}
        </button>
      </div>
    </div>
  );
}
