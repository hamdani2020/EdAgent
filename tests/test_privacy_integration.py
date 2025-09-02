"""
Integration tests for privacy functionality
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from edagent.database.connection import db_manager
from edagent.database.models import (
    User, UserSkill, Conversation, LearningPath, Milestone,
    UserSession, APIKey
)
from edagent.services.privacy_service import PrivacyService
from edagent.models.privacy import PrivacyAction


class TestPrivacyIntegration:
    """Integration tests for privacy functionality"""
    
    @pytest.fixture
    async def db_session(self):
        """Create database session for testing"""
        await db_manager.initialize()
        async with db_manager.get_session() as session:
            yield session
        await db_manager.close()
    
    @pytest.fixture
    async def sample_user_data(self, db_session: AsyncSession):
        """Create sample user data for testing"""
        user_id = uuid.uuid4()
        
        # Create user
        user = User(
            id=user_id,
            created_at=datetime.utcnow(),
            preferences={"theme": "dark", "language": "en"}
        )
        db_session.add(user)
        
        # Create skills
        skills = [
            UserSkill(
                user_id=user_id,
                skill_name="Python",
                level="intermediate",
                confidence_score=0.8
            ),
            UserSkill(
                user_id=user_id,
                skill_name="JavaScript",
                level="beginner",
                confidence_score=0.4
            )
        ]
        for skill in skills:
            db_session.add(skill)
        
        # Create conversations
        conversations = [
            Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                message="Hello, I want to learn Python",
                response="Great! I can help you with that.",
                message_type="general"
            ),
            Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                message="What should I learn first?",
                response="Let's start with basic syntax and data types.",
                message_type="learning_path"
            )
        ]
        for conv in conversations:
            db_session.add(conv)
        
        # Create learning path with milestones
        learning_path = LearningPath(
            id=uuid.uuid4(),
            user_id=user_id,
            goal="Learn Python Programming",
            estimated_duration_days=90,
            difficulty_level="beginner"
        )
        db_session.add(learning_path)
        
        milestone = Milestone(
            id=uuid.uuid4(),
            learning_path_id=learning_path.id,
            title="Learn Python Basics",
            description="Variables, data types, control structures",
            order_index=1,
            estimated_hours=20
        )
        db_session.add(milestone)
        
        # Create session
        user_session = UserSession(
            session_id="test_session_123",
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            status="active"
        )
        db_session.add(user_session)
        
        # Create API key
        api_key = APIKey(
            key_id="test_key_123",
            user_id=user_id,
            key_hash="hashed_key_value",
            name="Test API Key",
            permissions=["read", "write"]
        )
        db_session.add(api_key)
        
        await db_session.commit()
        
        return {
            "user_id": str(user_id),
            "user": user,
            "skills": skills,
            "conversations": conversations,
            "learning_path": learning_path,
            "milestone": milestone,
            "session": user_session,
            "api_key": api_key
        }
    
    @pytest.mark.asyncio
    async def test_full_data_export_integration(self, sample_user_data):
        """Test complete data export integration"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        result = await privacy_service.export_user_data(user_id)
        
        assert result.success is True
        assert result.user_id == user_id
        assert result.export_data is not None
        assert result.exported_at is not None
        
        # Verify all data types are included
        export_data = result.export_data
        assert "user_profile" in export_data
        assert "skills" in export_data
        assert "conversations" in export_data
        assert "learning_paths" in export_data
        assert "sessions" in export_data
        assert "api_keys" in export_data
        
        # Verify data content
        assert export_data["user_profile"]["preferences"]["theme"] == "dark"
        assert len(export_data["skills"]) == 2
        assert len(export_data["conversations"]) == 2
        assert len(export_data["learning_paths"]) == 1
        assert len(export_data["learning_paths"][0]["milestones"]) == 1
        assert len(export_data["sessions"]) == 1
        assert len(export_data["api_keys"]) == 1
        
        # Verify sensitive data is excluded from API keys
        assert "key_hash" not in export_data["api_keys"][0]
        assert export_data["api_keys"][0]["name"] == "Test API Key"
    
    @pytest.mark.asyncio
    async def test_selective_data_deletion_integration(self, sample_user_data):
        """Test selective data deletion integration"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        # Delete only conversations
        result = await privacy_service.delete_user_data(
            user_id=user_id,
            data_types=["conversations"],
            confirm_deletion=True
        )
        
        assert result.success is True
        assert result.user_id == user_id
        assert result.deleted_data_types == ["conversations"]
        assert result.deleted_counts["conversations"] == 2
        
        # Verify conversations are deleted but other data remains
        summary = await privacy_service.get_user_data_summary(user_id)
        assert summary["conversations"] == 0
        assert summary["skills"] == 2
        assert summary["learning_paths"] == 1
        assert summary["user_profile"] == 1
    
    @pytest.mark.asyncio
    async def test_complete_data_deletion_integration(self, sample_user_data):
        """Test complete data deletion integration"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        # Delete all user data
        result = await privacy_service.delete_user_data(
            user_id=user_id,
            confirm_deletion=True
        )
        
        assert result.success is True
        assert result.user_id == user_id
        assert result.total_deleted_items > 0
        
        # Verify all data is deleted
        summary = await privacy_service.get_user_data_summary(user_id)
        assert summary["conversations"] == 0
        assert summary["skills"] == 0
        assert summary["learning_paths"] == 0
        assert summary["sessions"] == 0
        assert summary["api_keys"] == 0
        assert summary["user_profile"] == 0
    
    @pytest.mark.asyncio
    async def test_data_summary_accuracy(self, sample_user_data):
        """Test data summary accuracy"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        summary = await privacy_service.get_user_data_summary(user_id)
        
        assert summary["user_profile"] == 1
        assert summary["skills"] == 2
        assert summary["conversations"] == 2
        assert summary["learning_paths"] == 1
        assert summary["sessions"] == 1
        assert summary["api_keys"] == 1
    
    @pytest.mark.asyncio
    async def test_export_data_json_serialization(self, sample_user_data):
        """Test that exported data can be properly serialized to JSON"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        result = await privacy_service.export_user_data(user_id)
        
        assert result.success is True
        
        # Test JSON serialization
        json_string = result.to_json_string()
        assert json_string != "{}"
        
        # Verify it can be parsed back
        parsed_data = json.loads(json_string)
        assert "user_profile" in parsed_data
        assert "skills" in parsed_data
        assert "conversations" in parsed_data
    
    @pytest.mark.asyncio
    async def test_privacy_action_logging(self, sample_user_data):
        """Test that privacy actions are properly logged"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        # Mock the logging to capture log calls
        with pytest.MonkeyPatch().context() as m:
            log_calls = []
            
            def mock_log_info(message, **kwargs):
                log_calls.append((message, kwargs))
            
            m.setattr("edagent.services.privacy_service.logger.info", mock_log_info)
            
            # Perform export
            await privacy_service.export_user_data(user_id)
            
            # Verify logging occurred
            assert len(log_calls) > 0
            export_log = next((call for call in log_calls if "Privacy action" in call[0]), None)
            assert export_log is not None
            assert PrivacyAction.DATA_EXPORT.value in export_log[0]
    
    @pytest.mark.asyncio
    async def test_cascade_deletion_learning_paths(self, sample_user_data):
        """Test that learning path deletion properly cascades to milestones"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        # Delete learning paths
        result = await privacy_service.delete_user_data(
            user_id=user_id,
            data_types=["learning_paths"],
            confirm_deletion=True
        )
        
        assert result.success is True
        assert result.deleted_counts["learning_paths"] == 1
        
        # Verify both learning path and milestone are gone
        summary = await privacy_service.get_user_data_summary(user_id)
        assert summary["learning_paths"] == 0
    
    @pytest.mark.asyncio
    async def test_nonexistent_user_handling(self):
        """Test handling of operations on nonexistent users"""
        privacy_service = PrivacyService()
        fake_user_id = str(uuid.uuid4())
        
        # Test export
        export_result = await privacy_service.export_user_data(fake_user_id)
        assert export_result.success is False
        assert "not found" in export_result.error_message
        
        # Test deletion
        delete_result = await privacy_service.delete_user_data(
            fake_user_id, confirm_deletion=True
        )
        assert delete_result.success is False
        assert "not found" in delete_result.error_message
        
        # Test summary
        summary = await privacy_service.get_user_data_summary(fake_user_id)
        assert all(count == 0 for count in summary.values())
    
    @pytest.mark.asyncio
    async def test_partial_deletion_error_handling(self, sample_user_data):
        """Test error handling during partial data deletion"""
        privacy_service = PrivacyService()
        user_id = sample_user_data["user_id"]
        
        # Test deletion with invalid data type
        result = await privacy_service.delete_user_data(
            user_id=user_id,
            data_types=["invalid_data_type"],
            confirm_deletion=True
        )
        
        # Should still succeed but with 0 deletions for invalid type
        assert result.success is True
        assert result.deleted_counts.get("invalid_data_type", 0) == 0