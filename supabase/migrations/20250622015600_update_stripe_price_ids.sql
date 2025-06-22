-- Update subscription plans with real Stripe Price IDs
-- Migration: Add real Stripe Price ID for Standard plan

UPDATE subscription_plans 
SET stripe_price_id = 'price_1RchcvGKwE0ADhm7uSACGHdG'
WHERE plan_name = 'standard';

-- Verify the update
SELECT plan_name, price_monthly, stripe_price_id 
FROM subscription_plans 
WHERE plan_name = 'standard';
