import { loadStripe } from '@stripe/stripe-js';

// Initialize Stripe with publishable key - handle missing env var gracefully
const stripePublishableKey = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;

let stripePromise = null;

if (stripePublishableKey) {
  stripePromise = loadStripe(stripePublishableKey);
} else {
  console.warn('⚠️ Stripe publishable key not found. Payment features will be disabled.');
  // Return a mock promise that resolves to null
  stripePromise = Promise.resolve(null);
}

export default stripePromise;
