from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from openai import OpenAI
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

try:
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logging.info("OpenAI client initialized successfully")
except Exception as e:
    logging.warning(f"OpenAI client initialization warning: {e}")
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
