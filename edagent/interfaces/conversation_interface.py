"""
Abstract interface for conversation management
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import ConversationResponse, AssessmentSession, LearningPath, Message


class ConversationManagerInterface(ABC):
    """Abstract base class for conversation management"""
    
    @abstractmethod
    async def handle_message(self, user_id: str, message: str) -> ConversationResponse:
        """
        Handle incoming user message and generate response
        
        Args:
            user_id: Unique user identifier
            message: User's input message
            
        Returns:
            Structured conversation response
        """
        pass
    
    @abstractmethod
    async def start_skill_assessment(self, user_id: str) -> AssessmentSession:
        """
        Start a skill assessment session
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            New assessment session
        """
        pass
    
    @abstractmethod
    async def generate_learning_path(self, user_id: str, goal: str) -> LearningPath:
        """
        Generate a personalized learning path
        
        Args:
            user_id: Unique user identifier
            goal: User's learning or career goal
            
        Returns:
            Personalized learning path
        """
        pass
    
    @abstractmethod
    async def get_conversation_history(self, user_id: str) -> List[Message]:
        """
        Retrieve conversation history for a user
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of conversation messages
        """
        pass