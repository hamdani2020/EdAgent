"""
User context management service implementation
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.user_context_interface import UserContextInterface
from ..models.user_context import UserContext, SkillLevel, UserPreferences, SkillLevelEnum, LearningStyleEnum
from ..models.conversation import Message, MessageType
from ..database import DatabaseUtils, get_database_connection
from ..database.models import User as DBUser, UserSkill as DBUserSkill, Conversation as DBConversation

logger = logging.getLogger(__name__)


class UserContextManager(UserContextInterface):
    """
    Service for managing user context, skills, and preferences
    """
    
    def __init__(self):
        self.db_utils = DatabaseUtils()
    
    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """
        Retrieve user context by ID
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User context if found, None otherwise
        """
        try:
            async with get_database_connection() as session:
                # Get user from database
                db_user = await self.db_utils.get_user_by_id(session, user_id)
                if not db_user:
                    logger.info(f"User {user_id} not found in database")
                    return None
                
                # Convert database user to UserContext
                user_context = await self._db_user_to_context(db_user)
                logger.info(f"Retrieved user context for {user_id}")
                return user_context
                
        except Exception as e:
            logger.error(f"Error retrieving user context for {user_id}: {e}")
            return None
    
    async def create_user_context(self, user_id: str, preferences: Optional[Dict[str, Any]] = None) -> UserContext:
        """
        Create new user context
        
        Args:
            user_id: Unique user identifier
            preferences: Optional initial preferences
            
        Returns:
            Newly created user context
        """
        try:
            async with get_database_connection() as session:
                # Create user in database
                db_user = await self.db_utils.create_user(session, preferences or {})
                
                # Create UserContext object
                user_context = UserContext(
                    user_id=str(db_user.id),
                    created_at=db_user.created_at,
                    last_active=db_user.last_active or db_user.created_at
                )
                
                # Set preferences if provided
                if preferences:
                    try:
                        user_prefs = UserPreferences.from_dict(preferences)
                        user_context.learning_preferences = user_prefs
                    except Exception as e:
                        logger.warning(f"Could not parse preferences for user {user_id}: {e}")
                
                logger.info(f"Created new user context for {user_context.user_id}")
                return user_context
                
        except Exception as e:
            logger.error(f"Error creating user context for {user_id}: {e}")
            raise
    
    async def update_skills(self, user_id: str, skills: Dict[str, SkillLevel]) -> None:
        """
        Update user's skill levels
        
        Args:
            user_id: Unique user identifier
            skills: Dictionary of skill names to skill levels
        """
        try:
            async with get_database_connection() as session:
                for skill_name, skill_level in skills.items():
                    await self.db_utils.upsert_user_skill(
                        session=session,
                        user_id=user_id,
                        skill_name=skill_name,
                        level=skill_level.level.value,
                        confidence_score=skill_level.confidence_score
                    )
                
                # Update user's last active timestamp
                await self.db_utils.update_user_preferences(
                    session, user_id, {}  # Empty dict to just update timestamp
                )
                
                logger.info(f"Updated {len(skills)} skills for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error updating skills for user {user_id}: {e}")
            raise
    
    async def save_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        """
        Save user preferences
        
        Args:
            user_id: Unique user identifier
            preferences: User learning preferences
        """
        try:
            async with get_database_connection() as session:
                # Convert preferences to dictionary
                prefs_dict = preferences.to_dict()
                
                # Update user preferences in database
                success = await self.db_utils.update_user_preferences(
                    session, user_id, prefs_dict
                )
                
                if not success:
                    raise ValueError(f"User {user_id} not found")
                
                logger.info(f"Saved preferences for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error saving preferences for user {user_id}: {e}")
            raise
    
    async def track_progress(self, user_id: str, milestone_id: str) -> None:
        """
        Track user progress on learning milestones
        
        Args:
            user_id: Unique user identifier
            milestone_id: ID of completed milestone
        """
        try:
            async with get_database_connection() as session:
                # Mark milestone as completed
                success = await self.db_utils.complete_milestone(session, milestone_id)
                
                if not success:
                    logger.warning(f"Milestone {milestone_id} not found or already completed")
                    return
                
                # Update user's last active timestamp
                await self.db_utils.update_user_preferences(
                    session, user_id, {}  # Empty dict to just update timestamp
                )
                
                logger.info(f"Tracked progress for user {user_id}, milestone {milestone_id}")
                
        except Exception as e:
            logger.error(f"Error tracking progress for user {user_id}: {e}")
            raise
    
    async def save_assessment_results(self, user_id: str, assessment_results: Dict[str, Any]) -> None:
        """
        Save skill assessment results for a user
        
        Args:
            user_id: Unique user identifier
            assessment_results: Dictionary containing assessment results
        """
        try:
            async with get_database_connection() as session:
                # Get or create user
                db_user = await self.db_utils.get_user_by_id(session, user_id)
                if not db_user:
                    logger.warning(f"User {user_id} not found when saving assessment results")
                    return
                
                # Update user preferences with assessment results
                current_preferences = db_user.preferences or {}
                current_preferences['assessment_results'] = assessment_results
                current_preferences['last_assessment_date'] = datetime.now().isoformat()
                
                db_user.preferences = current_preferences
                db_user.last_active = datetime.now()
                
                await session.commit()
                logger.info(f"Saved assessment results for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error saving assessment results for user {user_id}: {e}")
            raise
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get user's conversation history
        
        Args:
            user_id: Unique user identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        try:
            async with get_database_connection() as session:
                # Get conversation history from database
                conversations = await self.db_utils.get_conversation_history(
                    session, user_id, limit
                )
                
                # Convert to message format
                messages = []
                for conv in conversations:
                    # Add user message
                    messages.append({
                        "id": f"{conv.id}_user",
                        "content": conv.message,
                        "message_type": "user",
                        "timestamp": conv.timestamp.isoformat(),
                        "metadata": conv.context_data
                    })
                    
                    # Add assistant response
                    messages.append({
                        "id": f"{conv.id}_assistant",
                        "content": conv.response,
                        "message_type": "assistant",
                        "timestamp": conv.timestamp.isoformat(),
                        "metadata": conv.context_data
                    })
                
                # Sort by timestamp (most recent first)
                messages.sort(key=lambda x: x["timestamp"], reverse=True)
                
                logger.info(f"Retrieved {len(messages)} messages for user {user_id}")
                return messages[:limit]
                
        except Exception as e:
            logger.error(f"Error retrieving conversation history for user {user_id}: {e}")
            return []
    
    async def add_conversation(
        self, 
        user_id: str, 
        user_message: str, 
        assistant_response: str,
        message_type: str = "general",
        context_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation entry to the user's history
        
        Args:
            user_id: Unique user identifier
            user_message: User's message
            assistant_response: Assistant's response
            message_type: Type of conversation (general, assessment, etc.)
            context_data: Additional context data
        """
        try:
            async with get_database_connection() as session:
                await self.db_utils.add_conversation(
                    session=session,
                    user_id=user_id,
                    message=user_message,
                    response=assistant_response,
                    message_type=message_type,
                    context_data=context_data
                )
                
                logger.info(f"Added conversation entry for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error adding conversation for user {user_id}: {e}")
            raise
    
    async def get_user_skills(self, user_id: str) -> Dict[str, SkillLevel]:
        """
        Get all skills for a user
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dictionary of skill names to SkillLevel objects
        """
        try:
            async with get_database_connection() as session:
                db_skills = await self.db_utils.get_user_skills(session, user_id)
                
                skills = {}
                for db_skill in db_skills:
                    skill_level = SkillLevel(
                        skill_name=db_skill.skill_name,
                        level=SkillLevelEnum(db_skill.level),
                        confidence_score=db_skill.confidence_score,
                        last_updated=db_skill.updated_at
                    )
                    skills[db_skill.skill_name] = skill_level
                
                logger.info(f"Retrieved {len(skills)} skills for user {user_id}")
                return skills
                
        except Exception as e:
            logger.error(f"Error retrieving skills for user {user_id}: {e}")
            return {}
    
    async def create_learning_path(
        self,
        user_id: str,
        goal: str,
        milestones: List[Dict[str, Any]],
        estimated_duration_days: Optional[int] = None,
        difficulty_level: Optional[str] = None
    ) -> str:
        """
        Create a learning path for the user
        
        Args:
            user_id: Unique user identifier
            goal: Learning goal description
            milestones: List of milestone dictionaries
            estimated_duration_days: Estimated duration in days
            difficulty_level: Difficulty level
            
        Returns:
            Learning path ID
        """
        try:
            async with get_database_connection() as session:
                # Create learning path
                learning_path = await self.db_utils.create_learning_path(
                    session=session,
                    user_id=user_id,
                    goal=goal,
                    estimated_duration_days=estimated_duration_days,
                    difficulty_level=difficulty_level
                )
                
                # Add milestones
                for i, milestone_data in enumerate(milestones):
                    await self.db_utils.add_milestone(
                        session=session,
                        learning_path_id=str(learning_path.id),
                        title=milestone_data.get("title", f"Milestone {i+1}"),
                        description=milestone_data.get("description"),
                        order_index=i,
                        estimated_hours=milestone_data.get("estimated_hours"),
                        prerequisites=milestone_data.get("prerequisites", [])
                    )
                
                logger.info(f"Created learning path for user {user_id}: {goal}")
                return str(learning_path.id)
                
        except Exception as e:
            logger.error(f"Error creating learning path for user {user_id}: {e}")
            raise
    
    async def get_active_learning_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active learning paths for a user
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of learning path dictionaries
        """
        try:
            async with get_database_connection() as session:
                learning_paths = await self.db_utils.get_active_learning_paths(session, user_id)
                
                paths = []
                for lp in learning_paths:
                    path_dict = {
                        "id": str(lp.id),
                        "goal": lp.goal,
                        "created_at": lp.created_at.isoformat(),
                        "estimated_duration_days": lp.estimated_duration_days,
                        "difficulty_level": lp.difficulty_level,
                        "completion_percentage": lp.completion_percentage,
                        "milestones": []
                    }
                    
                    # Add milestones
                    for milestone in lp.milestones:
                        milestone_dict = {
                            "id": str(milestone.id),
                            "title": milestone.title,
                            "description": milestone.description,
                            "order_index": milestone.order_index,
                            "is_completed": milestone.is_completed,
                            "completed_at": milestone.completed_at.isoformat() if milestone.completed_at else None,
                            "estimated_hours": milestone.estimated_hours,
                            "prerequisites": milestone.prerequisites
                        }
                        path_dict["milestones"].append(milestone_dict)
                    
                    # Sort milestones by order
                    path_dict["milestones"].sort(key=lambda x: x["order_index"])
                    paths.append(path_dict)
                
                logger.info(f"Retrieved {len(paths)} active learning paths for user {user_id}")
                return paths
                
        except Exception as e:
            logger.error(f"Error retrieving learning paths for user {user_id}: {e}")
            return []
    
    async def _db_user_to_context(self, db_user: DBUser) -> UserContext:
        """
        Convert database user to UserContext object
        
        Args:
            db_user: Database user object with relationships loaded
            
        Returns:
            UserContext object
        """
        # Convert skills
        skills = {}
        for db_skill in db_user.skills:
            skill_level = SkillLevel(
                skill_name=db_skill.skill_name,
                level=SkillLevelEnum(db_skill.level),
                confidence_score=db_skill.confidence_score,
                last_updated=db_skill.updated_at
            )
            skills[db_skill.skill_name] = skill_level
        
        # Convert preferences
        preferences = None
        if db_user.preferences:
            try:
                preferences = UserPreferences.from_dict(db_user.preferences)
            except Exception as e:
                logger.warning(f"Could not parse preferences for user {db_user.id}: {e}")
        
        # Get recent conversation history (last 10 messages)
        conversation_history = []
        recent_conversations = sorted(db_user.conversations, key=lambda x: x.timestamp, reverse=True)[:5]
        for conv in recent_conversations:
            conversation_history.extend([conv.message, conv.response])
        
        # Create UserContext
        user_context = UserContext(
            user_id=str(db_user.id),
            current_skills=skills,
            career_goals=[],  # TODO: Extract from preferences or conversations
            learning_preferences=preferences,
            conversation_history=conversation_history,
            assessment_results=None,  # TODO: Extract from conversation metadata
            created_at=db_user.created_at,
            last_active=db_user.last_active or db_user.created_at
        )
        
        return user_context