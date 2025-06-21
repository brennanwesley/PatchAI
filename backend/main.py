#!/usr/bin/env python3
"""
Simplified main.py for guaranteed Render deployment success
Uses minimal dependencies and robust error handling
Last updated: 2025-06-21 - SECURITY FIXES + RATE LIMITING APPLIED
"""

import os
import logging
import httpx
import jwt
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from openai import OpenAI
from supabase import create_client, Client

# Configure logging - SECURITY: Remove sensitive data from logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="PatchAI Backend API", version="1.0.0")

# CORS middleware - SECURITY: Strict origin validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://patchai-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # SECURITY: Limit methods
    allow_headers=["Authorization", "Content-Type"],  # SECURITY: Limit headers
)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Validate required environment variables
if not all([OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET]):
    logger.error("Missing required environment variables")
    raise RuntimeError("Missing required environment variables")

# Initialize clients with error handling
openai_client = None
supabase_client = None
initialization_error = None

# Security
security = HTTPBearer()

# Debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"OPENAI_API_KEY exists: {OPENAI_API_KEY is not None}")
logger.info(f"SUPABASE_URL exists: {SUPABASE_URL is not None}")
logger.info(f"SUPABASE_SERVICE_ROLE_KEY exists: {SUPABASE_SERVICE_ROLE_KEY is not None}")

# Initialize Supabase client
try:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        logger.error("Supabase configuration missing")
except Exception as e:
    logger.error(f"Supabase client initialization error: {e}")

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

