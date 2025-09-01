"""
Abstract interface for content recommendation services
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models import ContentRecommendation, Course, YouTubeVideo, UserContext, SkillLevel


class ContentFilters:
    """Filters for content search and recommendation"""
    
    def __init__(
        self,
        max_duration: int = None,
        is_free: bool = None,
        min_rating: float = None,
        content_types: List[str] = None,
        difficulty_level: str = None
    ):
        self.max_duration = max_duration
        self.is_free = is_free
        self.min_rating = min_rating
        self.content_types = content_types or []
        self.difficulty_level = difficulty_level


class ContentRecommenderInterface(ABC):
    """Abstract base class for content recommendation services"""
    
    @abstractmethod
    async def search_youtube_content(self, query: str, filters: ContentFilters) -> List[YouTubeVideo]:
        """
        Search for YouTube educational content
        
        Args:
            query: Search query string
            filters: Content filtering criteria
            
        Returns:
            List of relevant YouTube videos
        """
        pass
    
    @abstractmethod
    async def search_courses(self, skill: str, level: SkillLevel) -> List[Course]:
        """
        Search for courses on various platforms
        
        Args:
            skill: Target skill name
            level: User's current skill level
            
        Returns:
            List of relevant courses
        """
        pass
    
    @abstractmethod
    async def filter_by_preferences(
        self, 
        content: List[ContentRecommendation], 
        preferences: Dict[str, Any]
    ) -> List[ContentRecommendation]:
        """
        Filter content based on user preferences
        
        Args:
            content: List of content recommendations
            preferences: User preference dictionary
            
        Returns:
            Filtered list of content recommendations
        """
        pass
    
    @abstractmethod
    async def rank_content(
        self, 
        content: List[ContentRecommendation], 
        user_context: UserContext
    ) -> List[ContentRecommendation]:
        """
        Rank content based on user context and relevance
        
        Args:
            content: List of content recommendations
            user_context: Current user context
            
        Returns:
            Ranked list of content recommendations
        """
        pass