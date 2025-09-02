"""
Dependency injection for EdAgent API
"""

import logging
from functools import lru_cache
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.conversation_manager import ConversationManager
from ..services.user_context_manager import UserContextManager
from ..services.learning_path_generator import EnhancedLearningPathGenerator
from ..services.ai_service import GeminiAIService
from ..services.content_recommender import ContentRecommender
from ..services.auth_service import AuthenticationService
from ..database.connection import db_manager
from ..config import get_settings


logger = logging.getLogger(__name__)


# Global service instances
_conversation_manager: Optional[ConversationManager] = None
_user_context_manager: Optional[UserContextManager] = None
_learning_path_generator: Optional[EnhancedLearningPathGenerator] = None
_ai_service: Optional[GeminiAIService] = None
_content_recommender: Optional[ContentRecommender] = None
_auth_service: Optional[AuthenticationService] = None


@lru_cache()
def get_ai_service() -> GeminiAIService:
    """Get AI service instance"""
    global _ai_service
    if _ai_service is None:
        settings = get_settings()
        _ai_service = GeminiAIService()
    return _ai_service


@lru_cache()
def get_content_recommender() -> ContentRecommender:
    """Get content recommender instance"""
    global _content_recommender
    if _content_recommender is None:
        settings = get_settings()
        _content_recommender = ContentRecommender(settings)
    return _content_recommender


@lru_cache()
def get_user_context_manager() -> UserContextManager:
    """Get user context manager instance"""
    global _user_context_manager
    if _user_context_manager is None:
        _user_context_manager = UserContextManager()
    return _user_context_manager


@lru_cache()
def get_learning_path_generator() -> EnhancedLearningPathGenerator:
    """Get learning path generator instance"""
    global _learning_path_generator
    if _learning_path_generator is None:
        ai_service = get_ai_service()
        content_recommender = get_content_recommender()
        user_context_manager = get_user_context_manager()
        
        _learning_path_generator = EnhancedLearningPathGenerator()
    return _learning_path_generator


@lru_cache()
def get_auth_service() -> AuthenticationService:
    """Get authentication service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service


@lru_cache()
def get_conversation_manager() -> ConversationManager:
    """Get conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        ai_service = get_ai_service()
        user_context_manager = get_user_context_manager()
        content_recommender = get_content_recommender()
        learning_path_generator = get_learning_path_generator()
        
        _conversation_manager = ConversationManager()
    return _conversation_manager


# Security scheme for Bearer token authentication
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token or API key
    
    This dependency validates the authentication token and returns user information.
    It supports both JWT session tokens and API keys.
    """
    auth_service = get_auth_service()
    
    try:
        # Try to validate as JWT session token first
        token = credentials.credentials
        result = await auth_service.validate_session_token(token)
        
        if result.is_valid:
            return {
                "user_id": result.user_id,
                "session_id": result.session_id,
                "auth_type": "session"
            }
        
        # If JWT validation fails, try as API key
        api_result = await auth_service.validate_api_key(token)
        
        if api_result.is_valid:
            return {
                "user_id": api_result.user_id,
                "session_id": api_result.session_id,
                "auth_type": "api_key"
            }
        
        # If both fail, check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if api_key:
            api_result = await auth_service.validate_api_key(api_key)
            if api_result.is_valid:
                return {
                    "user_id": api_result.user_id,
                    "session_id": api_result.session_id,
                    "auth_type": "api_key"
                }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def cleanup_dependencies():
    """Cleanup global service instances"""
    global _conversation_manager, _user_context_manager, _learning_path_generator
    global _ai_service, _content_recommender, _auth_service
    
    # Close any resources that need cleanup
    if _user_context_manager:
        # Close database connections if needed
        pass
    
    # Reset instances
    _conversation_manager = None
    _user_context_manager = None
    _learning_path_generator = None
    _ai_service = None
    _content_recommender = None
    _auth_service = None
    
    logger.info("Dependencies cleaned up")