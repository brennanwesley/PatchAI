"""
JWT authentication and authorization utilities
"""

import os
import jwt
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_JWT_SECRET:
    logger.warning("SUPABASE_JWT_SECRET not found - JWT verification will fail")


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user ID - SECURITY: Signature verification enabled"""
    try:
        if not SUPABASE_JWT_SECRET:
            logger.error("🚨 SUPABASE_JWT_SECRET not configured - this will cause authentication failures")
            logger.error("🚨 Please set SUPABASE_JWT_SECRET environment variable in Render")
            raise HTTPException(status_code=500, detail="Authentication configuration error - JWT secret missing")
        
        # DEBUG: Log token details for debugging
        token = credentials.credentials
        logger.info(f"🔐 Attempting JWT verification...")
        logger.info(f"🔐 Token preview: {token[:50]}...")
        logger.info(f"🔐 JWT secret present: {bool(SUPABASE_JWT_SECRET)}")
        logger.info(f"🔐 JWT secret length: {len(SUPABASE_JWT_SECRET) if SUPABASE_JWT_SECRET else 0}")
        
        # SECURITY: Verify JWT signature with secret
        payload = jwt.decode(
            credentials.credentials, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            options={
                "verify_signature": True,  # CRITICAL: Signature verification enabled
                "verify_aud": False        # FIXED: Disable audience verification for Supabase tokens
            }
        )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token missing user ID (sub claim)")
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        logger.info(f"✅ JWT verification successful for user: {user_id}")
        return user_id
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"🚨 JWT token validation failed: {str(e)}")
        logger.error(f"🚨 Token type: {type(e).__name__}")
        logger.error(f"🚨 Full error: {repr(e)}")
        logger.error(f"🚨 This usually means SUPABASE_JWT_SECRET is incorrect or missing")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"🚨 Unexpected error during JWT verification: {str(e)}")
        logger.error(f"🚨 Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
