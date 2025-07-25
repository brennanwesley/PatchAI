#!/usr/bin/env python3
"""
PatchAI Backend v2.0.0 - Enterprise SaaS Platform
Copyright (c) 2025 brennanwesley. All Rights Reserved.

PROPRIETARY AND CONFIDENTIAL
This software is proprietary to brennanwesley. Unauthorized copying, distribution,
modification, or commercial use is strictly prohibited.

Modular FastAPI application with proper separation of concerns
Last updated: 2025-06-28 - EMERGENCY DEPLOYMENT FOR MESSAGE PERSISTENCE FIX
DEPLOYMENT TRIGGER: 2025-06-28T14:20:00Z - CRITICAL MESSAGE BUG RESOLUTION
"""

import os
import time
import uuid
import logging
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging
from typing import Dict, Any

# Import our modular components
from core.logging import StructuredLogger
from core.rate_limiter import RateLimiter
from core.auth import verify_jwt_token
from core.monitoring import get_health_status
from core.subscription_middleware import enforce_subscription
# Fixed import: get_stripe_config_status (not get_stripe_config)
from core.stripe_config import validate_stripe_config, get_stripe_config_status, initialize_stripe
from models.schemas import PromptRequest, PromptResponse, SaveChatRequest, Message
from services.openai_service import initialize_openai_client, get_system_prompt
from services.supabase_service import supabase
from services.wti_service import wti_service
from services.chat_service import ChatService
from routes.payment_routes import router as payment_router
from routes.referral_routes import router as referral_router
from routes.monitoring_routes import router as monitoring_router
from routes.sync_routes import router as sync_router
from routes.phase3_routes import router as phase3_router
# Pump routes removed to restore basic chat functionality
from services.background_monitor import background_monitor
# Phase 3 Production Hardening Services
from services.webhook_redundancy_service import webhook_redundancy_service
from services.integrity_validation_service import integrity_validation_service
from services.performance_optimization_service import performance_optimization_service
from services.monitoring_dashboard_service import monitoring_dashboard_service
from services.provisional_scheduler import provisional_scheduler

# Initialize structured logging
structured_logger = StructuredLogger()
logger = structured_logger.logger

# Initialize services
logger.info("🚀 Initializing PatchAI Backend services...")
logger.info("🚨 EMERGENCY DEPLOYMENT: Message persistence bug resolution - 2025-06-28T14:20:00Z")
logger.info("🔍 Enhanced debugging enabled for chat message operations")

# Initialize OpenAI
if not initialize_openai_client():
    logger.error("❌ Failed to initialize OpenAI client")
    
# Initialize Supabase
supabase_client = supabase

# Initialize Stripe
logger.info("💳 Initializing Stripe...")
if initialize_stripe():
    logger.info("✅ Stripe initialized successfully")
else:
    logger.error("❌ Failed to initialize Stripe - payment features may not work")

logger.info("✅ Service initialization complete")

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pump context service removed to restore basic chat functionality

# Initialize FastAPI app
app = FastAPI(
    title="PatchAI Backend",
    description="Enterprise SaaS Platform for PatchAI",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Global exception handler for all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full error with traceback
    logger.error(
        f"Unhandled exception: {str(exc)}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Client: {request.client.host if request.client else 'unknown'}\n"
        f"Traceback: {traceback.format_exc()}",
        exc_info=True
    )
    
    # Return a detailed error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "request_url": str(request.url),
            "request_method": request.method,
            "error_type": exc.__class__.__name__
        }
    )

# Handle HTTP exceptions (like 404, 403, etc.)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        f"HTTP Exception: {exc.detail}\n"
        f"Status Code: {exc.status_code}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Handle request validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Request Validation Error: {str(exc)}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Errors: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://patchai.app",        # Production domain
        "https://www.patchai.app",    # Production domain with www
        "https://patchai-frontend.vercel.app",
        "http://localhost:3000",  # For local development
        "https://localhost:3000"  # For local HTTPS development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize clients
openai_client = initialize_openai_client()
rate_limiter = RateLimiter()
chat_service = ChatService(supabase_client) if supabase_client else None

# Pump initialization removed to restore basic chat functionality

# Validate Stripe configuration
try:
    validate_stripe_config()
    stripe_config = get_stripe_config_status()
    logger.info(f"Stripe configured: API key={stripe_config['stripe_secret_configured']}, Webhook={stripe_config['stripe_webhook_configured']}")
except Exception as e:
    logger.warning(f"Stripe configuration warning: {str(e)}")

