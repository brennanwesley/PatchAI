"""
Stripe Configuration Module
Handles Stripe SDK initialization and configuration
"""

import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Stripe with secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe configuration constants
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

def get_stripe_config():
    """Get Stripe configuration for validation"""
    return {
        "api_key_configured": bool(stripe.api_key),
        "webhook_secret_configured": bool(STRIPE_WEBHOOK_SECRET),
        "api_key_prefix": stripe.api_key[:7] + "..." if stripe.api_key else None
    }

def validate_stripe_config():
    """Validate that Stripe is properly configured"""
    if not stripe.api_key:
        raise ValueError("STRIPE_SECRET_KEY environment variable is not set")
    
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is not set")
    
    # Validate API key format
    if not stripe.api_key.startswith(('sk_test_', 'sk_live_')):
        raise ValueError("Invalid Stripe secret key format")
    
    return True
