#!/usr/bin/env python3
"""
PatchAI Backend - Refactored Enterprise Architecture
Modular FastAPI application with proper separation of concerns
Last updated: 2025-06-21 - REFACTORED FOR ENTERPRISE SCALABILITY
"""

import os
import time
import uuid
import logging
import traceback
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from services.supabase_service import initialize_supabase_client
from services.chat_service import ChatService
from routes.payment_routes import router as payment_router

# Initialize structured logging
structured_logger = StructuredLogger()
logger = structured_logger.logger

# Initialize services
logger.info("🚀 Initializing PatchAI Backend services...")

# Initialize OpenAI
if not initialize_openai_client():
    logger.error("❌ Failed to initialize OpenAI client")
    
# Initialize Supabase
if not initialize_supabase_client():
    logger.error("❌ Failed to initialize Supabase client")

# Initialize Stripe
logger.info("💳 Initializing Stripe...")
if initialize_stripe():
    logger.info("✅ Stripe initialized successfully")
else:
    logger.error("❌ Failed to initialize Stripe - payment features may not work")

logger.info("✅ Service initialization complete")

# Initialize FastAPI app
app = FastAPI(
    title="PatchAI Backend API",
    description="Enterprise-grade AI assistant for oilfield operations",
    version="0.3.1"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
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
supabase_client = initialize_supabase_client()
rate_limiter = RateLimiter()
chat_service = ChatService(supabase_client) if supabase_client else None

# Validate Stripe configuration
try:
    validate_stripe_config()
    stripe_config = get_stripe_config_status()
    logger.info(f"Stripe configured: API key={stripe_config['stripe_secret_configured']}, Webhook={stripe_config['stripe_webhook_configured']}")
except Exception as e:
    logger.warning(f"Stripe configuration warning: {str(e)}")

logger.info("PatchAI Backend initialized with enterprise architecture and chat service")


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
    
    try:
        # Check rate limits
        await check_rate_limits(req, user_id)
        
        # Enforce subscription access (PAYWALL)
        subscription_info = await enforce_subscription(req, user_id)
        
        # Validate input
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages array cannot be empty")
        
        if not openai_client:
            structured_logger.log_error(correlation_id, "OpenAI", "OpenAI client not initialized", user_id)
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        # Log OpenAI request
        structured_logger.log_openai_request(correlation_id, "gpt-4", len(request.messages))
        
        # Prepare messages for OpenAI (include system prompt)
        openai_messages = [{"role": "system", "content": get_system_prompt()}]
        
        # Add conversation history
        for message in request.messages:
            openai_messages.append({
                "role": message.role,
                "content": message.content
            })
        
        # Send to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to conversation
        updated_messages = request.messages + [Message(role="assistant", content=ai_response)]
        
        # Handle chat session
        chat_id = request.chat_id
        if chat_id:
            # Update existing chat session
            success = await chat_service.update_chat_session(chat_id, user_id, updated_messages)
            if not success:
                # Chat not found, create new one
                chat_id = await chat_service.create_chat_session(user_id, updated_messages)
        else:
            # Create new chat session
            chat_id = await chat_service.create_chat_session(user_id, updated_messages)
        
        logger.info(f"OpenAI response generated for user {user_id}, chat {chat_id}")
        
        return PromptResponse(response=ai_response, chat_id=chat_id)
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_openai_error(correlation_id, str(e))
        structured_logger.log_error(correlation_id, "OpenAI", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to process your request")


@app.get("/history")
async def get_history(req: Request, user_id: str = Depends(verify_jwt_token)):
    """Get chat sessions for authenticated user"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Enforce subscription access (PAYWALL)
        await enforce_subscription(req, user_id)
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        sessions = await chat_service.get_user_chat_sessions(user_id)
        
        logger.info(f"Chat sessions retrieved for user {user_id}: {len(sessions)} sessions")
        return {"sessions": sessions}
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


@app.get("/history/{chat_id}")
async def get_chat_session(chat_id: str, req: Request, user_id: str = Depends(verify_jwt_token)):
    """Get specific chat session with full message history"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Enforce subscription access (PAYWALL)
        await enforce_subscription(req, user_id)
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        session = await chat_service.get_chat_session(chat_id, user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        logger.info(f"Chat session {chat_id} retrieved for user {user_id}")
        return {
            "id": session.id,
            "title": session.title,
            "messages": [{"role": msg.role, "content": msg.content} for msg in session.messages],
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve chat session")


@app.post("/history")
async def save_chat_session(request: SaveChatRequest, req: Request, user_id: str = Depends(verify_jwt_token)):
    """Save or update chat session"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Enforce subscription access (PAYWALL)
        await enforce_subscription(req, user_id)
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        # Validate input
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages array cannot be empty")
        
        # Check if chat session exists first
        existing_chat = await chat_service.get_chat_session(request.chat_id, user_id)
        
        if existing_chat:
            # Session exists, update it
            success = await chat_service.update_chat_session(request.chat_id, user_id, request.messages)
            chat_id = request.chat_id
        else:
            # Session doesn't exist, create new one
            chat_id = await chat_service.create_chat_session(user_id, request.messages, request.title)
        
        logger.info(f"Chat session saved for user {user_id}, chat {chat_id}")
        return {"status": "saved", "chat_id": chat_id}
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to save chat session")


@app.delete("/history/{chat_id}")
async def delete_chat_session(chat_id: str, req: Request, user_id: str = Depends(verify_jwt_token)):
    """Delete a chat session"""
    correlation_id = getattr(req.state, 'correlation_id', 'unknown')
    
    try:
        # Enforce subscription access (PAYWALL)
        await enforce_subscription(req, user_id)
        
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized", user_id)
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        success = await chat_service.delete_chat_session(chat_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        logger.info(f"Chat session {chat_id} deleted for user {user_id}")
        return {"status": "deleted", "chat_id": chat_id}
        
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(correlation_id, "Database", str(e), user_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to delete chat session")


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
        if not chat_service:
            structured_logger.log_error(correlation_id, "ChatService", "Chat service not initialized")
            raise HTTPException(status_code=503, detail="Chat service temporarily unavailable")
        
        # Get all chat sessions for the user
        chat_sessions = await chat_service.get_user_chat_sessions(user_id, limit=1000)
        
        if not chat_sessions:
            logger.info(f"No chat sessions found for user {user_id}")
            return {"status": "no_data", "message": f"No chat history found for user {user_id}"}
        
        deleted_sessions = 0
        deleted_messages = 0
        
        # Delete each chat session (this will also delete associated messages)
        for session in chat_sessions:
            chat_id = session['id']
            success = await chat_service.delete_chat_session(chat_id, user_id)
            if success:
                deleted_sessions += 1
                # Count messages (rough estimate)
                deleted_messages += 10  # Average estimate
        
        logger.info(f"Deleted {deleted_sessions} chat sessions for user {user_id}")
        
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


app.include_router(payment_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
