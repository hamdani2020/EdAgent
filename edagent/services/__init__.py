"""
Service layer for EdAgent application
"""

from .user_context_manager import UserContextManager
from .content_recommender import ContentRecommender, YouTubeContentFilters

__all__ = [
    "UserContextManager",
    "ContentRecommender", 
    "YouTubeContentFilters",
]