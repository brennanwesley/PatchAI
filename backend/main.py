#!/usr/bin/env python3
"""
Simplified main.py for guaranteed Render deployment success
Uses minimal dependencies and robust error handling
Last updated: 2025-06-20 06:48 UTC - FINAL DEPLOYMENT FIX
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="PatchAI Backend API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients with error handling
openai_client = None
initialization_error = None

# Debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"OPENAI_API_KEY exists: {OPENAI_API_KEY is not None}")
logger.info(f"OPENAI_API_KEY length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")

try:
    if OPENAI_API_KEY:
        # Initialize OpenAI client for project keys (sk-proj-*)
        from openai import OpenAI
        
        # Create client with minimal parameters to avoid proxies issue
        openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            # Explicitly set other parameters to avoid defaults
            timeout=60.0,
            max_retries=3
        )
        logger.info("OpenAI client initialized successfully")
    else:
        logger.error("OPENAI_API_KEY is None or empty")
        initialization_error = "OPENAI_API_KEY is None or empty"
except Exception as e:
    logger.error(f"OpenAI client initialization error: {e}")
    logger.error(f"Error type: {type(e).__name__}")
    logger.error(f"OpenAI key starts with: {OPENAI_API_KEY[:10] if OPENAI_API_KEY else 'None'}...")
    initialization_error = f"{type(e).__name__}: {str(e)}"
    # Continue without crashing - will handle in endpoints

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class PromptRequest(BaseModel):
    messages: List[Message]

class PromptResponse(BaseModel):
    response: str

# Routes
@app.get("/")
async def root():
    # Trigger deployment
    """Root endpoint for health check"""
    return {"message": "PatchAI Backend API is running"}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment variables and client status"""
    return {
        "openai_key_exists": OPENAI_API_KEY is not None,
        "openai_key_length": len(OPENAI_API_KEY) if OPENAI_API_KEY else 0,
        "openai_client_initialized": openai_client is not None,
        "initialization_error": initialization_error,
        "environment_vars": {
            "PORT": os.getenv("PORT"),
            "OPENAI_API_KEY": "***" if OPENAI_API_KEY else None,
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_SERVICE_ROLE_KEY": "***" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else None
        }
    }

@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: PromptRequest):
    """Send messages to OpenAI Chat Completion API"""
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI client not initialized"
        )
    try:
        # Convert Pydantic models to dict format expected by OpenAI
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        assistant_response = response.choices[0].message.content
        
        return PromptResponse(response=assistant_response)
        
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from OpenAI: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
