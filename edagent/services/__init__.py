"""
Service layer for EdAgent application
"""

from .user_context_manager import UserContextManager
from .content_recommender import ContentRecommender, YouTubeContentFilters
from .conversation_manager import ConversationManager
from .ai_service import GeminiAIService

__all__ = [
    "UserContextManager",
    "ContentRecommender", 
    "YouTubeContentFilters",
    "ConversationManager",
    "GeminiAIService",
]