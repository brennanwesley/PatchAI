"""
Referral System Routes
Handles referral code signup, profile management, and referral tracking
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from core.auth import verify_jwt_token
from services.referral_service import ReferralService
from services.supabase_service import supabase
from models.schemas import (
    SignupWithReferralRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    ReferralInfoResponse,
    ReferralRewardsResponse,
    ValidateReferralCodeRequest
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/referrals", tags=["referrals"])

# Initialize referral service
referral_service = ReferralService(supabase)


@router.post("/signup", response_model=Dict[str, Any])
async def signup_with_referral(request: SignupWithReferralRequest):
    """
    Enhanced signup endpoint that accepts optional referral codes
    This endpoint handles user registration and referral relationship creation
    """
    try:
        logger.info(f"Processing signup for email: {request.email}, referral_code: {request.referral_code}")
        
        # Validate referral code if provided
        referring_user_info = None
        if request.referral_code:
            referring_user_info = await referral_service.validate_referral_code(request.referral_code)
            if not referring_user_info:
                logger.warning(f"Invalid referral code provided: {request.referral_code}")
                raise HTTPException(status_code=400, detail="Invalid referral code")
            
            logger.info(f"Valid referral code from user: {referring_user_info['referring_user_id']}")
        
        # Create user account using Supabase Auth
        try:
            auth_response = supabase.auth.sign_up({
                "email": request.email,
                "password": request.password
            })
            
            if not auth_response.user:
                logger.error(f"Failed to create user account for: {request.email}")
                raise HTTPException(status_code=400, detail="Failed to create user account")
            
            user_id = auth_response.user.id
            logger.info(f"Created user account: {user_id}")
            
        except Exception as e:
            logger.error(f"Supabase auth error for {request.email}: {e}")
            if "already registered" in str(e).lower():
                raise HTTPException(status_code=400, detail="Email already registered")
            raise HTTPException(status_code=500, detail="Account creation failed")
        
        # Generate referral code for new user
        try:
            user_referral_code = await referral_service.assign_referral_code_to_user(user_id)
            logger.info(f"Assigned referral code {user_referral_code} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to assign referral code to user {user_id}: {e}")
            # Don't fail signup if referral code assignment fails
            user_referral_code = None
        
        # Create referral relationship if referral code was used
        referral_relationship_created = False
        if referring_user_info:
            try:
                referral_relationship_created = await referral_service.create_referral_relationship(
                    referring_user_info['referring_user_id'],
                    user_id,
                    request.referral_code
                )
                
                if referral_relationship_created:
                    logger.info(f"Created referral relationship: {referring_user_info['referring_user_id']} -> {user_id}")
                else:
                    logger.warning(f"Failed to create referral relationship for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error creating referral relationship: {e}")
                # Don't fail signup if referral relationship creation fails
        
        return {
            "success": True,
            "user_id": user_id,
            "email": request.email,
            "referral_code": user_referral_code,
            "referral_relationship_created": referral_relationship_created,
            "referred_by": referring_user_info['referring_user_id'] if referring_user_info else None,
            "message": "Account created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile", response_model=ProfileResponse)
async def get_user_profile(user_id: str = Depends(verify_jwt_token)):
    """
    Get user profile including referral information
    """
    try:
        logger.info(f"Getting profile for user: {user_id}")
        
        # Get user profile from database
        profile_response = supabase.table("user_profiles").select(
            "id, email, display_name, company, referral_code, referred_by, "
            "subscription_status, plan_tier, created_at, updated_at"
        ).eq("id", user_id).single().execute()
        
        if not profile_response.data:
            logger.error(f"Profile not found for user: {user_id}")
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_data = profile_response.data
        
        # Ensure user has a referral code
        if not profile_data.get('referral_code'):
            try:
                referral_code = await referral_service.assign_referral_code_to_user(user_id)
                profile_data['referral_code'] = referral_code
                logger.info(f"Assigned missing referral code {referral_code} to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to assign referral code to user {user_id}: {e}")
        
        return ProfileResponse(**profile_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/profile", response_model=ProfileResponse)
async def update_user_profile(
    request: ProfileUpdateRequest,
    user_id: str = Depends(verify_jwt_token)
):
    """
    Update user profile information (display_name, phone, company)
    """
    try:
        logger.info(f"Updating profile for user: {user_id}")
        
        # Build update data
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if request.display_name is not None:
            update_data["display_name"] = request.display_name
        if request.company is not None:
            update_data["company"] = request.company
        
        # Update profile
        update_response = supabase.table("user_profiles").update(update_data).eq(
            "id", user_id
        ).execute()
        
        if not update_response.data:
            logger.error(f"Failed to update profile for user: {user_id}")
            raise HTTPException(status_code=400, detail="Failed to update profile")
        
        # Get updated profile
        profile_response = supabase.table("user_profiles").select(
            "id, email, display_name, company, referral_code, referred_by, "
            "subscription_status, plan_tier, created_at, updated_at"
        ).eq("id", user_id).single().execute()
        
        logger.info(f"Successfully updated profile for user: {user_id}")
        return ProfileResponse(**profile_response.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/info", response_model=ReferralInfoResponse)
async def get_referral_info(user_id: str = Depends(verify_jwt_token)):
    """
    Get comprehensive referral information for a user
    """
    try:
        logger.info(f"Getting referral info for user: {user_id}")
        
        referral_info = await referral_service.get_user_referral_info(user_id)
        
        if not referral_info:
            logger.warning(f"No referral info found for user: {user_id}")
            # Return empty response rather than error
            referral_info = {
                "user_id": user_id,
                "referral_code": None,
                "referred_by": None,
                "referring_user_info": None,
                "referrals_made": [],
                "total_referrals": 0
            }
        
        return ReferralInfoResponse(**referral_info)
        
    except Exception as e:
        logger.error(f"Error getting referral info for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/rewards", response_model=ReferralRewardsResponse)
async def get_referral_rewards(user_id: str = Depends(verify_jwt_token)):
    """
    Get referral rewards summary for a user
    """
    try:
        logger.info(f"Getting referral rewards for user: {user_id}")
        
        rewards_info = await referral_service.get_referral_rewards_summary(user_id)
        
        if not rewards_info:
            # Return empty response rather than error
            rewards_info = {
                "user_id": user_id,
                "total_rewards": 0.0,
                "total_paid": 0.0,
                "pending_rewards": 0.0,
                "rewards_history": []
            }
        
        return ReferralRewardsResponse(**rewards_info)
        
    except Exception as e:
        logger.error(f"Error getting referral rewards for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate-code")
async def validate_referral_code(request: ValidateReferralCodeRequest):
    """
    Validate a referral code (public endpoint for frontend validation)
    """
    try:
        referral_code = request.referral_code
        logger.info(f"Validating referral code: {referral_code}")
        
        if not referral_code or len(referral_code.strip()) != 6:
            return {"valid": False, "message": "Invalid code format"}
        
        referring_user_info = await referral_service.validate_referral_code(referral_code)
        
        if referring_user_info:
            return {
                "valid": True,
                "message": "Valid referral code",
                "referring_user_email": referring_user_info.get('referring_user_email', 'Unknown')
            }
        else:
            return {"valid": False, "message": "Referral code not found"}
            
    except Exception as e:
        logger.error(f"Error validating referral code {request.referral_code if hasattr(request, 'referral_code') else 'unknown'}: {e}")
        return {"valid": False, "message": "Validation error"}


@router.post("/generate-code")
async def generate_referral_code(user_id: str = Depends(verify_jwt_token)):
    """
    Generate or retrieve referral code for a user
    """
    try:
        logger.info(f"Generating/retrieving referral code for user: {user_id}")
        
        referral_code = await referral_service.assign_referral_code_to_user(user_id)
        
        return {
            "success": True,
            "referral_code": referral_code,
            "message": "Referral code ready"
        }
        
    except Exception as e:
        logger.error(f"Error generating referral code for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate referral code")
