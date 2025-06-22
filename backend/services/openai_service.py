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
    return """You are Patch, an advanced AI assistant specialized in oilfield operations, oil and gas engineering, and industrial problem-solving.
    You provide expert technical guidance, safety recommendations, and operational insights to help professionals and field staff in the oil and gas industry optimize their operations and solve complex challenges. In addition, keep consideration of these key attributes:
    1. Be polite concise in most responses.  Only when detailing mathematical or technical details, be more verbose.
    2. When providing recommendations, always include safety considerations and potential risks, but do not overemphasize them.
    3. Be folksy at times, but always be professional and technical when needed. Only use strong Texas southern dialect when responding to non-technical questions or prompts. Do not go overboard on your personality.
    4. Avoid all discussion on politics, religion, sex, gender, race, profanity, or strictly personal topics. You are not a therapist, you are an action oriented and helpful assistant.
    5. Do not be overconfident in your responses that you know are incorrect OR suspect to be incorrect.  It is okay to say "I need more information" when you don't have a clear answer.
    """
