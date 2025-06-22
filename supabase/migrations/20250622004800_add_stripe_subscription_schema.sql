-- PatchAI Stripe Subscription Schema
-- Phase 1: Database Schema Design for Paywall Integration
-- Created: 2025-06-22 00:48:00 UTC
-- Objective: Add subscription tables and extend user_profiles for Stripe integration

-- ============================================================================
-- STEP 1: Create subscription_plans table
-- ============================================================================

CREATE TABLE public.subscription_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id TEXT UNIQUE NOT NULL, -- e.g., 'free', 'standard', 'premium'
  plan_name TEXT NOT NULL, -- e.g., 'Free Plan', 'Standard Plan', 'Premium Plan'
  stripe_price_id TEXT, -- Stripe Price ID for paid plans (NULL for free)
  monthly_price DECIMAL(10,2) NOT NULL DEFAULT 0.00, -- Monthly price in USD
  message_limit INTEGER NOT NULL DEFAULT 10, -- Messages per day limit
  feature_flags JSONB DEFAULT '{}', -- Additional features as JSON
  is_active BOOLEAN DEFAULT true, -- Whether plan is available for new subscriptions
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS for subscription_plans
ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Anyone can read active subscription plans (for pricing page)
CREATE POLICY "Anyone can view active subscription plans"
  ON public.subscription_plans FOR SELECT
  USING (is_active = true);

-- Only service role can modify subscription plans
CREATE POLICY "Service role can manage subscription plans"
  ON public.subscription_plans FOR ALL
  USING (auth.role() = 'service_role');

-- Trigger to update updated_at
CREATE TRIGGER update_subscription_plans_updated_at
  BEFORE UPDATE ON public.subscription_plans
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 2: Create user_subscriptions table
-- ============================================================================

CREATE TABLE public.user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES public.subscription_plans(id),
  stripe_subscription_id TEXT, -- Stripe Subscription ID (NULL for free plans)
  status TEXT NOT NULL CHECK (status IN ('active', 'trialing', 'canceled', 'past_due', 'incomplete', 'unpaid')),
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT false,
  canceled_at TIMESTAMPTZ,
  trial_start TIMESTAMPTZ,
  trial_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Ensure one active subscription per user
  CONSTRAINT unique_active_subscription_per_user 
    EXCLUDE (user_id WITH =) WHERE (status IN ('active', 'trialing'))
);

-- Enable RLS for user_subscriptions
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_subscriptions
CREATE POLICY "Users can view their own subscriptions"
  ON public.user_subscriptions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all subscriptions"
  ON public.user_subscriptions FOR ALL
  USING (auth.role() = 'service_role');

-- Trigger to update updated_at
CREATE TRIGGER update_user_subscriptions_updated_at
  BEFORE UPDATE ON public.user_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 3: Create payment_transactions table
-- ============================================================================

CREATE TABLE public.payment_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_payment_intent_id TEXT UNIQUE NOT NULL,
  stripe_invoice_id TEXT,
  subscription_id UUID REFERENCES public.user_subscriptions(id),
  amount_paid DECIMAL(10,2) NOT NULL, -- Amount in USD
  currency TEXT DEFAULT 'usd',
  status TEXT NOT NULL CHECK (status IN ('succeeded', 'failed', 'pending', 'canceled', 'refunded')),
  payment_method TEXT, -- e.g., 'card', 'bank_transfer'
  failure_reason TEXT, -- Stripe failure reason if payment failed
  metadata JSONB DEFAULT '{}', -- Additional Stripe metadata
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS for payment_transactions
ALTER TABLE public.payment_transactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for payment_transactions
CREATE POLICY "Users can view their own payment transactions"
  ON public.payment_transactions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all payment transactions"
  ON public.payment_transactions FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================================
-- STEP 4: Extend user_profiles table with Stripe fields
-- ============================================================================

-- Add Stripe-related columns to existing user_profiles table
ALTER TABLE public.user_profiles 
ADD COLUMN stripe_customer_id TEXT UNIQUE,
ADD COLUMN subscription_status TEXT DEFAULT 'inactive' CHECK (subscription_status IN ('active', 'trialing', 'canceled', 'past_due', 'incomplete', 'unpaid', 'inactive')),
ADD COLUMN plan_tier TEXT DEFAULT 'none',
ADD COLUMN last_payment_at TIMESTAMPTZ;

-- ============================================================================
-- STEP 5: Create indexes for performance
-- ============================================================================

-- Subscription plans indexes
CREATE INDEX idx_subscription_plans_plan_id ON public.subscription_plans(plan_id);
CREATE INDEX idx_subscription_plans_stripe_price_id ON public.subscription_plans(stripe_price_id);
CREATE INDEX idx_subscription_plans_active ON public.subscription_plans(is_active);

