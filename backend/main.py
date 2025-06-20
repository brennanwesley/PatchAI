#!/usr/bin/env python3
"""
Simplified main.py for guaranteed Render deployment success
Uses minimal dependencies and robust error handling
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PatchAI Backend API",
    version="1.0.0",
    description="OpenAI Chat Completion API for PatchAI"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class PromptRequest(BaseModel):
    messages: List[Message]

class PromptResponse(BaseModel):
    response: str

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
else:
    logger.warning("OPENAI_API_KEY not found - OpenAI client not initialized")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PatchAI Backend API is running",
        "status": "healthy",
        "openai_client_initialized": openai_client is not None
    }

@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: PromptRequest):
    """Send messages to OpenAI Chat Completion API"""
    logger.info(f"Received prompt request with {len(request.messages)} messages")
    
    if not openai_client:
        logger.error("OpenAI client not initialized")
        raise HTTPException(
            status_code=500,
            detail="OpenAI client not initialized. Please check OPENAI_API_KEY environment variable."
        )
    
    try:
        # Convert Pydantic models to dict format expected by OpenAI
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        logger.info(f"Converted messages: {messages}")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        assistant_response = response.choices[0].message.content
        logger.info(f"OpenAI response received: {assistant_response[:100]}...")
        
        return PromptResponse(response=assistant_response)
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from OpenAI: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
