"""
Dependency injection for EdAgent API
"""

import logging
from functools import lru_cache
from typing import Optional

from ..services.conversation_manager import ConversationManager
from ..services.user_context_manager import UserContextManager
from ..services.learning_path_generator import EnhancedLearningPathGenerator
from ..services.ai_service import GeminiAIService
from ..services.content_recommender import ContentRecommender
from ..database.connection import db_manager
from ..config import get_settings


logger = logging.getLogger(__name__)


# Global service instances
_conversation_manager: Optional[ConversationManager] = None
_user_context_manager: Optional[UserContextManager] = None
_learning_path_generator: Optional[EnhancedLearningPathGenerator] = None
_ai_service: Optional[GeminiAIService] = None
_content_recommender: Optional[ContentRecommender] = None


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


async def cleanup_dependencies():
    """Cleanup global service instances"""
    global _conversation_manager, _user_context_manager, _learning_path_generator
    global _ai_service, _content_recommender
    
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
    
    logger.info("Dependencies cleaned up")