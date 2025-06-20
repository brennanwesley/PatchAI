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

# Import OpenAI and set up client
import openai
from openai import OpenAI

# Use a custom HTTP client to avoid proxy issues
import httpx

class CustomHTTPClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        # Remove any proxy settings
        kwargs.pop('proxies', None)
        kwargs['timeout'] = httpx.Timeout(60.0, connect=60.0)
        super().__init__(*args, **kwargs)

# Initialize the client
try:
    if OPENAI_API_KEY:
        # Create a custom HTTP client
        http_client = CustomHTTPClient()
        
        # Initialize OpenAI with our custom client
        openai_client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
        
        # Test the connection
        openai_client.models.list()
        logger.info("OpenAI client initialized and tested successfully")
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

def get_system_prompt():
    """
    Defines the system prompt that sets the behavior and personality of PatchAI
    """
    return """You are PatchAI, an AI assistant specialized in oilfield operations. Your role is to provide expert-level 
    guidance on drilling, completions, production, and other oilfield-related topics. Follow these guidelines:
    
    1. Be concise and technical in your responses
    2. Use industry-standard terminology and units of measurement
    3. When discussing complex topics, break down information into clear, numbered points
    4. Always prioritize safety and regulatory compliance in your advice
    5. If you're unsure about something, say so rather than guessing
    6. Format your responses with proper markdown for better readability
    7. Use bullet points for lists and **bold** for important terms
    
    Your responses should be helpful, accurate, and tailored to the user's level of expertise.
    """

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
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI client not initialized"
        )
    try:
        # Convert messages to the format expected by the API
        messages = [{"role": "system", "content": get_system_prompt()}]
        
        # Add conversation history
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        logger.info(f"Sending request to OpenAI with messages: {messages}")
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.1
        )
        
        assistant_response = response.choices[0].message.content
        logger.info(f"Received response from OpenAI: {assistant_response[:200]}...")  # Log first 200 chars
        
        return PromptResponse(response=assistant_response)
        
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
