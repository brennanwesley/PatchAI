"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, validator


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
    """Request model for chat prompts"""
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 5000:
            raise ValueError('Message too long (max 5000 characters)')
        return v.strip()


class PromptResponse(BaseModel):
    """Response model for chat prompts"""
    response: str