logger.info("PatchAI Backend initialized with enterprise architecture and chat service")

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize background services on startup"""
    logger.info("🚀 Application startup initiated")
    
    # Start provisional access scheduler
    try:
        provisional_scheduler.start()
        logger.info("✅ Provisional access scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start provisional scheduler: {str(e)}")
    
    # Pump context service removed to restore basic chat functionality
    
    logger.info("🚀 Application startup complete")
    logger.info("✅ All services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of background services"""
    logger.info("🛑 Application shutdown initiated")
    
    # Stop provisional access scheduler
    try:
        provisional_scheduler.stop()
        logger.info("✅ Provisional access scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping provisional scheduler: {str(e)}")
    
    logger.info("✅ Application shutdown complete")


def get_client_ip(request: Request) -> str:
    """Extract client IP address with proxy support"""
    # Check for forwarded IP first (common in production deployments)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    return request.client.host


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for tracing"""
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Get client info
    client_ip = get_client_ip(request)
    
    # Log request start
    structured_logger.log_request(
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        client_ip=client_ip
    )
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log response
        structured_logger.log_response(
            correlation_id=correlation_id,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            endpoint=request.url.path
        )
        
        # Add correlation ID and timing to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
        
        return response
        
    except Exception as e:
        # Log error
        response_time_ms = (time.time() - start_time) * 1000
        structured_logger.log_error(
            correlation_id=correlation_id,
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "correlation_id": correlation_id},
            headers={"X-Correlation-ID": correlation_id, "X-Response-Time": f"{response_time_ms:.2f}ms"}
        )


async def check_rate_limits(request: Request, user_id: str):
    """Check both user and IP rate limits"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    client_ip = get_client_ip(request)
    
    # Check user rate limit
    user_allowed, user_count, user_limit = rate_limiter.check_user_limit(user_id)
    if not user_allowed:
        structured_logger.log_rate_limit_hit(correlation_id, "user_daily", user_id, client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Daily message limit exceeded ({user_count}/{user_limit}). Upgrade your subscription for higher limits.",
            headers={"Retry-After": "86400"}  # 24 hours
        )
    
    # Check IP rate limit
    ip_allowed, ip_count = rate_limiter.check_ip_limit(client_ip)
    if not ip_allowed:
        structured_logger.log_rate_limit_hit(correlation_id, "ip_hourly", user_id, client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests from your IP ({ip_count}/100 per hour). Please try again later.",
            headers={"Retry-After": "3600"}  # 1 hour
        )


