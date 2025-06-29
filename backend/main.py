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
from services.supabase_service import supabase
from services.chat_service import ChatService
from routes.payment_routes import router as payment_router
from routes.referral_routes import router as referral_router
from routes.monitoring_routes import router as monitoring_router
from routes.sync_routes import router as sync_router
from routes.phase3_routes import router as phase3_router
from services.background_monitor import background_monitor
# Phase 3 Production Hardening Services
from services.webhook_redundancy_service import webhook_redundancy_service
from services.integrity_validation_service import integrity_validation_service
from services.performance_optimization_service import performance_optimization_service
from services.monitoring_dashboard_service import monitoring_dashboard_service

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
    logger.info("🚀 Starting background monitoring service...")
    await background_monitor.start_monitoring()
    logger.info("✅ Background monitoring service started")
    
    # Phase 3 Production Hardening Services
    logger.info("🔧 Starting Phase 3 production hardening services...")
    try:
        await webhook_redundancy_service.start_redundancy_service()
        await integrity_validation_service.start_continuous_validation()
        await performance_optimization_service.start_performance_monitoring()
        await monitoring_dashboard_service.start_dashboard_service()
        logger.info("✅ Phase 3 services started successfully")
    except Exception as e:
        logger.error(f"❌ Phase 3 service startup error: {str(e)}")
        # Continue startup even if Phase 3 services fail

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of background services"""
    logger.info("🛑 Shutting down background services...")
    await background_monitor.stop()
    logger.info("✅ Background services stopped")


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
        openai_messages = [{"role": "system", "content": get_system_prompt()}]
        
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
        structured_logger.log_openai_request(correlation_id, "gpt-4", total_conversation_messages)
        
        # Send to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=openai_messages,
            max_tokens=1000,
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
app.include_router(referral_router)
app.include_router(monitoring_router)
app.include_router(sync_router)
app.include_router(phase3_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
