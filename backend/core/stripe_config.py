"""
Stripe Configuration Module
Handles Stripe SDK initialization and configuration
"""

import os
import stripe
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Stripe configuration constants
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

def initialize_stripe():
    """Initialize Stripe with API key from environment variables."""
    stripe_secret_key = os.getenv("STRIPE_API_SECRET")
    
    if not stripe_secret_key:
        logger.error("STRIPE_API_SECRET environment variable not found")
        return False
    
    try:
        stripe.api_key = stripe_secret_key
        logger.info("Stripe initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Stripe: {e}")
        return False

def validate_stripe_config():
    """Validate that Stripe is properly configured."""
    stripe_secret_key = os.getenv("STRIPE_API_SECRET")
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
    
    if not stripe_secret_key:
        logger.error("STRIPE_API_SECRET environment variable not found")
        return False
    
    if not stripe_webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET environment variable not found")
    
    if not stripe_publishable_key:
        logger.warning("STRIPE_PUBLISHABLE_KEY environment variable not found")
    
    return True

def get_stripe_config_status():
    """Get current Stripe configuration status for health checks."""
    return {
        "stripe_secret_configured": bool(os.getenv("STRIPE_API_SECRET")),
        "stripe_webhook_configured": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
        "stripe_publishable_configured": bool(os.getenv("STRIPE_PUBLISHABLE_KEY")),
        "stripe_initialized": stripe.api_key is not None
    }

def get_stripe_publishable_key():
    """Get Stripe publishable key for frontend use."""
    return os.getenv("STRIPE_PUBLISHABLE_KEY")
