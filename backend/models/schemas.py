"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
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


# Referral System Models
class SignupWithReferralRequest(BaseModel):
    """Request model for user signup with optional referral code"""
    email: str
    password: str
    referral_code: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Valid email address required')
        return v.lower().strip()
    
    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('referral_code')
    def validate_referral_code(cls, v):
        if v:
            v = v.strip().upper()
            if len(v) != 6:
                raise ValueError('Referral code must be exactly 6 characters')
            if not v.isalnum():
                raise ValueError('Referral code must contain only letters and numbers')
        return v


class ProfileUpdateRequest(BaseModel):
    """Request model for updating user profile"""
    display_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if v and len(v.strip()) > 100:
            raise ValueError('Display name too long (max 100 characters)')
        return v.strip() if v else None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.strip()) > 20:
            raise ValueError('Phone number too long (max 20 characters)')
        return v.strip() if v else None
    
    @validator('company')
    def validate_company(cls, v):
        if v and len(v.strip()) > 100:
            raise ValueError('Company name too long (max 100 characters)')
        return v.strip() if v else None


class ReferralInfoResponse(BaseModel):
    """Response model for user referral information"""
    user_id: str
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None
    referring_user_info: Optional[Dict[str, str]] = None
    referrals_made: List[Dict[str, Any]] = []
    total_referrals: int = 0


class ReferralRewardsResponse(BaseModel):
    """Response model for referral rewards summary"""
    user_id: str
    total_rewards: float = 0.0
    total_paid: float = 0.0
    pending_rewards: float = 0.0
    rewards_history: List[Dict[str, Any]] = []


class ProfileResponse(BaseModel):
    """Response model for user profile information"""
    id: str
    email: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None
    subscription_status: Optional[str] = None
    plan_tier: Optional[str] = None
    created_at: str
    updated_at: str


class ValidateReferralCodeRequest(BaseModel):
    """Request model for validating referral codes"""
    referral_code: str
    
    @validator('referral_code')
    def validate_referral_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Referral code cannot be empty')
        v = v.strip().upper()
        if len(v) != 6:
            raise ValueError('Referral code must be exactly 6 characters')
        if not v.isalnum():
            raise ValueError('Referral code must contain only letters and numbers')
        return v
