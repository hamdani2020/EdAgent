"""
Base interfaces and abstract classes for EdAgent components
"""

from .ai_interface import AIServiceInterface
from .user_context_interface import UserContextInterface
from .content_interface import ContentRecommenderInterface
from .conversation_interface import ConversationManagerInterface

__all__ = [
    "AIServiceInterface",
    "UserContextInterface",
    "ContentRecommenderInterface", 
    "ConversationManagerInterface",
]