-- User subscriptions indexes
CREATE INDEX idx_user_subscriptions_user_id ON public.user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_stripe_id ON public.user_subscriptions(stripe_subscription_id);
CREATE INDEX idx_user_subscriptions_status ON public.user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_period_end ON public.user_subscriptions(current_period_end);

-- Payment transactions indexes
CREATE INDEX idx_payment_transactions_user_id ON public.payment_transactions(user_id);
CREATE INDEX idx_payment_transactions_stripe_payment_id ON public.payment_transactions(stripe_payment_intent_id);
CREATE INDEX idx_payment_transactions_status ON public.payment_transactions(status);
CREATE INDEX idx_payment_transactions_created_at ON public.payment_transactions(created_at DESC);

-- User profiles Stripe indexes
CREATE INDEX idx_user_profiles_stripe_customer_id ON public.user_profiles(stripe_customer_id);
CREATE INDEX idx_user_profiles_subscription_status ON public.user_profiles(subscription_status);
CREATE INDEX idx_user_profiles_plan_tier ON public.user_profiles(plan_tier);

-- ============================================================================
-- STEP 6: Insert initial subscription plans
-- ============================================================================

-- Insert default subscription plans
INSERT INTO public.subscription_plans (plan_id, plan_name, stripe_price_id, monthly_price, message_limit, feature_flags, is_active) VALUES
('standard', 'Standard Plan', NULL, 19.99, 1000, '{"basic_chat": true, "priority_support": false, "advanced_features": false}', true),
('premium', 'Premium Plan', NULL, 49.99, 5000, '{"basic_chat": true, "priority_support": true, "advanced_features": true, "unlimited_history": true}', true);

-- Note: stripe_price_id will be updated when Stripe products are created in Phase 2

-- ============================================================================
-- STEP 7: Create helper functions for subscription management
-- ============================================================================

-- Function to get user's current active subscription
CREATE OR REPLACE FUNCTION public.get_user_active_subscription(user_uuid UUID)
RETURNS TABLE (
  subscription_id UUID,
  plan_id TEXT,
  plan_name TEXT,
  status TEXT,
  message_limit INTEGER,
  current_period_end TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    us.id as subscription_id,
    sp.plan_id,
    sp.plan_name,
    us.status,
    sp.message_limit,
    us.current_period_end
  FROM public.user_subscriptions us
  JOIN public.subscription_plans sp ON us.plan_id = sp.id
  WHERE us.user_id = user_uuid 
    AND us.status IN ('active', 'trialing')
  ORDER BY us.created_at DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has active subscription
CREATE OR REPLACE FUNCTION public.user_has_active_subscription(user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.user_subscriptions 
    WHERE user_id = user_uuid 
      AND status IN ('active', 'trialing')
      AND (current_period_end IS NULL OR current_period_end > NOW())
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- STEP 8: Create audit triggers for subscription changes
-- ============================================================================

-- Function to sync user_profiles with subscription changes
CREATE OR REPLACE FUNCTION public.sync_user_subscription_status()
RETURNS TRIGGER AS $$
BEGIN
  -- Update user_profiles with latest subscription info
  UPDATE public.user_profiles 
  SET 
    subscription_status = NEW.status,
    plan_tier = (SELECT plan_id FROM public.subscription_plans WHERE id = NEW.plan_id),
    updated_at = NOW()
  WHERE id = NEW.user_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to sync user_profiles when subscription changes
CREATE TRIGGER sync_user_subscription_status_trigger
  AFTER INSERT OR UPDATE ON public.user_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION public.sync_user_subscription_status();

-- Function to update last_payment_at when payment succeeds
CREATE OR REPLACE FUNCTION public.update_last_payment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  -- Only update for successful payments
  IF NEW.status = 'succeeded' THEN
    UPDATE public.user_profiles 
    SET 
      last_payment_at = NEW.created_at,
      updated_at = NOW()
    WHERE id = NEW.user_id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update last_payment_at on successful payments
CREATE TRIGGER update_last_payment_timestamp_trigger
  AFTER INSERT OR UPDATE ON public.payment_transactions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_last_payment_timestamp();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Summary of changes:
-- ✅ Created subscription_plans table with Stripe integration fields
-- ✅ Created user_subscriptions table to track user subscription status
-- ✅ Created payment_transactions table for auditable payment history
-- ✅ Extended user_profiles with Stripe customer ID and subscription fields
-- ✅ Added comprehensive indexes for performance
-- ✅ Inserted initial Standard and Premium subscription plans
-- ✅ Created helper functions for subscription queries
-- ✅ Added audit triggers to keep user_profiles in sync
-- ✅ Implemented Row Level Security for all new tables
-- 
-- Next Phase: Backend Integration with Stripe webhooks and middleware
