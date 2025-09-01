"""
Database utility functions for common operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import User, UserSkill, Conversation, LearningPath, Milestone, ContentRecommendation

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Utility class for common database operations"""
    
    @staticmethod
    async def create_user(session: AsyncSession, preferences: Optional[Dict[str, Any]] = None) -> User:
        """
        Create a new user with optional preferences
        
        Args:
            session: Database session
            preferences: User preferences dictionary
            
        Returns:
            Created user instance
        """
        user = User(preferences=preferences or {})
        session.add(user)
        await session.flush()  # Get the ID without committing
        logger.info(f"Created new user with ID: {user.id}")
        return user
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
        """
        Get user by ID with all relationships loaded
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            User instance or None if not found
        """
        result = await session.execute(
            select(User)
            .options(
                selectinload(User.skills),
                selectinload(User.conversations),
                selectinload(User.learning_paths).selectinload(LearningPath.milestones)
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user_preferences(
        session: AsyncSession, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences
        
        Args:
            session: Database session
            user_id: User ID
            preferences: New preferences dictionary
            
        Returns:
            True if updated successfully, False if user not found
        """
        result = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(preferences=preferences, last_active=datetime.utcnow())
        )
        success = result.rowcount > 0
        if success:
            logger.info(f"Updated preferences for user {user_id}")
        return success
    
    @staticmethod
    async def upsert_user_skill(
        session: AsyncSession,
        user_id: str,
        skill_name: str,
        level: str,
        confidence_score: float
    ) -> UserSkill:
        """
        Insert or update a user skill
        
        Args:
            session: Database session
            user_id: User ID
            skill_name: Name of the skill
            level: Skill level (beginner, intermediate, advanced)
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            UserSkill instance
        """
        # Try to get existing skill
        result = await session.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .where(UserSkill.skill_name == skill_name)
        )
        existing_skill = result.scalar_one_or_none()
        
        if existing_skill:
            # Update existing skill
            existing_skill.level = level
            existing_skill.confidence_score = confidence_score
            existing_skill.updated_at = datetime.utcnow()
            skill = existing_skill
            logger.info(f"Updated skill {skill_name} for user {user_id}")
        else:
            # Create new skill
            skill = UserSkill(
                user_id=user_id,
                skill_name=skill_name,
                level=level,
                confidence_score=confidence_score
            )
            session.add(skill)
            logger.info(f"Created new skill {skill_name} for user {user_id}")
        
        return skill
    
    @staticmethod
    async def get_user_skills(session: AsyncSession, user_id: str) -> List[UserSkill]:
        """
        Get all skills for a user
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            List of UserSkill instances
        """
        result = await session.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.updated_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def add_conversation(
        session: AsyncSession,
        user_id: str,
        message: str,
        response: str,
        message_type: str = "general",
        context_data: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Add a conversation entry
        
        Args:
            session: Database session
            user_id: User ID
            message: User message
            response: AI response
            message_type: Type of message (general, assessment, etc.)
            context_data: Additional context data
            
        Returns:
            Conversation instance
        """
        conversation = Conversation(
            user_id=user_id,
            message=message,
            response=response,
            message_type=message_type,
            context_data=context_data or {}
        )
        session.add(conversation)
        logger.info(f"Added conversation entry for user {user_id}, type: {message_type}")
        return conversation
    
    @staticmethod
    async def get_conversation_history(
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
        message_type: Optional[str] = None
    ) -> List[Conversation]:
        """
        Get conversation history for a user
        
        Args:
            session: Database session
            user_id: User ID
            limit: Maximum number of conversations to return
            message_type: Filter by message type (optional)
            
        Returns:
            List of Conversation instances
        """
        query = select(Conversation).where(Conversation.user_id == user_id)
        
        if message_type:
            query = query.where(Conversation.message_type == message_type)
        
        query = query.order_by(Conversation.timestamp.desc()).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_learning_path(
        session: AsyncSession,
        user_id: str,
        goal: str,
        estimated_duration_days: Optional[int] = None,
        difficulty_level: Optional[str] = None
    ) -> LearningPath:
        """
        Create a new learning path
        
        Args:
            session: Database session
            user_id: User ID
            goal: Learning goal description
            estimated_duration_days: Estimated duration in days
            difficulty_level: Difficulty level
            
        Returns:
            LearningPath instance
        """
        learning_path = LearningPath(
            user_id=user_id,
            goal=goal,
            estimated_duration_days=estimated_duration_days,
            difficulty_level=difficulty_level
        )
        session.add(learning_path)
        await session.flush()  # Get the ID
        logger.info(f"Created learning path for user {user_id}: {goal}")
        return learning_path
    
    @staticmethod
    async def add_milestone(
        session: AsyncSession,
        learning_path_id: str,
        title: str,
        description: Optional[str] = None,
        order_index: int = 0,
        estimated_hours: Optional[int] = None,
        prerequisites: Optional[List[str]] = None
    ) -> Milestone:
        """
        Add a milestone to a learning path
        
        Args:
            session: Database session
            learning_path_id: Learning path ID
            title: Milestone title
            description: Milestone description
            order_index: Order in the learning path
            estimated_hours: Estimated hours to complete
            prerequisites: List of prerequisite milestone IDs or skills
            
        Returns:
            Milestone instance
        """
        milestone = Milestone(
            learning_path_id=learning_path_id,
            title=title,
            description=description,
            order_index=order_index,
            estimated_hours=estimated_hours,
            prerequisites=prerequisites or []
        )
        session.add(milestone)
        logger.info(f"Added milestone to learning path {learning_path_id}: {title}")
        return milestone
    
    @staticmethod
    async def complete_milestone(
        session: AsyncSession,
        milestone_id: str
    ) -> bool:
        """
        Mark a milestone as completed
        
        Args:
            session: Database session
            milestone_id: Milestone ID
            
        Returns:
            True if updated successfully, False if milestone not found
        """
        result = await session.execute(
            update(Milestone)
            .where(Milestone.id == milestone_id)
            .values(is_completed=True, completed_at=datetime.utcnow())
        )
        success = result.rowcount > 0
        if success:
            logger.info(f"Marked milestone {milestone_id} as completed")
        return success
    
    @staticmethod
    async def get_active_learning_paths(
        session: AsyncSession,
        user_id: str
    ) -> List[LearningPath]:
        """
        Get active learning paths for a user
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            List of active LearningPath instances with milestones
        """
        result = await session.execute(
            select(LearningPath)
            .options(selectinload(LearningPath.milestones))
            .where(LearningPath.user_id == user_id)
            .where(LearningPath.is_active == True)
            .order_by(LearningPath.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def cache_content_recommendation(
        session: AsyncSession,
        title: str,
        url: str,
        platform: str,
        content_type: str,
        duration_minutes: Optional[int] = None,
        rating: Optional[float] = None,
        is_free: bool = True,
        skill_tags: Optional[List[str]] = None,
        difficulty_level: Optional[str] = None
    ) -> ContentRecommendation:
        """
        Cache a content recommendation
        
        Args:
            session: Database session
            title: Content title
            url: Content URL
            platform: Platform name (youtube, coursera, etc.)
            content_type: Type of content (video, course, etc.)
            duration_minutes: Duration in minutes
            rating: Content rating
            is_free: Whether content is free
            skill_tags: List of relevant skill tags
            difficulty_level: Difficulty level
            
        Returns:
            ContentRecommendation instance
        """
        content = ContentRecommendation(
            title=title,
            url=url,
            platform=platform,
            content_type=content_type,
            duration_minutes=duration_minutes,
            rating=rating,
            is_free=is_free,
            skill_tags=skill_tags or [],
            difficulty_level=difficulty_level
        )
        session.add(content)
        logger.info(f"Cached content recommendation: {title} from {platform}")
        return content
    
    @staticmethod
    async def search_cached_content(
        session: AsyncSession,
        skill_tags: List[str],
        content_type: Optional[str] = None,
        is_free: Optional[bool] = None,
        limit: int = 10
    ) -> List[ContentRecommendation]:
        """
        Search cached content recommendations
        
        Args:
            session: Database session
            skill_tags: List of skill tags to search for
            content_type: Filter by content type
            is_free: Filter by free/paid content
            limit: Maximum number of results
            
        Returns:
            List of ContentRecommendation instances
        """
        query = select(ContentRecommendation)
        
        # Filter by skill tags (PostgreSQL JSON contains, SQLite fallback)
        if skill_tags:
            # This works for PostgreSQL with JSON column
            # For SQLite, we'd need a different approach
            for tag in skill_tags:
                query = query.where(ContentRecommendation.skill_tags.contains([tag]))
        
        if content_type:
            query = query.where(ContentRecommendation.content_type == content_type)
        
        if is_free is not None:
            query = query.where(ContentRecommendation.is_free == is_free)
        
        query = query.order_by(ContentRecommendation.rating.desc()).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def cleanup_old_conversations(
        session: AsyncSession,
        days_to_keep: int = 30
    ) -> int:
        """
        Clean up old conversation records
        
        Args:
            session: Database session
            days_to_keep: Number of days to keep conversations
            
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = await session.execute(
            delete(Conversation)
            .where(Conversation.timestamp < cutoff_date)
        )
        
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old conversation records")
        
        return deleted_count