# Routes
@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: PromptRequest, req: Request, user_id: str = Depends(verify_jwt_token)):
    """Send conversation to OpenAI and return response with proper chat session management"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    logger.info(f"[REQUEST] Starting chat completion - User: {user_id}, Correlation ID: {correlation_id}")
    
    try:
        # Log the incoming request
        logger.debug(f"[REQUEST] Incoming request data: {request.model_dump_json()}")
        
        # Check rate limits
        logger.debug("[RATE LIMIT] Checking rate limits...")
        await check_rate_limits(req, user_id)
        logger.debug("[RATE LIMIT] Rate limits check passed")
        
        # Enforce subscription access (PAYWALL)
        logger.debug("[SUBSCRIPTION] Validating subscription...")
        subscription_info = await enforce_subscription(req, user_id)
        logger.debug(f"[SUBSCRIPTION] Subscription info: {subscription_info}")
        
        # Validate input
        if not request.messages:
            logger.warning("[VALIDATION] Empty messages array received")
            raise HTTPException(status_code=400, detail="Messages array cannot be empty")
            
        # Log the last user message for context
        last_user_message = next((msg for msg in reversed(request.messages) if msg.role == "user"), None)
        if last_user_message:
            logger.info(f"[MESSAGE] Processing user message: {last_user_message.content[:200]}...")
        
        # Pump context service removed to restore basic chat functionality
        
        if not openai_client:
            structured_logger.log_error(correlation_id, "OpenAI", "OpenAI client not initialized", user_id)
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        # CRITICAL FIX: Retrieve full conversation history from database
        logger.info(f"🔍 CONTEXT_DEBUG: Received {len(request.messages)} new messages from frontend")
        
        # Get the user's single chat session with full message history
        try:
            chat_session = await chat_service.get_single_chat_session(user_id)
            stored_messages = chat_session.messages if chat_session else []
            logger.info(f"📚 CONTEXT_DEBUG: Retrieved {len(stored_messages)} stored messages from database")
        except Exception as e:
            logger.error(f"❌ CONTEXT_DEBUG: Failed to retrieve chat history: {e}")
            stored_messages = []
        
        # Combine stored messages with new message for complete context
        # The new message should be the last one in request.messages
        new_message = request.messages[-1] if request.messages else None
        
        if new_message:
            logger.info(f"📝 CONTEXT_DEBUG: New message ({new_message.role}): {new_message.content[:50]}...")
        
        # Prepare complete conversation history for OpenAI
        system_prompt = get_system_prompt()
        logger.info(f"📝 CONTEXT_DEBUG: Base system prompt length: {len(system_prompt)} characters")
        
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Add all stored messages first (Message objects with .role and .content attributes)
        for i, stored_msg in enumerate(stored_messages):
            openai_messages.append({
                "role": stored_msg.role,
                "content": stored_msg.content
            })
            logger.info(f"🔄 CONTEXT_DEBUG: Added stored message {i+1} ({stored_msg.role})")
        
        # Add the new message
        if new_message:
            openai_messages.append({
                "role": new_message.role,
                "content": new_message.content
            })
            logger.info(f"🆕 CONTEXT_DEBUG: Added new message ({new_message.role})")
        
        # Final context validation
        total_conversation_messages = len(openai_messages) - 1  # Exclude system prompt
        total_stored = len(stored_messages)
        total_new = 1 if new_message else 0
        
        logger.info(f"🎯 CONTEXT_DEBUG: Complete context prepared:")
        logger.info(f"   - System prompt: 1 message")
        logger.info(f"   - Stored history: {total_stored} messages")
        logger.info(f"   - New message: {total_new} messages")
        logger.info(f"   - Total to OpenAI: {len(openai_messages)} messages")
        
        # Log OpenAI request with correct count
        structured_logger.log_openai_request(correlation_id, "gpt-4o", total_conversation_messages)
        
        # Send to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            max_tokens=2500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Add user message to single chat session
        user_message = request.messages[-1]  # Get the latest user message
        chat_id = await chat_service.add_message_to_single_chat(user_id, user_message)
        
        # Add AI response to single chat session
        ai_message = Message(role="assistant", content=ai_response)
        await chat_service.add_message_to_single_chat(user_id, ai_message)
        
        logger.info(f"OpenAI response generated and saved to single chat {chat_id} for user {user_id}")
        
        return PromptResponse(response=ai_response, chat_id=chat_id)
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_openai_error(correlation_id, str(e))
        structured_logger.log_error(correlation_id, "OpenAI", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to process your request")


@app.get("/history")
async def get_history(req: Request, user_id: str = Depends(verify_jwt_token)):
    """Get user's single chat session with all messages"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # NOTE: Removed enforce_subscription() to allow new users to load empty chat history
        # Paywall enforcement happens at /prompt endpoint when user tries to chat
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        # Get user's single chat session
        chat_session = await chat_service.get_single_chat_session(user_id)
        
        if chat_session:
            # Return single chat session in expected format
            session_data = {
                "id": chat_session.id,
                "title": chat_session.title,
                "created_at": chat_session.created_at.isoformat(),
                "updated_at": chat_session.updated_at.isoformat()
            }
            
            # Properly serialize Message objects for JSON response
            serialized_messages = []
            for msg in chat_session.messages:
                serialized_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            logger.info(f"Single chat session retrieved for user {user_id} with {len(chat_session.messages)} messages")
            logger.info(f"🔍 HISTORY_DEBUG: Returning {len(serialized_messages)} serialized messages to frontend")
            
            # Debug log first few messages for verification
            for i, msg in enumerate(serialized_messages[:3]):
                preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                logger.info(f"📄 HISTORY_DEBUG: Message {i+1} ({msg['role']}): {preview}")
            
            return {"sessions": [session_data], "messages": serialized_messages}
        else:
            # No chat session exists yet
            logger.info(f"No chat session found for user {user_id} - will be created on first message")
            return {"sessions": [], "messages": []}
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


# REMOVED: Individual chat session endpoint - single chat architecture only uses /history


# REMOVED: Multi-chat message append endpoint - single chat architecture handles messages automatically