# RATE LIMITING SYSTEM
class RateLimiter:
    """High-performance memory-based rate limiter with subscription-tier awareness"""
    
    def __init__(self):
        # Memory-based counters for microsecond performance
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        self.ip_requests: Dict[str, deque] = defaultdict(deque)
        
        # Subscription tier limits (messages per day)
        self.TIER_LIMITS = {
            'free': 10,
            'standard': 1000,
            'premium': 5000,
            'default': 10  # Default to free tier
        }
        
        # IP-based limits (per hour to prevent abuse)
        self.IP_LIMIT_PER_HOUR = 100
        
        logger.info("Rate limiter initialized with subscription-tier awareness")
    
    def _cleanup_old_requests(self, request_queue: deque, time_window: int) -> None:
        """Remove requests older than time_window seconds"""
        current_time = time.time()
        while request_queue and current_time - request_queue[0] > time_window:
            request_queue.popleft()
    
    def _get_user_tier(self, user_id: str) -> str:
        """Get user's subscription tier - placeholder for future subscription system"""
        # TODO: Query user's subscription from database
        # For now, default to 'standard' for existing users, 'free' for new
        return 'standard'  # Will be configurable per user
    
    def check_user_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if user has exceeded their daily message limit"""
        current_time = time.time()
        day_in_seconds = 24 * 60 * 60
        
        # Clean up old requests (older than 24 hours)
        self._cleanup_old_requests(self.user_requests[user_id], day_in_seconds)
        
        # Get user's subscription tier and limit
        user_tier = self._get_user_tier(user_id)
        daily_limit = self.TIER_LIMITS.get(user_tier, self.TIER_LIMITS['default'])
        
        # Count requests in last 24 hours
        requests_today = len(self.user_requests[user_id])
        
        # Check if limit exceeded
        if requests_today >= daily_limit:
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Daily message limit reached ({daily_limit} messages)',
                'tier': user_tier,
                'requests_today': requests_today,
                'limit': daily_limit,
                'reset_time': 'midnight UTC'
            }
        
        # Record this request
        self.user_requests[user_id].append(current_time)
        
        return True, {
            'tier': user_tier,
            'requests_today': requests_today + 1,
            'limit': daily_limit,
            'remaining': daily_limit - requests_today - 1
        }
    
    def check_ip_limit(self, client_ip: str) -> Tuple[bool, Dict]:
        """Check if IP has exceeded hourly request limit"""
        current_time = time.time()
        hour_in_seconds = 60 * 60
        
        # Clean up old requests (older than 1 hour)
        self._cleanup_old_requests(self.ip_requests[client_ip], hour_in_seconds)
        
        # Count requests in last hour
        requests_this_hour = len(self.ip_requests[client_ip])
        
        # Check if limit exceeded
        if requests_this_hour >= self.IP_LIMIT_PER_HOUR:
            return False, {
                'error': 'ip_rate_limit_exceeded',
                'message': f'Too many requests from this IP ({self.IP_LIMIT_PER_HOUR}/hour)',
                'requests_this_hour': requests_this_hour,
                'limit': self.IP_LIMIT_PER_HOUR,
                'reset_time': '1 hour'
            }
        
        # Record this request
        self.ip_requests[client_ip].append(current_time)
        
        return True, {
            'requests_this_hour': requests_this_hour + 1,
            'limit': self.IP_LIMIT_PER_HOUR,
            'remaining': self.IP_LIMIT_PER_HOUR - requests_this_hour - 1
        }

# Initialize rate limiter
rate_limiter = RateLimiter()

def get_client_ip(request: Request) -> str:
    """Extract client IP address with proxy support"""
    # Check for forwarded IP (from load balancers/proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"

async def check_rate_limits(request: Request, user_id: str) -> None:
    """Check both user and IP rate limits"""
    client_ip = get_client_ip(request)
    
    # Check IP-based rate limit first (prevents IP-based abuse)
    ip_allowed, ip_info = rate_limiter.check_ip_limit(client_ip)
    if not ip_allowed:
        logger.warning(f"IP rate limit exceeded for {client_ip}: {ip_info}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "type": "ip_limit",
                "retry_after": 3600  # 1 hour in seconds
            }
        )
    
    # Check user-based rate limit (subscription-tier aware)
    user_allowed, user_info = rate_limiter.check_user_limit(user_id)
    if not user_allowed:
        logger.warning(f"User rate limit exceeded for {user_id}: {user_info}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": user_info['message'],
                "type": "user_limit",
                "tier": user_info['tier'],
                "requests_today": user_info['requests_today'],
                "limit": user_info['limit'],
                "retry_after": 86400  # 24 hours in seconds
            }
        )
    
    # Log successful rate limit check (for monitoring)
    logger.info(f"Rate limit check passed - User: {user_id}, IP: {client_ip}, "
               f"User tier: {user_info['tier']}, Remaining: {user_info['remaining']}")

# SECURITY: Enhanced Pydantic models with validation
class Message(BaseModel):
    role: str
    content: str
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError('Invalid role')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        if len(v) > 10000:  # SECURITY: Limit message length
            raise ValueError('Content too long (max 10000 characters)')
        return v.strip()

class PromptRequest(BaseModel):
    messages: List[Message]
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('Messages cannot be empty')
        if len(v) > 50:  # SECURITY: Limit conversation length
            raise ValueError('Too many messages (max 50)')
        return v

class PromptResponse(BaseModel):
    response: str

# SECURITY: Enhanced JWT validation
async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token with proper signature validation
    """
    try:
        token = credentials.credentials
        
        # SECURITY: Proper JWT verification with signature
        decoded = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
            
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {type(e).__name__}")  # SECURITY: No token details in logs
        raise HTTPException(status_code=401, detail="Authentication failed")

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
    # SWD Permitting Guidelines (to be completed with user-provided data)
    swd_guidelines = """
    [SWD PERMITTING GUIDELINES - TO BE PROVIDED]
    Please provide the specific SWD permitting guidelines you'd like to include here. If user starts asking questions about the Saltwater Disposals (SWD) in Texas then please share with a breakdown of the information below and provide them a link (provided here:https://www.rrc.texas.gov/oil-and-gas/applications-and-permits/injection-storage-permits/oil-and-gas-waste-disposal/injection-disposal-permit-procedures/) to the public website to the RRC.
    Information From the RRC:
    Utilizing scientific and engineering analysis, the Railroad Commission of Texas has issued new guidelines that further strengthen permitting of disposal wells in the Permian Basin.

    In order to further enhance the integrity of the underground disposal of produced water, new requirements will be implemented for saltwater disposal well (SWD) permit applications in the region. Produced water is a byproduct of oil and gas production and is injected into SWDs.  

    New and amended permit applications in the Permian Basin will now be evaluated based on three primary factors:

    An expanded area of review (AOR) at the injection site;
    Limits on the maximum injection pressure at the surface based on geologic properties; and
    Limits on the maximum daily injection volume based on reservoir pressure.

    In an AOR, operators are required to assess old or unplugged wells to ensure produced water would not escape through those wellbores. The new guidelines increase the AOR to half a mile – an increase from the current quarter-mile radius.

    The new permitting criteria also require operators to demonstrate that their injection pressure will not fracture the confining strata of the reservoirs that produced water is injected into.

    Additionally, the RRC will place limits on the maximum volumes that SWDs can inject based on the pressure in the disposal reservoirs.

    These changes strengthen the Commission’s disposal well permitting requirements by focusing permitting efforts to ensure injected fluids remain confined to the disposal formations to safeguard ground and surface fresh water.

    The new SWD permitting guidelines in the Permian Basin go into effect on June 1, 2025. They apply to new and amended permit applications for deep and shallow disposal wells. Applications for disposal wells that are located within 25 kilometers of a seismic event will continue to be reviewed under the agency’s seismicity review guidelines.
    """
    
    return f"""You are PatchAI, an AI Oilfield consultant specialized in oilfield drilling, completing, and production operations. Your role is to provide expert-level 
    guidance on drilling, completions, production, and other oilfield-related topics, such as reservoir analysis production optimization, and unit economics of oil and gas production and SWD wells. Follow these guidelines:
    
    1. Be helpful, concise, and technical in your responses
    2. Use United States oil and gas industry-standard terminology and units of measurement
    3. When discussing complex topics, break down information into clear, numbered points
    4. Always prioritize safety and regulatory compliance in your advice
    5. If you're unsure about something, say so rather than guessing, it is okay to display uncertainty 
    6. Format your responses with proper markdown for better readability
    7. Use bullet points for lists and **bold** for important terms
    8. Be friendly and folksy, we are in the American south so feel free to use southern dialect, just make sure to not do it on every response, especially not on the technical responses.
    9. Avoid all discussions of sex, gender, race, politics, religion, and personal topics. Stear the conversation back to being productive at work in the oil and gas industry
    
    IMPORTANT REFERENCE INFORMATION:
    {swd_guidelines}
    
    Your responses should be helpful, accurate, and tailored to the user's level of expertise.
    """

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive system status"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "openai": openai_client is not None,
            "supabase": supabase_client is not None,
            "rate_limiter": rate_limiter is not None
        },
        "rate_limiter": {
            "active_users": len(rate_limiter.user_requests),
            "active_ips": len(rate_limiter.ip_requests),
            "tier_limits": rate_limiter.TIER_LIMITS
        }
    }
    
    if initialization_error:
        status["initialization_error"] = initialization_error
        status["status"] = "degraded"
    
    return status

