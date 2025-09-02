"""
Tests for privacy service functionality
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from edagent.services.privacy_service import PrivacyService
from edagent.models.privacy import (
    DataExportResult, DataDeletionResult, PrivacyAction
)
from edagent.database.models import (
    User, UserSkill, Conversation, LearningPath, Milestone,
    UserSession, APIKey
)


class TestPrivacyService:
    """Test cases for PrivacyService"""
    
    @pytest.fixture
    def privacy_service(self):
        """Create privacy service instance"""
        return PrivacyService()
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_export_user_data_success(self, privacy_service, sample_user_id):
        """Test successful user data export"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            # Mock database session and user data
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user exists
            mock_user = User(
                id=uuid.UUID(sample_user_id),
                created_at=datetime.utcnow(),
                preferences={"theme": "dark"}
            )
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Mock collect_user_data
            expected_data = {
                "user_profile": {"id": sample_user_id, "preferences": {"theme": "dark"}},
                "skills": [],
                "conversations": [],
                "learning_paths": [],
                "sessions": [],
                "api_keys": []
            }
            
            with patch.object(privacy_service, '_collect_user_data', return_value=expected_data):
                with patch.object(privacy_service, '_log_privacy_action'):
                    result = await privacy_service.export_user_data(sample_user_id)
            
            assert result.success is True
            assert result.user_id == sample_user_id
            assert result.export_data == expected_data
            assert result.exported_at is not None
    
    @pytest.mark.asyncio
    async def test_export_user_data_user_not_found(self, privacy_service, sample_user_id):
        """Test data export when user doesn't exist"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user not found
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            result = await privacy_service.export_user_data(sample_user_id)
            
            assert result.success is False
            assert f"User {sample_user_id} not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_delete_user_data_success(self, privacy_service, sample_user_id):
        """Test successful user data deletion"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user exists
            mock_user = User(id=uuid.UUID(sample_user_id))
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Mock deletion methods
            with patch.object(privacy_service, '_delete_data_by_type', return_value=5):
                with patch.object(privacy_service, '_log_privacy_action'):
                    result = await privacy_service.delete_user_data(
                        sample_user_id, 
                        data_types=["conversations"],
                        confirm_deletion=True
                    )
            
            assert result.success is True
            assert result.user_id == sample_user_id
            assert result.deleted_data_types == ["conversations"]
            assert result.deleted_counts == {"conversations": 5}
            assert result.deleted_at is not None
    
    @pytest.mark.asyncio
    async def test_delete_user_data_not_confirmed(self, privacy_service, sample_user_id):
        """Test data deletion without confirmation"""
        result = await privacy_service.delete_user_data(
            sample_user_id, 
            confirm_deletion=False
        )
        
        assert result.success is False
        assert "Deletion must be explicitly confirmed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_delete_user_data_user_not_found(self, privacy_service, sample_user_id):
        """Test data deletion when user doesn't exist"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user not found
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            result = await privacy_service.delete_user_data(
                sample_user_id, 
                confirm_deletion=True
            )
            
            assert result.success is False
            assert f"User {sample_user_id} not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_get_user_data_summary(self, privacy_service, sample_user_id):
        """Test getting user data summary"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user exists first
            mock_user = User(id=uuid.UUID(sample_user_id))
            
            # Create separate mock results for each query
            mock_results = []
            
            # User query result
            user_result = AsyncMock()
            user_result.scalar_one_or_none.return_value = mock_user
            mock_results.append(user_result)
            
            # Skills query result
            skills_result = AsyncMock()
            skills_result.scalars.return_value.all.return_value = [UserSkill()]
            mock_results.append(skills_result)
            
            # Conversations query result
            conv_result = AsyncMock()
            conv_result.scalars.return_value.all.return_value = [Conversation(), Conversation()]
            mock_results.append(conv_result)
            
            # Learning paths query result
            lp_result = AsyncMock()
            lp_result.scalars.return_value.all.return_value = [LearningPath()]
            mock_results.append(lp_result)
            
            # Sessions query result
            session_result = AsyncMock()
            session_result.scalars.return_value.all.return_value = [UserSession()]
            mock_results.append(session_result)
            
            # API keys query result
            api_result = AsyncMock()
            api_result.scalars.return_value.all.return_value = [APIKey()]
            mock_results.append(api_result)
            
            mock_session.execute.side_effect = mock_results
            
            summary = await privacy_service.get_user_data_summary(sample_user_id)
            
            assert summary["user_profile"] == 1
            assert summary["skills"] == 1
            assert summary["conversations"] == 2
            assert summary["learning_paths"] == 1
            assert summary["sessions"] == 1
            assert summary["api_keys"] == 1
    
    @pytest.mark.asyncio
    async def test_collect_user_data_comprehensive(self, privacy_service):
        """Test comprehensive user data collection"""
        user_id = uuid.uuid4()
        mock_session = AsyncMock()
        
        # Mock user data
        mock_user = User(
            id=user_id,
            created_at=datetime.utcnow(),
            preferences={"theme": "dark"}
        )
        
        mock_skill = UserSkill(
            user_id=user_id,
            skill_name="Python",
            level="intermediate",
            confidence_score=0.8,
            updated_at=datetime.utcnow()
        )
        
        mock_conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            message="Hello",
            response="Hi there!",
            timestamp=datetime.utcnow(),
            message_type="general"
        )
        
        mock_learning_path = LearningPath(
            id=uuid.uuid4(),
            user_id=user_id,
            goal="Learn Python",
            created_at=datetime.utcnow(),
            milestones=[]
        )
        
        # Mock database queries
        mock_results = []
        
        # User query result
        user_result = AsyncMock()
        user_result.scalar_one_or_none.return_value = mock_user
        mock_results.append(user_result)
        
        # Skills query result
        skills_result = AsyncMock()
        skills_result.scalars.return_value.all.return_value = [mock_skill]
        mock_results.append(skills_result)
        
        # Conversations query result
        conv_result = AsyncMock()
        conv_result.scalars.return_value.all.return_value = [mock_conversation]
        mock_results.append(conv_result)
        
        # Learning paths query result (with selectinload)
        lp_result = AsyncMock()
        lp_result.scalars.return_value.all.return_value = [mock_learning_path]
        mock_results.append(lp_result)
        
        # Sessions query result
        session_result = AsyncMock()
        session_result.scalars.return_value.all.return_value = []
        mock_results.append(session_result)
        
        # API keys query result
        api_result = AsyncMock()
        api_result.scalars.return_value.all.return_value = []
        mock_results.append(api_result)
        
        mock_session.execute.side_effect = mock_results
        
        result = await privacy_service._collect_user_data(mock_session, user_id)
        
        assert "user_profile" in result
        assert "skills" in result
        assert "conversations" in result
        assert "learning_paths" in result
        assert "sessions" in result
        assert "api_keys" in result
        
        assert len(result["skills"]) == 1
        assert result["skills"][0]["skill_name"] == "Python"
        assert len(result["conversations"]) == 1
        assert result["conversations"][0]["message"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_delete_data_by_type_conversations(self, privacy_service):
        """Test deleting conversations data type"""
        user_id = uuid.uuid4()
        mock_session = AsyncMock()
        
        # Mock delete result
        mock_session.execute.return_value.rowcount = 3
        
        count = await privacy_service._delete_data_by_type(
            mock_session, user_id, "conversations"
        )
        
        assert count == 3
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_data_by_type_skills(self, privacy_service):
        """Test deleting skills data type"""
        user_id = uuid.uuid4()
        mock_session = AsyncMock()
        
        # Mock delete result
        mock_session.execute.return_value.rowcount = 5
        
        count = await privacy_service._delete_data_by_type(
            mock_session, user_id, "skills"
        )
        
        assert count == 5
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_data_by_type_learning_paths(self, privacy_service):
        """Test deleting learning paths data type"""
        user_id = uuid.uuid4()
        mock_session = AsyncMock()
        
        # Mock delete results (milestones first, then learning paths)
        mock_session.execute.return_value.rowcount = 2
        
        count = await privacy_service._delete_data_by_type(
            mock_session, user_id, "learning_paths"
        )
        
        assert count == 2
        # Should be called twice (milestones, then learning paths)
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_log_privacy_action(self, privacy_service):
        """Test privacy action logging"""
        mock_session = AsyncMock()
        user_id = str(uuid.uuid4())
        action = PrivacyAction.DATA_EXPORT
        metadata = {"test": "data"}
        
        with patch('edagent.services.privacy_service.logger') as mock_logger:
            await privacy_service._log_privacy_action(
                mock_session, user_id, action, metadata
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert action.value in call_args[0][0]
            assert user_id in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_export_data_exception_handling(self, privacy_service, sample_user_id):
        """Test exception handling in data export"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            mock_db.get_session.side_effect = Exception("Database error")
            
            result = await privacy_service.export_user_data(sample_user_id)
            
            assert result.success is False
            assert "Data export failed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_delete_data_exception_handling(self, privacy_service, sample_user_id):
        """Test exception handling in data deletion"""
        with patch('edagent.services.privacy_service.db_manager') as mock_db:
            mock_db.get_session.side_effect = Exception("Database error")
            
            result = await privacy_service.delete_user_data(
                sample_user_id, confirm_deletion=True
            )
            
            assert result.success is False
            assert "Data deletion failed" in result.error_message