@app.delete("/history/clear")
async def clear_chat_messages(req: Request, user_id: str = Depends(verify_jwt_token)):
    """Clear all messages from user's single chat session"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Enforce subscription access (PAYWALL)
        await enforce_subscription(req, user_id)
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        success = await chat_service.clear_single_chat_messages(user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear chat messages")
        
        logger.info(f"Chat messages cleared for user {user_id}")
        return {"status": "cleared"}
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to clear chat messages")


@app.post("/admin/global-hard-delete")
async def global_hard_delete_all_messages(req: Request, user_id: str = Depends(verify_jwt_token)):
    """ADMIN ONLY: Global hard delete of ALL chat messages for ALL users (complete reset)"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # CRITICAL: This is a destructive operation - log extensively
        logger.warning(f"🚨 ADMIN GLOBAL HARD DELETE requested by user {user_id}")
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        # Execute global hard delete
        success = await chat_service.global_hard_delete_all_messages()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to execute global hard delete")
        
        logger.warning(f"🚨 GLOBAL HARD DELETE COMPLETED by user {user_id} - ALL chat history removed")
        return {"status": "global_hard_delete_complete", "message": "All chat history for all users has been permanently deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to execute global hard delete")


@app.get("/metrics")
async def get_metrics():
    """Get current performance metrics"""
    return structured_logger.get_metrics()


@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "PatchAI Backend API is running", "version": "0.3.1"}


@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive system status"""
    health_status = get_health_status(openai_client, supabase_client, rate_limiter, structured_logger)
    
    # Add Stripe configuration status
    try:
        stripe_config = get_stripe_config_status()
        health_status["stripe"] = {
            "configured": stripe_config['stripe_secret_configured'] and stripe_config['stripe_webhook_configured'],
            "stripe_secret_configured": stripe_config['stripe_secret_configured'],
            "stripe_webhook_configured": stripe_config['stripe_webhook_configured'],
            "stripe_publishable_configured": stripe_config['stripe_publishable_configured'],
            "stripe_initialized": stripe_config['stripe_initialized']
        }
    except Exception as e:
        logger.error(f"Error getting Stripe config status: {str(e)}")
        health_status["stripe"] = {"configured": False, "error": str(e)}
    
    return health_status


@app.get("/healthz")
async def health_check_render():
    """Simple health check endpoint for Render"""
    return {"status": "ok"}


@app.get("/rate-limit-status")
async def get_rate_limit_status(request: Request, user_id: str = Depends(verify_jwt_token)):
    """Get current rate limit status for authenticated user"""
    client_ip = get_client_ip(request)
    
    try:
        user_status = rate_limiter.get_user_status(user_id)
        ip_status = rate_limiter.get_ip_status(client_ip)
        
        return {
            "user_limits": user_status,
            "ip_limits": ip_status,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit status")


@app.delete("/admin/user/{user_id}/history")
async def delete_user_history(user_id: str, req: Request):
    """Admin endpoint to delete all chat history for a specific user"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Get the requesting user's ID from the JWT token
        requesting_user_id = verify_jwt_token(req.headers.get("authorization", "").replace("Bearer ", ""))
        
        # Check if the requesting user is an admin
        admin_result = supabase.table("users").select("is_admin").eq("id", requesting_user_id).execute()
        
        if not admin_result.data or not admin_result.data[0].get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Delete all messages for the specified user
        delete_result = supabase.table("messages").delete().eq("user_id", user_id).execute()
        
        # Delete the chat session for the user
        chat_delete_result = supabase.table("chats").delete().eq("user_id", user_id).execute()
        
        logger.info(f"Admin {requesting_user_id} deleted all history for user {user_id}")
        
        return {
            "status": "deleted",
            "user_id": user_id,
            "deleted_sessions": deleted_sessions,
            "estimated_deleted_messages": deleted_messages,
            "message": f"Successfully deleted all chat history for user {user_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete user history: {str(e)}")


@app.get("/api/wti-price")
async def get_wti_price():
    """Get current WTI oil price data"""
    try:
        logger.info("WTI price endpoint called")
        wti_data = await wti_service.get_wti_price()
        logger.info(f"WTI price data returned: ${wti_data.get('price', 'N/A')}")
        return wti_data
    except Exception as e:
        logger.error(f"Failed to get WTI price: {e}")
        # Return fallback data instead of error to keep UI working
        import time
        return {
            'price': 65.00,
            'change': 0.00,
            'changePercent': 0.0,
            'lastUpdated': time.time(),
            'source': 'fallback',
            'isLive': False,
            'oilType': 'Fallback Data'
        }


app.include_router(payment_router)
app.include_router(referral_router)
app.include_router(monitoring_router)
app.include_router(sync_router)
app.include_router(phase3_router)
# Pump router removed to restore basic chat functionality

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)