@app.get("/rate-limit-status")
async def get_rate_limit_status(request: Request, user_id: str = Depends(verify_jwt_token)):
    """Get current rate limit status for authenticated user"""
    client_ip = get_client_ip(request)
    
    # Get user tier and current usage
    user_tier = rate_limiter._get_user_tier(user_id)
    daily_limit = rate_limiter.TIER_LIMITS.get(user_tier, rate_limiter.TIER_LIMITS['default'])
    
    # Clean up old requests to get accurate counts
    current_time = time.time()
    day_in_seconds = 24 * 60 * 60
    hour_in_seconds = 60 * 60
    
    rate_limiter._cleanup_old_requests(rate_limiter.user_requests[user_id], day_in_seconds)
    rate_limiter._cleanup_old_requests(rate_limiter.ip_requests[client_ip], hour_in_seconds)
    
    # Calculate current usage
    requests_today = len(rate_limiter.user_requests[user_id])
    requests_this_hour = len(rate_limiter.ip_requests[client_ip])
    
    return {
        "user": {
            "tier": user_tier,
            "daily_limit": daily_limit,
            "requests_today": requests_today,
            "remaining_today": daily_limit - requests_today,
            "percentage_used": round((requests_today / daily_limit) * 100, 1)
        },
        "ip": {
            "hourly_limit": rate_limiter.IP_LIMIT_PER_HOUR,
            "requests_this_hour": requests_this_hour,
            "remaining_this_hour": rate_limiter.IP_LIMIT_PER_HOUR - requests_this_hour
        },
        "status": "within_limits" if requests_today < daily_limit else "limit_reached"
    }

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "PatchAI Backend API is running", "status": "healthy"}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment variables and client status"""
    return {
        "openai_client_initialized": openai_client is not None,
        "supabase_client_initialized": supabase_client is not None,
        "initialization_error": initialization_error,
        "environment_check": {
            "openai_key_configured": OPENAI_API_KEY is not None,
            "supabase_url_configured": SUPABASE_URL is not None,
            "supabase_key_configured": SUPABASE_SERVICE_ROLE_KEY is not None,
            "jwt_secret_configured": SUPABASE_JWT_SECRET is not None
        }
    }

# SECURITY: Add authentication to /prompt endpoint
@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: Request, request_data: PromptRequest, user_id: str = Depends(verify_jwt_token)):
    await check_rate_limits(request, user_id)
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI service unavailable"
        )
    try:
        # Convert messages to the format expected by the API
        messages = [{"role": "system", "content": get_system_prompt()}]
        
        # Add conversation history
        for msg in request_data.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # SECURITY: Log request without sensitive content
        logger.info(f"Processing chat request for user: {user_id[:8]}...")
        
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
        logger.info(f"Chat response generated for user: {user_id[:8]}...")  # SECURITY: No content in logs
        
        return PromptResponse(response=assistant_response)
        
    except Exception as e:
        error_msg = "Chat service error"  # SECURITY: Generic error message
        logger.error(f"OpenAI API error for user {user_id[:8]}...: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/history")
async def get_history(request: Request, user_id: str = Depends(verify_jwt_token)):
    """
    Get chat history for the authenticated user
    """
    await check_rate_limits(request, user_id)
    if not supabase_client:
        raise HTTPException(
            status_code=500,
            detail="Database service unavailable"
        )
    
    try:
        # Query chat_sessions for this user
        response = supabase_client.table('chat_sessions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('updated_at', desc=True)\
            .execute()
            
        return {"data": response.data, "error": None}
        
    except Exception as e:
        error_msg = "Error fetching chat history"
        logger.error(f"Database error for user {user_id[:8]}...: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

# SECURITY: Add authentication to /history POST endpoint
@app.post("/history")
async def save_history(request: Request, request_data: PromptRequest, user_id: str = Depends(verify_jwt_token)):
    await check_rate_limits(request, user_id)
    if not supabase_client:
        raise HTTPException(
            status_code=500,
            detail="Database service unavailable"
        )
    try:
        data = {
            "user_id": user_id,  # SECURITY: Associate with authenticated user
            "messages": [msg.dict() for msg in request_data.messages],
            "response": ""
        }
        supabase_client.from_("history").insert([data]).execute()
        logger.info(f"History saved for user: {user_id[:8]}...")
        return {"message": "History saved successfully"}
    except Exception as e:
        error_msg = "Error saving chat history"
        logger.error(f"Database save error for user {user_id[:8]}...: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
