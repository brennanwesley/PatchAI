#!/usr/bin/env python3
"""
Startup script for the FastAPI application.
This script provides better error handling and logging for deployment.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("App will start but some endpoints may not work properly")
    else:
        logger.info("All required environment variables are set")

def main():
    """Start the FastAPI application."""
    try:
        # Check environment
        check_environment()
        
        # Import and start the app
        logger.info("Starting FastAPI application...")
        
        # Import main module
        from main import app
        
        # Get port from environment or default to 8000
        port = int(os.getenv('PORT', 8000))
        
        # Start uvicorn
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
