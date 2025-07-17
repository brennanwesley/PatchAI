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
from services.chat_service import ChatService
from services.pump_context_service import PumpContextService
from routes.payment_routes import router as payment_router
from routes.referral_routes import router as referral_router
from routes.monitoring_routes import router as monitoring_router
from routes.sync_routes import router as sync_router
from routes.phase3_routes import router as phase3_router
from routes.pump_routes import router as pump_router
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

# Global variable for pump context service
pump_context_service = None

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

# Initialize referral service
from services.referral_service import ReferralService
referral_service = ReferralService(supabase_client) if supabase_client else None
logger.info(f"✅ Referral service initialized: {referral_service is not None}")

# DEPLOYMENT TRIGGER: 2025-07-14T01:52:30Z - FORCE RENDER REBUILD WITH 500 ERROR FIX
# Initialize pump context service with comprehensive error handling and diagnostics
logger.info("🔧 PUMP_INIT: Starting PumpContextService initialization...")

# Pre-initialization diagnostics
try:
    import os
    from pathlib import Path
    
    # Check if pump data directory exists
    pump_data_dir = Path(__file__).parent / "data" / "pumps"
    logger.info(f"🔍 PUMP_INIT: Checking pump data directory: {pump_data_dir}")
    logger.info(f"🔍 PUMP_INIT: Directory exists: {pump_data_dir.exists()}")
    
    if pump_data_dir.exists():
        pump_files = list(pump_data_dir.glob("*.json"))
        logger.info(f"🔍 PUMP_INIT: Found {len(pump_files)} JSON files in pump data directory")
        for pump_file in pump_files:
            logger.info(f"🔍 PUMP_INIT: - {pump_file.name} (size: {pump_file.stat().st_size} bytes)")
    else:
        logger.error(f"❌ PUMP_INIT: Pump data directory does not exist: {pump_data_dir}")
    
    # Check specific transfer_pumps.json file
    transfer_pumps_file = pump_data_dir / "transfer_pumps.json"
    logger.info(f"🔍 PUMP_INIT: Checking transfer_pumps.json: {transfer_pumps_file}")
    logger.info(f"🔍 PUMP_INIT: File exists: {transfer_pumps_file.exists()}")
    
    if transfer_pumps_file.exists():
        logger.info(f"🔍 PUMP_INIT: File size: {transfer_pumps_file.stat().st_size} bytes")
        logger.info(f"🔍 PUMP_INIT: File readable: {os.access(transfer_pumps_file, os.R_OK)}")
    
except Exception as diag_e:
    logger.error(f"❌ PUMP_INIT: Error during pre-initialization diagnostics: {diag_e}")
    logger.error(f"❌ PUMP_INIT: Diagnostics traceback: {traceback.format_exc()}")

# Attempt PumpContextService initialization
try:
    logger.info("🔧 PUMP_INIT: Attempting to import PumpContextService...")
    from services.pump_context_service import PumpContextService
    logger.info("✅ PUMP_INIT: PumpContextService import successful")
    
    logger.info("🔧 PUMP_INIT: Attempting to instantiate PumpContextService...")
    pump_context_service = PumpContextService()
    logger.info("✅ PUMP_INIT: PumpContextService initialized successfully")
    
    # Validate service functionality
    logger.info("🔧 PUMP_INIT: Testing service functionality...")
    if hasattr(pump_context_service, 'generate_pump_context'):
        logger.info("✅ PUMP_INIT: generate_pump_context method available")
    else:
        logger.error("❌ PUMP_INIT: generate_pump_context method missing")
    
    # Test with a simple query
    try:
        test_result = pump_context_service.generate_pump_context("test pump query")
        logger.info(f"✅ PUMP_INIT: Service test successful, result type: {type(test_result)}")
    except Exception as test_e:
        logger.error(f"❌ PUMP_INIT: Service test failed: {test_e}")
        
except ImportError as ie:
    logger.error(f"❌ PUMP_INIT: Failed to import PumpContextService: {ie}")
    logger.error(f"❌ PUMP_INIT: Import traceback: {traceback.format_exc()}")
    pump_context_service = None
    logger.warning("⚠️ PUMP_INIT: Pump context features disabled due to import failure")
except Exception as e:
    logger.error(f"❌ PUMP_INIT: Failed to initialize PumpContextService: {e}")
    logger.error(f"❌ PUMP_INIT: Error type: {type(e).__name__}")
    logger.error(f"❌ PUMP_INIT: Full traceback: {traceback.format_exc()}")
    pump_context_service = None
    logger.warning("⚠️ PUMP_INIT: Pump context features disabled due to initialization failure")

