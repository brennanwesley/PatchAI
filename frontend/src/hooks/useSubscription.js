import { useState, useEffect } from 'react';
import { getSubscriptionStatus } from '@/services/paymentService';
import { useAuth } from '@/contexts/AuthContext';

export function useSubscription() {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSubscription = async () => {
    if (!user) {
      setSubscription(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await getSubscriptionStatus();
      setSubscription(data);
    } catch (err) {
      console.error('Error fetching subscription:', err);
      setError(err.message);
      setSubscription(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscription();
  }, [user]);

  const refetch = () => {
    fetchSubscription();
  };

  // Helper functions
  const hasActiveSubscription = subscription?.has_active_subscription || false;
  const isTrialing = subscription?.subscription?.status === 'trialing';
  const isPastDue = subscription?.subscription?.status === 'past_due';
  const needsPayment = !hasActiveSubscription && !isTrialing;

  return {
    subscription,
    loading,
    error,
    refetch,
    hasActiveSubscription,
    isTrialing,
    isPastDue,
    needsPayment,
  };
}
