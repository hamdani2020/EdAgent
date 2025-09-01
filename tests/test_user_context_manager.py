"""
Unit tests for UserContextManager service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from edagent.services.user_context_manager import UserContextManager
from edagent.models.user_context import UserContext, SkillLevel, UserPreferences, SkillLevelEnum, LearningStyleEnum
from edagent.database.models import User as DBUser, UserSkill as DBUserSkill, Conversation as DBConversation


class TestUserContextManager:
    """Test cases for UserContextManager"""
    
    @pytest.fixture
    def user_context_manager(self):
        """Create UserContextManager instance for testing"""
        return UserContextManager()
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample UserContext for testing"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week",
            budget_preference="free",
            preferred_platforms=["youtube", "coursera"],
            content_types=["video", "interactive"],
            difficulty_preference="gradual"
        )
        
        skills = {
            "python": SkillLevel(
                skill_name="python",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=0.6,
                last_updated=datetime.now()
            ),
            "javascript": SkillLevel(
                skill_name="javascript",
                level=SkillLevelEnum.INTERMEDIATE,
                confidence_score=0.8,
                last_updated=datetime.now()
            )
        }
        
        return UserContext(
            user_id="test-user-123",
            current_skills=skills,
            career_goals=["become a full-stack developer"],
            learning_preferences=preferences,
            conversation_history=["Hello", "Hi there!", "I want to learn Python"],
            assessment_results={"python": {"level": "beginner", "confidence": 0.6}},
            created_at=datetime.now() - timedelta(days=1),
            last_active=datetime.now()
        )
    
    @pytest.fixture
    def sample_db_user(self):
        """Create sample database user for testing"""
        user = DBUser(
            id="test-user-123",
            created_at=datetime.now() - timedelta(days=1),
            last_active=datetime.now(),
            preferences={
                "learning_style": "visual",
                "time_commitment": "2-3 hours/week",
                "budget_preference": "free"
            }
        )
        
        # Add skills
        skill1 = DBUserSkill(
            user_id="test-user-123",
            skill_name="python",
            level="beginner",
            confidence_score=0.6,
            updated_at=datetime.now()
        )
        skill2 = DBUserSkill(
            user_id="test-user-123",
            skill_name="javascript",
            level="intermediate",
            confidence_score=0.8,
            updated_at=datetime.now()
        )
        user.skills = [skill1, skill2]
        
        # Add conversations
        conv1 = DBConversation(
            id="conv-1",
            user_id="test-user-123",
            message="Hello",
            response="Hi there! How can I help you today?",
            timestamp=datetime.now() - timedelta(minutes=10),
            message_type="general",
            context_data={}
        )
        user.conversations = [conv1]
        user.learning_paths = []
        
        return user
    
    @pytest.mark.asyncio
    async def test_create_user_context_success(self, user_context_manager):
        """Test successful user context creation"""
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database user creation
            mock_db_user = DBUser(
                id="new-user-123",
                created_at=datetime.now(),
                last_active=datetime.now(),
                preferences={}
            )
            user_context_manager.db_utils.create_user = AsyncMock(return_value=mock_db_user)
            
            # Test creation
            result = await user_context_manager.create_user_context("new-user-123")
            
            assert isinstance(result, UserContext)
            assert result.user_id == "new-user-123"
            assert result.current_skills == {}
            assert result.career_goals == []
            assert result.learning_preferences is None
            
            # Verify database call
            user_context_manager.db_utils.create_user.assert_called_once_with(mock_session, {})
    
    @pytest.mark.asyncio
    async def test_create_user_context_with_preferences(self, user_context_manager):
        """Test user context creation with initial preferences"""
        preferences_dict = {
            "learning_style": "visual",
            "time_commitment": "2-3 hours/week",
            "budget_preference": "free"
        }
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_db_user = DBUser(
                id="new-user-123",
                created_at=datetime.now(),
                last_active=datetime.now(),
                preferences=preferences_dict
            )
            user_context_manager.db_utils.create_user = AsyncMock(return_value=mock_db_user)
            
            result = await user_context_manager.create_user_context("new-user-123", preferences_dict)
            
            assert isinstance(result, UserContext)
            assert result.learning_preferences is not None
            assert result.learning_preferences.learning_style == LearningStyleEnum.VISUAL
            assert result.learning_preferences.budget_preference == "free"
    
    @pytest.mark.asyncio
    async def test_get_user_context_success(self, user_context_manager, sample_db_user):
        """Test successful user context retrieval"""
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.get_user_by_id = AsyncMock(return_value=sample_db_user)
            
            result = await user_context_manager.get_user_context("test-user-123")
            
            assert isinstance(result, UserContext)
            assert result.user_id == "test-user-123"
            assert len(result.current_skills) == 2
            assert "python" in result.current_skills
            assert "javascript" in result.current_skills
            assert result.current_skills["python"].level == SkillLevelEnum.BEGINNER
            assert result.current_skills["javascript"].level == SkillLevelEnum.INTERMEDIATE
    
    @pytest.mark.asyncio
    async def test_get_user_context_not_found(self, user_context_manager):
        """Test user context retrieval when user not found"""
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.get_user_by_id = AsyncMock(return_value=None)
            
            result = await user_context_manager.get_user_context("nonexistent-user")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_skills_success(self, user_context_manager):
        """Test successful skill updates"""
        skills = {
            "python": SkillLevel(
                skill_name="python",
                level=SkillLevelEnum.INTERMEDIATE,
                confidence_score=0.8,
                last_updated=datetime.now()
            ),
            "react": SkillLevel(
                skill_name="react",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=0.5,
                last_updated=datetime.now()
            )
        }
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.upsert_user_skill = AsyncMock()
            user_context_manager.db_utils.update_user_preferences = AsyncMock(return_value=True)
            
            await user_context_manager.update_skills("test-user-123", skills)
            
            # Verify skill updates
            assert user_context_manager.db_utils.upsert_user_skill.call_count == 2
            
            # Check first skill call
            first_call = user_context_manager.db_utils.upsert_user_skill.call_args_list[0]
            assert first_call.kwargs["skill_name"] == "python"
            assert first_call.kwargs["level"] == "intermediate"
            assert first_call.kwargs["confidence_score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_save_preferences_success(self, user_context_manager):
        """Test successful preference saving"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.KINESTHETIC,
            time_commitment="5-10 hours/week",
            budget_preference="low_cost",
            preferred_platforms=["udemy", "pluralsight"],
            content_types=["video", "course"],
            difficulty_preference="challenging"
        )
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.update_user_preferences = AsyncMock(return_value=True)
            
            await user_context_manager.save_preferences("test-user-123", preferences)
            
            # Verify preferences were saved
            user_context_manager.db_utils.update_user_preferences.assert_called_once()
            call_args = user_context_manager.db_utils.update_user_preferences.call_args
            assert call_args[0][1] == "test-user-123"  # user_id
            
            prefs_dict = call_args[0][2]  # preferences dict
            assert prefs_dict["learning_style"] == "kinesthetic"
            assert prefs_dict["budget_preference"] == "low_cost"
    
    @pytest.mark.asyncio
    async def test_save_preferences_user_not_found(self, user_context_manager):
        """Test preference saving when user not found"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week"
        )
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.update_user_preferences = AsyncMock(return_value=False)
            
            with pytest.raises(ValueError, match="User .* not found"):
                await user_context_manager.save_preferences("nonexistent-user", preferences)
    
    @pytest.mark.asyncio
    async def test_track_progress_success(self, user_context_manager):
        """Test successful progress tracking"""
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.complete_milestone = AsyncMock(return_value=True)
            user_context_manager.db_utils.update_user_preferences = AsyncMock(return_value=True)
            
            await user_context_manager.track_progress("test-user-123", "milestone-456")
            
            # Verify milestone completion
            user_context_manager.db_utils.complete_milestone.assert_called_once_with(
                mock_session, "milestone-456"
            )
            
            # Verify user timestamp update
            user_context_manager.db_utils.update_user_preferences.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, user_context_manager):
        """Test successful conversation history retrieval"""
        mock_conversations = [
            DBConversation(
                id="conv-1",
                user_id="test-user-123",
                message="Hello",
                response="Hi there!",
                timestamp=datetime.now() - timedelta(minutes=5),
                message_type="general",
                context_data={"session": "1"}
            ),
            DBConversation(
                id="conv-2",
                user_id="test-user-123",
                message="I want to learn Python",
                response="Great choice! Let's start with the basics.",
                timestamp=datetime.now() - timedelta(minutes=2),
                message_type="general",
                context_data={}
            )
        ]
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.get_conversation_history = AsyncMock(
                return_value=mock_conversations
            )
            
            result = await user_context_manager.get_conversation_history("test-user-123", limit=10)
            
            assert len(result) == 4  # 2 conversations * 2 messages each
            assert all(isinstance(msg, dict) for msg in result)
            assert all("content" in msg and "message_type" in msg for msg in result)
            
            # Check message types
            message_types = [msg["message_type"] for msg in result]
            assert "user" in message_types
            assert "assistant" in message_types
    
    @pytest.mark.asyncio
    async def test_add_conversation_success(self, user_context_manager):
        """Test successful conversation addition"""
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.add_conversation = AsyncMock()
            
            await user_context_manager.add_conversation(
                user_id="test-user-123",
                user_message="What is Python?",
                assistant_response="Python is a programming language...",
                message_type="general",
                context_data={"topic": "programming"}
            )
            
            # Verify conversation was added
            user_context_manager.db_utils.add_conversation.assert_called_once_with(
                session=mock_session,
                user_id="test-user-123",
                message="What is Python?",
                response="Python is a programming language...",
                message_type="general",
                context_data={"topic": "programming"}
            )
    
    @pytest.mark.asyncio
    async def test_get_user_skills_success(self, user_context_manager):
        """Test successful user skills retrieval"""
        mock_skills = [
            DBUserSkill(
                user_id="test-user-123",
                skill_name="python",
                level="beginner",
                confidence_score=0.6,
                updated_at=datetime.now()
            ),
            DBUserSkill(
                user_id="test-user-123",
                skill_name="sql",
                level="intermediate",
                confidence_score=0.8,
                updated_at=datetime.now()
            )
        ]
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            user_context_manager.db_utils.get_user_skills = AsyncMock(return_value=mock_skills)
            
            result = await user_context_manager.get_user_skills("test-user-123")
            
            assert len(result) == 2
            assert "python" in result
            assert "sql" in result
            assert isinstance(result["python"], SkillLevel)
            assert result["python"].level == SkillLevelEnum.BEGINNER
            assert result["sql"].level == SkillLevelEnum.INTERMEDIATE
    
    @pytest.mark.asyncio
    async def test_create_learning_path_success(self, user_context_manager):
        """Test successful learning path creation"""
        milestones = [
            {
                "title": "Learn Python Basics",
                "description": "Variables, data types, control structures",
                "estimated_hours": 20,
                "prerequisites": []
            },
            {
                "title": "Build First Project",
                "description": "Create a simple calculator",
                "estimated_hours": 10,
                "prerequisites": ["Learn Python Basics"]
            }
        ]
        
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock learning path creation
            mock_learning_path = MagicMock()
            mock_learning_path.id = "lp-123"
            user_context_manager.db_utils.create_learning_path = AsyncMock(return_value=mock_learning_path)
            user_context_manager.db_utils.add_milestone = AsyncMock()
            
            result = await user_context_manager.create_learning_path(
                user_id="test-user-123",
                goal="Learn Python Programming",
                milestones=milestones,
                estimated_duration_days=30,
                difficulty_level="beginner"
            )
            
            assert result == "lp-123"
            
            # Verify learning path creation
            user_context_manager.db_utils.create_learning_path.assert_called_once_with(
                session=mock_session,
                user_id="test-user-123",
                goal="Learn Python Programming",
                estimated_duration_days=30,
                difficulty_level="beginner"
            )
            
            # Verify milestone creation
            assert user_context_manager.db_utils.add_milestone.call_count == 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, user_context_manager):
        """Test error handling in various methods"""
        with patch('edagent.services.user_context_manager.get_database_connection') as mock_db:
            # Simulate database error
            mock_db.side_effect = Exception("Database connection failed")
            
            # Test get_user_context error handling
            result = await user_context_manager.get_user_context("test-user-123")
            assert result is None
            
            # Test get_conversation_history error handling
            result = await user_context_manager.get_conversation_history("test-user-123")
            assert result == []
            
            # Test get_user_skills error handling
            result = await user_context_manager.get_user_skills("test-user-123")
            assert result == {}
    
    def test_db_user_to_context_conversion(self, user_context_manager, sample_db_user):
        """Test conversion from database user to UserContext"""
        # This is a private method, but we can test it directly for thoroughness
        result = asyncio.run(user_context_manager._db_user_to_context(sample_db_user))
        
        assert isinstance(result, UserContext)
        assert result.user_id == "test-user-123"
        assert len(result.current_skills) == 2
        assert "python" in result.current_skills
        assert "javascript" in result.current_skills
        assert result.learning_preferences is not None
        assert result.learning_preferences.learning_style == LearningStyleEnum.VISUAL


if __name__ == "__main__":
    pytest.main([__file__])