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
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    config_status = {
        "stripe_secret_key": bool(stripe_secret_key),
        "webhook_secret": bool(webhook_secret),
        "stripe_initialized": bool(stripe.api_key)
    }
    
    return config_status

def get_stripe_config_status():
    """Get current Stripe configuration status for health checks."""
    config = validate_stripe_config()
    
    status = "healthy" if all(config.values()) else "degraded"
    
    return {
        "status": status,
        "details": config
    }
