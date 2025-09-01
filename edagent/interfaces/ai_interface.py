"""
Abstract interface for AI service implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models import UserContext, SkillAssessment, LearningPath, SkillLevel


class AIServiceInterface(ABC):
    """Abstract base class for AI service implementations"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: UserContext) -> str:
        """
        Generate a conversational response using AI
        
        Args:
            prompt: User's input message
            context: Current user context and conversation history
            
        Returns:
            AI-generated response string
        """
        pass
    
    @abstractmethod
    async def assess_skills(self, responses: List[str]) -> SkillAssessment:
        """
        Assess user skills based on their responses
        
        Args:
            responses: List of user responses to assessment questions
            
        Returns:
            Structured skill assessment results
        """
        pass
    
    @abstractmethod
    async def create_learning_path(self, goal: str, current_skills: Dict[str, SkillLevel]) -> LearningPath:
        """
        Create a personalized learning path
        
        Args:
            goal: User's career or learning goal
            current_skills: User's current skill levels
            
        Returns:
            Structured learning path with milestones
        """
        pass
    
    @abstractmethod
    def build_system_prompt(self, user_context: UserContext) -> str:
        """
        Build context-aware system prompt
        
        Args:
            user_context: Current user context
            
        Returns:
            Formatted system prompt string
        """
        pass