"""
Supabase client service and configuration
"""

import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def initialize_supabase_client() -> Client:
    """Initialize Supabase client"""
    try:
        if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
            client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Supabase client initialized successfully")
            return client
        else:
            logger.warning("Supabase credentials not found - database features will be disabled")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None
