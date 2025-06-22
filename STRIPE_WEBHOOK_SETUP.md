# Stripe Webhook Configuration Guide

## Problem
After users complete Stripe payments, their subscription status doesn't update automatically in the PatchAI system, causing the paywall to persist even after successful payment.

## Root Cause
The Stripe webhook endpoint is not configured in the Stripe Dashboard, so subscription lifecycle events (payment success, subscription creation, etc.) are not being sent to our backend.

## Solution: Configure Stripe Webhook

### Step 1: Access Stripe Dashboard
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Developers** → **Webhooks**
3. Or directly visit: https://dashboard.stripe.com/webhooks

### Step 2: Add Webhook Endpoint
1. Click **"Add endpoint"**
2. **Endpoint URL**: `https://patchai-backend.onrender.com/payments/webhook`
3. **Description**: "PatchAI Subscription Events"

### Step 3: Select Events
Click **"Select events"** and choose these events:
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

### Step 4: Save and Get Secret
1. Click **"Add endpoint"**
2. Click on the newly created webhook endpoint
3. Copy the **"Signing secret"** (starts with `whsec_...`)

### Step 5: Update Backend Environment
Add the webhook secret to your backend environment variables:
```
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
```

## Testing the Setup

### Manual Test (Current Users)
For users who already paid but don't have active subscriptions:
```bash
cd backend
python scripts/manual_subscription_fix.py user@example.com
```

### Webhook Test
```bash
cd backend
python scripts/test_webhook.py
```

### End-to-End Test
1. Create a new user account
2. Complete Stripe payment
3. Verify subscription status updates automatically
4. Confirm paywall disappears immediately

## Expected Flow After Configuration

1. **User completes payment** → Stripe processes payment
2. **Stripe sends webhook** → `customer.subscription.created` event
3. **Backend receives webhook** → Updates user_subscriptions and user_profiles tables
4. **Frontend detects success** → Refreshes subscription status via `?payment=success`
5. **UI updates immediately** → Paywall disappears, subscription status shows "Active"

## Troubleshooting

### Webhook Not Receiving Events
- Check webhook URL is exactly: `https://patchai-backend.onrender.com/payments/webhook`
- Verify events are selected correctly
- Check webhook secret is set in backend environment

### Subscription Still Not Active
- Run manual fix script for the specific user
- Check backend logs for webhook processing errors
- Verify user has completed payment in Stripe Dashboard

### Frontend Not Updating
- Check browser console for API errors
- Verify `?payment=success` parameter triggers refresh
- Test subscription status API endpoint directly

## Files Involved

**Backend:**
- `routes/payment_routes.py` - Subscription status API
- `core/stripe_webhooks.py` - Webhook event processing
- `scripts/manual_subscription_fix.py` - Manual fix for stuck users

**Frontend:**
- `App.js` - Payment success detection and subscription refresh
- `hooks/useSubscription.js` - Subscription status management
- `components/SubscriptionStatus.jsx` - UI display

## Security Notes
- Webhook signature verification is implemented
- All endpoints require JWT authentication
- Environment variables are properly secured
- Stripe secrets are not exposed in frontend code
