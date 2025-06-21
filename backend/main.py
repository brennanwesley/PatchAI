#!/usr/bin/env python3
"""
Simplified main.py for guaranteed Render deployment success
Uses minimal dependencies and robust error handling
Last updated: 2025-06-21 - SECURITY + RATE LIMITING + MONITORING APPLIED
"""

import os
import logging
import httpx
import jwt
import time
import uuid
import traceback
import psutil
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from openai import OpenAI
from supabase import create_client, Client

# MONITORING: Enhanced structured logging configuration
class StructuredLogger:
    """Enhanced logging with correlation IDs and structured data"""
    
    def __init__(self):
        # Configure structured logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Performance metrics storage
        self.metrics = {
            'requests_total': 0,
            'requests_by_endpoint': defaultdict(int),
            'response_times': defaultdict(list),
            'errors_total': 0,
            'errors_by_type': defaultdict(int),
            'openai_requests': 0,
            'openai_errors': 0,
            'rate_limit_hits': 0
        }
        
        self.logger.info("Structured logger initialized with performance metrics")
    
    def log_request(self, correlation_id: str, method: str, path: str, client_ip: str, user_id: str = None):
        """Log incoming request with structured data"""
        self.metrics['requests_total'] += 1
        self.metrics['requests_by_endpoint'][f"{method} {path}"] += 1
        
        self.logger.info(
            f"REQUEST_START - {correlation_id} - {method} {path} - "
            f"IP: {client_ip} - User: {user_id or 'anonymous'}"
        )
    
    def log_response(self, correlation_id: str, status_code: int, response_time_ms: float, endpoint: str):
        """Log response with performance metrics"""
        self.metrics['response_times'][endpoint].append(response_time_ms)
        
        # Keep only last 100 response times per endpoint
        if len(self.metrics['response_times'][endpoint]) > 100:
            self.metrics['response_times'][endpoint] = self.metrics['response_times'][endpoint][-100:]
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(
            level,
            f"REQUEST_END - {correlation_id} - Status: {status_code} - "
            f"Time: {response_time_ms:.2f}ms - Endpoint: {endpoint}"
        )
    
    def log_error(self, correlation_id: str, error_type: str, error_message: str, user_id: str = None, stack_trace: str = None):
        """Log error with detailed context"""
        self.metrics['errors_total'] += 1
        self.metrics['errors_by_type'][error_type] += 1
        
        error_data = {
            'correlation_id': correlation_id,
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if stack_trace:
            error_data['stack_trace'] = stack_trace
        
        self.logger.error(f"ERROR - {correlation_id} - {error_type}: {error_message}")
        if stack_trace:
            self.logger.error(f"STACK_TRACE - {correlation_id} - {stack_trace}")
    
    def log_openai_request(self, correlation_id: str, model: str, message_count: int):
        """Log OpenAI API request"""
        self.metrics['openai_requests'] += 1
        self.logger.info(
            f"OPENAI_REQUEST - {correlation_id} - Model: {model} - Messages: {message_count}"
        )
    
    def log_openai_error(self, correlation_id: str, error: str):
        """Log OpenAI API error"""
        self.metrics['openai_errors'] += 1
        self.logger.error(f"OPENAI_ERROR - {correlation_id} - {error}")
    
    def log_rate_limit_hit(self, correlation_id: str, limit_type: str, user_id: str, client_ip: str):
        """Log rate limit hit"""
        self.metrics['rate_limit_hits'] += 1
        self.logger.warning(
            f"RATE_LIMIT_HIT - {correlation_id} - Type: {limit_type} - "
            f"User: {user_id} - IP: {client_ip}"
        )
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        # Calculate average response times
        avg_response_times = {}
        for endpoint, times in self.metrics['response_times'].items():
            if times:
                avg_response_times[endpoint] = {
                    'avg_ms': round(sum(times) / len(times), 2),
                    'min_ms': round(min(times), 2),
                    'max_ms': round(max(times), 2),
                    'count': len(times)
                }
        
        return {
            'requests_total': self.metrics['requests_total'],
            'requests_by_endpoint': dict(self.metrics['requests_by_endpoint']),
            'response_times': avg_response_times,
            'errors_total': self.metrics['errors_total'],
            'errors_by_type': dict(self.metrics['errors_by_type']),
            'openai_requests': self.metrics['openai_requests'],
            'openai_errors': self.metrics['openai_errors'],
            'rate_limit_hits': self.metrics['rate_limit_hits']
        }

# Initialize structured logger
structured_logger = StructuredLogger()
logger = structured_logger.logger

# Track application start time for uptime monitoring
app_start_time = time.time()

# Initialize FastAPI
app = FastAPI(title="PatchAI Backend API", version="1.0.0")

# MONITORING: Request correlation middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for tracing"""
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    request.state.start_time = time.time()
    
    # Extract user info for logging
    client_ip = get_client_ip(request)
    user_id = None
    
    # Try to extract user ID from JWT token for logging
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            user_id = decoded.get("sub")
    except:
        pass  # Continue without user ID
    
    # Log request start
    structured_logger.log_request(
        correlation_id, 
        request.method, 
        request.url.path, 
        client_ip, 
        user_id
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time_ms = (time.time() - request.state.start_time) * 1000
    
    # Log response
    structured_logger.log_response(
        correlation_id,
        response.status_code,
        response_time_ms,
        f"{request.method} {request.url.path}"
    )
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
    
    return response

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

async def check_rate_limits(request: Request, user_id: str) -> None:
    """Check both user and IP rate limits"""
    client_ip = get_client_ip(request)
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Check IP-based rate limit first (prevents IP-based abuse)
    ip_allowed, ip_info = rate_limiter.check_ip_limit(client_ip)
    if not ip_allowed:
        structured_logger.log_rate_limit_hit(correlation_id, "ip_limit", user_id, client_ip)
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
        structured_logger.log_rate_limit_hit(correlation_id, "user_limit", user_id, client_ip)
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
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 10000:  # SECURITY: Limit message length
            raise ValueError('Message too long (max 10000 characters)')
        return v.strip()

class PromptResponse(BaseModel):
    response: str

# SECURITY: Enhanced JWT validation
async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user ID - SECURITY: Signature verification enabled"""
    try:
        token = credentials.credentials
        # SECURITY: Enable JWT signature verification
        decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        user_id = decoded.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        logger.error("Token validation error: ExpiredSignatureError")  # SECURITY: No token details in logs
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.error(f"Token validation error: InvalidTokenError")  # SECURITY: No token details in logs
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {type(e).__name__}")  # SECURITY: No token details in logs
        raise HTTPException(status_code=401, detail="Authentication failed")

def get_system_prompt():
    """
    Defines the system prompt that sets the behavior and personality of PatchAI
    """
    return """You are PatchAI, an expert AI assistant for drilling operations and oil & gas industry. 
    Provide accurate, practical advice on drilling, completions, production, and regulatory compliance.
    Be concise, technical, and prioritize safety in all recommendations."""

# Routes
@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: PromptRequest, req: Request, user_id: str = Depends(verify_jwt_token)):
    """Send prompt to OpenAI and return response - SECURITY: Now requires authentication"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Check rate limits first
        await check_rate_limits(req, user_id)
        
        # Validate request
        if not request.message or not request.message.strip():
            structured_logger.log_error(correlation_id, "validation_error", "Empty message provided", user_id)
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Log OpenAI request
        structured_logger.log_openai_request(correlation_id, "gpt-4", 1)
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": request.message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        logger.info(f"OpenAI request successful - {correlation_id} - User: {user_id}")
        
        return PromptResponse(
            response=ai_response,
            user_id=user_id,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like rate limits)
        raise
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        structured_logger.log_openai_error(correlation_id, error_msg)
        structured_logger.log_error(
            correlation_id, 
            "openai_api_error", 
            error_msg, 
            user_id, 
            traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Failed to process your request")

@app.get("/history")
async def get_history(req: Request, user_id: str = Depends(verify_jwt_token)):
    """Get chat history for authenticated user - SECURITY: JWT signature verification enabled"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Fetch chat sessions from Supabase
        response = supabase_client.table("chat_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        logger.info(f"Chat history retrieved - {correlation_id} - User: {user_id} - Sessions: {len(response.data)}")
        
        return {"sessions": response.data}
        
    except Exception as e:
        error_msg = f"Failed to retrieve chat history: {str(e)}"
        structured_logger.log_error(
            correlation_id, 
            "database_error", 
            error_msg, 
            user_id, 
            traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@app.post("/history")
async def save_history(request: PromptRequest, req: Request, user_id: str = Depends(verify_jwt_token)):
    """Save chat history - SECURITY: Now requires authentication"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Validate request
        if not request.message or not request.message.strip():
            structured_logger.log_error(correlation_id, "validation_error", "Empty message in save request", user_id)
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Save to Supabase with user association
        chat_data = {
            "user_id": user_id,
            "message": request.message,
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase_client.table("chat_sessions").insert(chat_data).execute()
        
        logger.info(f"Chat history saved - {correlation_id} - User: {user_id}")
        
        return {"message": "Chat history saved successfully", "id": response.data[0]["id"]}
        
    except Exception as e:
        error_msg = f"Failed to save chat history: {str(e)}"
        structured_logger.log_error(
            correlation_id, 
            "database_error", 
            error_msg, 
            user_id, 
            traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail="Failed to save chat history")

@app.get("/metrics")
async def get_metrics():
    """Get current performance metrics"""
    return structured_logger.get_metrics()

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

@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive system status"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get application metrics
        app_metrics = structured_logger.get_metrics()
        
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime_seconds": time.time() - app_start_time,
            "services": {
                "openai": openai_client is not None,
                "supabase": supabase_client is not None,
                "rate_limiter": rate_limiter is not None
            },
            "system_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            },
            "application_metrics": app_metrics,
            "rate_limiter": {
                "active_users": len(rate_limiter.user_requests),
                "active_ips": len(rate_limiter.ip_requests),
                "tier_limits": rate_limiter.TIER_LIMITS
            }
        }
        
        # Determine overall health status
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
            status["status"] = "degraded"
            status["warnings"] = []
            if cpu_percent > 90:
                status["warnings"].append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 90:
                status["warnings"].append(f"High memory usage: {memory.percent}%")
            if disk.percent > 95:
                status["warnings"].append(f"Low disk space: {disk.percent}% used")
        
        if initialization_error:
            status["initialization_error"] = initialization_error
            status["status"] = "degraded"
        
        return status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": "Health check failed",
            "services": {
                "openai": openai_client is not None,
                "supabase": supabase_client is not None,
                "rate_limiter": rate_limiter is not None
            }
        }

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
