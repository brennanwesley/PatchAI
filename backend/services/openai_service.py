"""
OpenAI API service and configuration
"""

import os
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class CustomHTTPClient(httpx.Client):
    """Custom HTTP client for OpenAI with timeout configuration"""
    def __init__(self, *args, **kwargs):
        # Remove any proxy settings
        kwargs.pop('proxies', None)
        kwargs['timeout'] = httpx.Timeout(60.0, connect=60.0)
        super().__init__(*args, **kwargs)


def initialize_openai_client():
    """Initialize OpenAI client with custom configuration"""
    try:
        if OPENAI_API_KEY:
            # Create a custom HTTP client
            custom_client = CustomHTTPClient()
            
            # Initialize OpenAI client with custom HTTP client
            client = OpenAI(
                api_key=OPENAI_API_KEY,
                http_client=custom_client
            )
            
            logger.info("OpenAI client initialized successfully")
            return client
        else:
            logger.warning("OPENAI_API_KEY not found - OpenAI features will be disabled")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return None


def get_system_prompt() -> str:
    """
    Defines the system prompt that sets the behavior and personality of PatchAI
    """
    return """You are PatchAI, an advanced AI assistant specialized in drilling operations, oil and gas engineering, and industrial problem-solving. You provide expert technical guidance, safety recommendations, and operational insights to help professionals in the energy sector optimize their operations and solve complex challenges."""
