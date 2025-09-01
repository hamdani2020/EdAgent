"""
Service layer for EdAgent application
"""

from .ai_service import AIService
from .user_context_manager import UserContextManager
from .content_recommender import ContentRecommender
from .conversation_manager import ConversationManager

__all__ = [
    "AIService",
    "UserContextManager", 
    "ContentRecommender",
    "ConversationManager",
]