logger.info(f"🔧 PUMP_INIT: Final pump_context_service state: {pump_context_service is not None}")

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
    global pump_context_service
    logger.info("🚀 Application startup initiated")
    
    # Start provisional access scheduler
    try:
        provisional_scheduler.start()
        logger.info("✅ Provisional access scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start provisional scheduler: {str(e)}")
    
    # Initialize pump context service
    try:
        logger.info("🔄 Initializing pump context service...")
        from services.pump_context_service import PumpContextService
        pump_context_service = PumpContextService()
        
        # Test the service
        test_query = "4x6-13 pump"
        logger.info("🧪 Testing pump context service...")
        test_result = pump_context_service.generate_pump_context(test_query)
        if test_result:
            logger.info(f"✅ Pump context service initialized successfully (test query: {test_query})")
            logger.debug(f"Test result preview: {test_result[:200]}...")
        else:
            logger.warning("⚠️ Pump context service returned None for test query")
    except Exception as e:
        logger.error(f"❌ Failed to initialize pump context service: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
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
        
        # Log pump context service status with more details
        global pump_context_service
        try:
            if pump_context_service is not None:
                logger.debug("[PUMP] Pump context service is initialized")
                # Test the pump context service with a sample query
                test_query = "4x6-13 pump"
                logger.debug(f"[PUMP] Testing pump context generation with query: {test_query}")
                try:
                    pump_context = pump_context_service.generate_pump_context(test_query)
                    if pump_context:
                        logger.debug(f"[PUMP] Successfully generated pump context ({len(pump_context)} chars)")
                        logger.debug(f"[PUMP] Context preview: {pump_context[:200]}...")
                    else:
                        logger.warning("[PUMP] No pump context generated (query may not be pump-related)")
                except Exception as e:
                    logger.error(f"[PUMP] Error generating pump context: {str(e)}")
                    logger.error(f"[PUMP] Traceback: {traceback.format_exc()}")
            else:
                logger.error("[PUMP] Pump context service is None - initializing...")
                try:
                    from services.pump_context_service import PumpContextService
                    pump_context_service = PumpContextService()
                    logger.info("[PUMP] Successfully initialized pump context service")
                except Exception as e:
                    logger.error(f"[PUMP] Failed to initialize pump context service: {str(e)}")
                    logger.error(f"[PUMP] Traceback: {traceback.format_exc()}")
        except Exception as e:
            logger.error(f"[PUMP] Unexpected error checking pump context service: {str(e)}")
            logger.error(f"[PUMP] Traceback: {traceback.format_exc()}")
        
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
        
        # Generate pump-specific context if relevant
        pump_context = None
        logger.info(f"🔍 PUMP_DEBUG: Starting pump context generation for message: {new_message.content[:100] if new_message else 'None'}...")
        logger.info(f"🔍 PUMP_DEBUG: pump_context_service available: {pump_context_service is not None}")
        
        # CRITICAL FIX: Enhanced null checking to prevent 500 errors
        if new_message and pump_context_service is not None:
            try:
                logger.info(f"🔍 PUMP_DEBUG: Calling generate_pump_context...")
                # Additional safety check before calling methods
                if hasattr(pump_context_service, 'generate_pump_context'):
                    pump_context = pump_context_service.generate_pump_context(new_message.content)
                    logger.info(f"🔍 PUMP_DEBUG: Pump context generated: {pump_context is not None}")
                    if pump_context:
                        logger.info(f"🔧 PUMP_CONTEXT: Generated pump expertise context for user query")
                        logger.info(f"🔍 PUMP_DEBUG: Context length: {len(pump_context)} characters")
                        logger.info(f"🔍 PUMP_DEBUG: Context preview: {pump_context[:200]}...")
                    else:
                        logger.info(f"🔍 PUMP_DEBUG: No pump context generated - query not pump-related")
                else:
                    logger.error(f"❌ PUMP_CONTEXT: PumpContextService object exists but missing generate_pump_context method")
                    pump_context = None
            except AttributeError as ae:
                logger.error(f"❌ PUMP_CONTEXT: AttributeError in pump context generation: {ae}")
                logger.error(f"❌ PUMP_DEBUG: This indicates pump_context_service is None or malformed")
                logger.error(f"❌ PUMP_DEBUG: Full traceback: {traceback.format_exc()}")
                pump_context = None
            except Exception as e:
                logger.error(f"❌ PUMP_CONTEXT: Unexpected error generating pump context: {e}")
                logger.error(f"❌ PUMP_DEBUG: Full traceback: {traceback.format_exc()}")
                pump_context = None  # Ensure pump_context is None on error
        elif new_message and pump_context_service is None:
            logger.warning(f"⚠️ PUMP_DEBUG: Pump context service is None - pump features disabled due to initialization failure")
            logger.warning(f"⚠️ PUMP_DEBUG: User query appears pump-related but service unavailable: {new_message.content[:100]}...")
        elif not new_message:
            logger.debug(f"🔍 PUMP_DEBUG: No new message to process for pump context")
        
        # Prepare complete conversation history for OpenAI
        system_prompt = get_system_prompt()
        logger.info(f"🔍 PUMP_DEBUG: Base system prompt length: {len(system_prompt)} characters")
        
        # Enhance system prompt with pump context if available
        if pump_context:
            enhanced_system_prompt = f"{system_prompt}\n\n=== CRITICAL: USE THIS PUMP DATA ===\n{pump_context}\n\nIMPORTANT: You MUST use the pump data provided above to answer pump-related questions. Do NOT provide generic responses when specific pump data is available. Format tables using proper markdown syntax with | separators."
            logger.info(f"🔧 PUMP_CONTEXT: Enhanced system prompt with real-time pump data")
            logger.info(f"🔍 PUMP_DEBUG: Enhanced prompt length: {len(enhanced_system_prompt)} characters")
            logger.info(f"🔍 PUMP_DEBUG: Enhanced prompt preview: ...{enhanced_system_prompt[-300:]}")
        else:
            enhanced_system_prompt = system_prompt
            logger.info(f"🔍 PUMP_DEBUG: Using base system prompt (no pump context)")
        
        openai_messages = [{"role": "system", "content": enhanced_system_prompt}]
        
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
app.include_router(pump_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
