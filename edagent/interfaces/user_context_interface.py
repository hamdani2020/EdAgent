"""
Abstract interface for user context management
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from ..models import UserContext, SkillLevel, UserPreferences, Milestone


class UserContextInterface(ABC):
    """Abstract base class for user context management"""
    
    @abstractmethod
    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """
        Retrieve user context by ID
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User context if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_user_context(self, user_id: str) -> UserContext:
        """
        Create new user context
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Newly created user context
        """
        pass
    
    @abstractmethod
    async def update_skills(self, user_id: str, skills: Dict[str, SkillLevel]) -> None:
        """
        Update user's skill levels
        
        Args:
            user_id: Unique user identifier
            skills: Dictionary of skill names to skill levels
        """
        pass
    
    @abstractmethod
    async def save_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        """
        Save user preferences
        
        Args:
            user_id: Unique user identifier
            preferences: User learning preferences
        """
        pass
    
    @abstractmethod
    async def track_progress(self, user_id: str, milestone: Milestone) -> None:
        """
        Track user progress on learning milestones
        
        Args:
            user_id: Unique user identifier
            milestone: Completed milestone
        """
        pass
    
    @abstractmethod
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get user's conversation history
        
        Args:
            user_id: Unique user identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        pass