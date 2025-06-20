from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client
import jwt
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Chat Backend API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class PromptRequest(BaseModel):
    messages: List[Message]

class PromptResponse(BaseModel):
    response: str

class HistoryRequest(BaseModel):
    user_message: str
    assistant_message: str

class HistoryMessage(BaseModel):
    id: int
    user_id: str
    role: str
    content: str
    created_at: str

# Helper functions
def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user ID from JWT token"""
    try:
        token = credentials.credentials
        # For development, you might want to decode without verification
        # In production, use proper JWT verification with your secret
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub", "anonymous")
    except Exception as e:
        # For development, return a default user ID if token parsing fails
        logging.warning(f"Token parsing failed: {e}")
        return "anonymous"

# Routes
@app.get("/")
async def root():
    return {"message": "Chat Backend API is running"}

@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: PromptRequest):
    """Send messages to OpenAI Chat Completion API"""
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get response from OpenAI: {str(e)}"
        )

@app.post("/history")
async def save_history(
    request: HistoryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Save user and assistant messages to Supabase"""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # Save user message
        user_result = supabase.table("messages").insert({
            "user_id": user_id,
            "role": "user",
            "content": request.user_message,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        # Save assistant message
        assistant_result = supabase.table("messages").insert({
            "user_id": user_id,
            "role": "assistant", 
            "content": request.assistant_message,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        return {"message": "Messages saved successfully"}
        
    except Exception as e:
        logging.error(f"Supabase save error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save messages: {str(e)}"
        )

@app.get("/history")
async def get_history(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> List[HistoryMessage]:
    """Get latest 20 messages for current user"""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # Query latest 20 messages for the user
        result = supabase.table("messages").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(20).execute()
        
        messages = []
        for msg in result.data:
            messages.append(HistoryMessage(
                id=msg["id"],
                user_id=msg["user_id"],
                role=msg["role"],
                content=msg["content"],
                created_at=msg["created_at"]
            ))
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))
        
    except Exception as e:
        logging.error(f"Supabase query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
