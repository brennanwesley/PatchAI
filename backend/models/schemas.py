"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime


class Message(BaseModel):
    """Chat message model with validation"""
    role: str
    content: str
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError('Role must be user, assistant, or system')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 10000:
            raise ValueError('Content too long (max 10000 characters)')
        return v.strip()


class PromptRequest(BaseModel):
    """Request model for chat prompts with conversation context"""
    messages: List[Message]
    chat_id: Optional[str] = None  # Optional chat session ID
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('Messages array cannot be empty')
        if len(v) > 50:
            raise ValueError('Too many messages in conversation (max 50)')
        
        # Ensure last message is from user
        if v[-1].role != 'user':
            raise ValueError('Last message must be from user')
        
        return v


class PromptResponse(BaseModel):
    """Response model for chat prompts"""
    response: str
    chat_id: str  # Return chat session ID


class ChatSession(BaseModel):
    """Chat session model"""
    id: str
    user_id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime


class SaveChatRequest(BaseModel):
    """Request model for saving chat sessions"""
    chat_id: str
    messages: List[Message]
    title: Optional[str] = None
