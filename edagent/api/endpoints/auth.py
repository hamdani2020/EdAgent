"""
Authentication endpoints for EdAgent API
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from datetime import datetime

from ...services.auth_service import AuthenticationService
from ...models.auth import AuthenticationRequest, TokenValidationResult
from ...config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response models
class SessionCreateRequest(BaseModel):
    """Request model for creating a session"""
    user_id: str = Field(..., description="User ID to create session for")
    session_duration_minutes: int = Field(
        default=1440, 
        description="Session duration in minutes (default: 24 hours)"
    )


class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    session_token: str = Field(..., description="JWT session token")
    user_id: str = Field(..., description="User ID")
    expires_at: datetime = Field(..., description="Session expiration time")
    session_id: str = Field(..., description="Session ID")


class SessionValidateResponse(BaseModel):
    """Response model for session validation"""
    is_valid: bool = Field(..., description="Whether the session is valid")
    user_id: Optional[str] = Field(None, description="User ID if valid")
    session_id: Optional[str] = Field(None, description="Session ID if valid")
    expires_at: Optional[datetime] = Field(None, description="Session expiration time")


class APIKeyCreateRequest(BaseModel):
    """Request model for creating an API key"""
    user_id: str = Field(..., description="User ID to create API key for")
    name: str = Field(..., description="Human-readable name for the API key")
    permissions: List[str] = Field(default=[], description="List of permissions")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")
    rate_limit_per_minute: Optional[int] = Field(None, description="Rate limit per minute")


class APIKeyCreateResponse(BaseModel):
    """Response model for API key creation"""
    api_key: str = Field(..., description="The generated API key")
    key_id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class APIKeyValidateResponse(BaseModel):
    """Response model for API key validation"""
    is_valid: bool = Field(..., description="Whether the API key is valid")
    user_id: Optional[str] = Field(None, description="User ID if valid")
    key_id: Optional[str] = Field(None, description="API key ID if valid")


# Dependency to get auth service
def get_auth_service() -> AuthenticationService:
    """Get authentication service instance"""
    return AuthenticationService()


@router.post("/session", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    http_request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Create a new user session
    
    Creates a new authenticated session for a user and returns a JWT token.
    The token should be included in the Authorization header as 'Bearer <token>'
    for subsequent requests.
    """
    try:
        # Extract client info from request
        client_ip = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        # Create authentication request
        auth_request = AuthenticationRequest(
            user_id=request.user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            session_duration_minutes=request.session_duration_minutes
        )
        
        # Create session
        response = await auth_service.create_session(auth_request)
        
        return SessionCreateResponse(
            session_token=response.session_token,
            user_id=response.user_id,
            expires_at=response.expires_at,
            session_id=response.session_id
        )
        
    except ValueError as e:
        logger.warning(f"Session creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


class SessionValidateRequest(BaseModel):
    """Request model for session validation"""
    token: str = Field(..., description="Session token to validate")


@router.post("/session/validate", response_model=SessionValidateResponse)
async def validate_session(
    request: SessionValidateRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Validate a session token
    
    Validates a JWT session token and returns session information if valid.
    """
    try:
        result = await auth_service.validate_session_token(request.token)
        
        response = SessionValidateResponse(
            is_valid=result.is_valid,
            user_id=result.user_id,
            session_id=result.session_id
        )
        
        if result.session:
            response.expires_at = result.session.expires_at
        
        return response
        
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate session"
        )


@router.delete("/session/{session_id}")
async def revoke_session(
    session_id: str,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Revoke a user session
    
    Revokes an active session, making the associated token invalid.
    """
    try:
        success = await auth_service.revoke_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session revocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@router.post("/api-key", response_model=APIKeyCreateResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Create a new API key
    
    Creates a new API key for a user. The API key should be included
    in the X-API-Key header for subsequent requests.
    """
    try:
        api_key, key_id = await auth_service.create_api_key(
            user_id=request.user_id,
            name=request.name,
            permissions=request.permissions,
            expires_in_days=request.expires_in_days,
            rate_limit_per_minute=request.rate_limit_per_minute
        )
        
        # Calculate expiration date if provided
        expires_at = None
        if request.expires_in_days:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        return APIKeyCreateResponse(
            api_key=api_key,
            key_id=key_id,
            name=request.name,
            expires_at=expires_at
        )
        
    except ValueError as e:
        logger.warning(f"API key creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"API key creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


class APIKeyValidateRequest(BaseModel):
    """Request model for API key validation"""
    api_key: str = Field(..., description="API key to validate")


@router.post("/api-key/validate", response_model=APIKeyValidateResponse)
async def validate_api_key(
    request: APIKeyValidateRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Validate an API key
    
    Validates an API key and returns user information if valid.
    """
    try:
        result = await auth_service.validate_api_key(request.api_key)
        
        return APIKeyValidateResponse(
            is_valid=result.is_valid,
            user_id=result.user_id,
            key_id=result.session_id  # session_id contains key_id for API keys
        )
        
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate API key"
        )


@router.delete("/api-key/{key_id}")
async def revoke_api_key(
    key_id: str,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Revoke an API key
    
    Revokes an active API key, making it invalid for future requests.
    """
    try:
        success = await auth_service.revoke_api_key(key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key revocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.post("/cleanup")
async def cleanup_expired_sessions(
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Clean up expired sessions
    
    Administrative endpoint to clean up expired sessions from the database.
    This is typically called by a scheduled task.
    """
    try:
        cleaned_count = await auth_service.cleanup_expired_sessions()
        
        return {
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Session cleanup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup sessions"
        )