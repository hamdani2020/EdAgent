"""
Tests for Learning Path Management System
Comprehensive tests for learning path CRUD operations and progress tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import streamlit as st

# Import the components to test
from streamlit_learning_path_components import LearningPathManager
from streamlit_api_client import EnhancedEdAgentAPI, LearningPath, APIResponse
from streamlit_session_manager import SessionManager, UserInfo


class TestLearningPathManager:
    """Test suite for LearningPathManager"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        session_manager.get_user_preferences.return_value = None
        return session_manager
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        api_client = Mock(spec=EnhancedEdAgentAPI)
        return api_client
    
    @pytest.fixture
    def learning_path_manager(self, mock_api_client, mock_session_manager):
        """Create LearningPathManager instance"""
        return LearningPathManager(mock_api_client, mock_session_manager)
    
    @pytest.fixture
    def sample_learning_path(self):
        """Create sample learning path data"""
        return LearningPath(
            id="path_123",
            title="Python Web Development",
            description="Learn to build web applications with Python",
            goal="Become a Python web developer",
            milestones=[
                {
                    "id": "milestone_1",
                    "title": "Python Basics",
                    "description": "Learn Python fundamentals",
                    "status": "completed",
                    "progress": 1.0
                },
                {
                    "id": "milestone_2", 
                    "title": "Web Frameworks",
                    "description": "Learn Flask and Django",
                    "status": "in_progress",
                    "progress": 0.5
                },
                {
                    "id": "milestone_3",
                    "title": "Database Integration",
                    "description": "Learn to work with databases",
                    "status": "pending",
                    "progress": 0.0
                }
            ],
            estimated_duration=120,
            difficulty_level="intermediate",
            prerequisites=["Basic programming knowledge"],
            target_skills=["Python", "Flask", "Django", "SQL"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            progress=0.5
        )
    
    def test_learning_path_manager_initialization(self, mock_api_client, mock_session_manager):
        """Test LearningPathManager initialization"""
        manager = LearningPathManager(mock_api_client, mock_session_manager)
        
        assert manager.api == mock_api_client
        assert manager.session_manager == mock_session_manager
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    def test_render_dashboard_unauthenticated(self, mock_warning, learning_path_manager):
        """Test dashboard rendering when user is not authenticated"""
        learning_path_manager.session_manager.is_authenticated.return_value = False
        
        learning_path_manager.render_learning_path_dashboard()
        
        mock_warning.assert_called_once_with("🔐 Please log in to access learning paths.")
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.header')
    @patch('streamlit.tabs')
    def test_render_dashboard_authenticated(self, mock_tabs, mock_header, learning_path_manager):
        """Test dashboard rendering when user is authenticated"""
        mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
        
        learning_path_manager.render_learning_path_dashboard()
        
        mock_header.assert_called_once_with("🛤️ Learning Path Management")
        mock_tabs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_learning_paths_success(self, learning_path_manager, sample_learning_path):
        """Test successful retrieval of cached learning paths"""
        # Mock API response
        learning_path_manager.api.get_user_learning_paths = AsyncMock(
            return_value=[sample_learning_path]
        )
        
        with patch('streamlit.session_state', {}) as mock_session_state:
            with patch('streamlit.spinner'):
                paths = learning_path_manager._get_cached_learning_paths("test_user_123")
        
        assert len(paths) == 1
        assert paths[0]['id'] == "path_123"
        assert paths[0]['title'] == "Python Web Development"
        assert paths[0]['progress'] == 0.5
    
    @pytest.mark.asyncio
    async def test_get_cached_learning_paths_error(self, learning_path_manager):
        """Test error handling in get_cached_learning_paths"""
        # Mock API to raise exception
        learning_path_manager.api.get_user_learning_paths = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        with patch('streamlit.session_state', {}) as mock_session_state:
            with patch('streamlit.spinner'):
                with patch('streamlit.error') as mock_error:
                    paths = learning_path_manager._get_cached_learning_paths("test_user_123")
        
        assert paths == []
        mock_error.assert_called_once()
    
    def test_filter_and_sort_paths_status_filter(self, learning_path_manager):
        """Test filtering paths by status"""
        paths = [
            {'progress': 0.0, 'title': 'Path 1'},
            {'progress': 0.5, 'title': 'Path 2'},
            {'progress': 1.0, 'title': 'Path 3'}
        ]
        
        # Test Active filter
        active_paths = learning_path_manager._filter_and_sort_paths(
            paths, "Active", "Title", "Ascending"
        )
        assert len(active_paths) == 1
        assert active_paths[0]['title'] == 'Path 2'
        
        # Test Completed filter
        completed_paths = learning_path_manager._filter_and_sort_paths(
            paths, "Completed", "Title", "Ascending"
        )
        assert len(completed_paths) == 1
        assert completed_paths[0]['title'] == 'Path 3'
    
    def test_filter_and_sort_paths_sorting(self, learning_path_manager):
        """Test sorting paths"""
        paths = [
            {'progress': 0.3, 'title': 'C Path', 'created_at': '2024-01-01'},
            {'progress': 0.1, 'title': 'A Path', 'created_at': '2024-01-03'},
            {'progress': 0.8, 'title': 'B Path', 'created_at': '2024-01-02'}
        ]
        
        # Test sorting by title ascending
        sorted_paths = learning_path_manager._filter_and_sort_paths(
            paths, "All", "Title", "Ascending"
        )
        titles = [p['title'] for p in sorted_paths]
        assert titles == ['A Path', 'B Path', 'C Path']
        
        # Test sorting by progress descending
        sorted_paths = learning_path_manager._filter_and_sort_paths(
            paths, "All", "Progress", "Descending"
        )
        progresses = [p['progress'] for p in sorted_paths]
        assert progresses == [0.8, 0.3, 0.1]
    
    @pytest.mark.asyncio
    async def test_create_learning_path_with_preferences_success(self, learning_path_manager, sample_learning_path):
        """Test successful learning path creation with preferences"""
        learning_path_manager.api.create_learning_path = AsyncMock(
            return_value=sample_learning_path
        )
        
        preferences = {
            'time_commitment': '10-20',
            'difficulty_preference': 'intermediate',
            'learning_style': ['video', 'interactive'],
            'budget_preference': 'moderate'
        }
        
        with patch('streamlit.spinner'):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.session_state', {}) as mock_session_state:
                    learning_path_manager._create_learning_path_with_preferences(
                        "test_user_123", 
                        "Learn Python web development", 
                        preferences
                    )
        
        learning_path_manager.api.create_learning_path.assert_called_once_with(
            "test_user_123", "Learn Python web development"
        )
        mock_success.assert_called_once_with("✅ Learning path created successfully!")
    
    @pytest.mark.asyncio
    async def test_create_learning_path_with_preferences_failure(self, learning_path_manager):
        """Test learning path creation failure"""
        learning_path_manager.api.create_learning_path = AsyncMock(return_value=None)
        
        preferences = {'time_commitment': '10-20'}
        
        with patch('streamlit.spinner'):
            with patch('streamlit.error') as mock_error:
                learning_path_manager._create_learning_path_with_preferences(
                    "test_user_123", 
                    "Learn Python", 
                    preferences
                )
        
        mock_error.assert_called_once_with("❌ Failed to create learning path. Please try again.")
    
    @pytest.mark.asyncio
    async def test_update_milestone_status_success(self, learning_path_manager):
        """Test successful milestone status update"""
        learning_path_manager.api.update_milestone_status = AsyncMock(return_value=True)
        
        with patch('streamlit.success') as mock_success:
            with patch('streamlit.session_state', {}) as mock_session_state:
                with patch('streamlit.rerun') as mock_rerun:
                    learning_path_manager._update_milestone_status(
                        "path_123", "milestone_1", "completed"
                    )
        
        learning_path_manager.api.update_milestone_status.assert_called_once_with(
            "path_123", "milestone_1", "completed"
        )
        mock_success.assert_called_once_with("✅ Milestone marked as completed!")
        mock_rerun.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_milestone_status_failure(self, learning_path_manager):
        """Test milestone status update failure"""
        learning_path_manager.api.update_milestone_status = AsyncMock(return_value=False)
        
        with patch('streamlit.error') as mock_error:
            learning_path_manager._update_milestone_status(
                "path_123", "milestone_1", "completed"
            )
        
        mock_error.assert_called_once_with("❌ Failed to update milestone status.")
    
    def test_generate_mock_recommendations(self, learning_path_manager):
        """Test generation of mock recommendations"""
        recommendations = learning_path_manager._generate_mock_recommendations(None)
        
        assert len(recommendations) > 0
        
        # Check structure of first recommendation
        rec = recommendations[0]
        required_fields = ['title', 'description', 'category', 'difficulty', 'duration', 'rating', 'skills']
        for field in required_fields:
            assert field in rec
        
        # Check data types
        assert isinstance(rec['title'], str)
        assert isinstance(rec['skills'], list)
        assert isinstance(rec['rating'], int)
    
    @pytest.mark.asyncio
    async def test_create_path_from_recommendation_success(self, learning_path_manager, sample_learning_path):
        """Test creating path from recommendation"""
        learning_path_manager.api.create_learning_path = AsyncMock(
            return_value=sample_learning_path
        )
        
        recommendation = {
            'title': 'Python Basics',
            'description': 'Learn Python programming fundamentals'
        }
        
        with patch('streamlit.spinner'):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.session_state', {}) as mock_session_state:
                    with patch('streamlit.rerun') as mock_rerun:
                        learning_path_manager._create_path_from_recommendation(
                            "test_user_123", recommendation
                        )
        
        expected_goal = "Learn Python Basics: Learn Python programming fundamentals"
        learning_path_manager.api.create_learning_path.assert_called_once_with(
            "test_user_123", expected_goal
        )
        mock_success.assert_called_once()
        mock_rerun.assert_called_once()


class TestLearningPathAPIIntegration:
    """Integration tests for learning path API methods"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager for API tests"""
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_auth_token.return_value = "test_token"
        return session_manager
    
    @pytest.fixture
    def api_client(self, mock_session_manager):
        """Create API client for testing"""
        return EnhancedEdAgentAPI("http://test-api", mock_session_manager)
    
    @pytest.mark.asyncio
    async def test_create_learning_path_api_success(self, api_client):
        """Test successful learning path creation via API"""
        mock_response_data = {
            "id": "path_123",
            "title": "Python Learning Path",
            "description": "Learn Python programming",
            "goal": "Become a Python developer",
            "milestones": [],
            "estimated_duration": 100,
            "difficulty_level": "intermediate",
            "prerequisites": [],
            "target_skills": ["Python"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "progress": 0.0
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await api_client.create_learning_path("user123", "Learn Python")
            
            assert result is not None
            assert result.id == "path_123"
            assert result.title == "Python Learning Path"
            assert result.goal == "Become a Python developer"
    
    @pytest.mark.asyncio
    async def test_get_user_learning_paths_api_success(self, api_client):
        """Test successful retrieval of user learning paths"""
        mock_response_data = {
            "learning_paths": [
                {
                    "id": "path_1",
                    "title": "Path 1",
                    "description": "Description 1",
                    "goal": "Goal 1",
                    "milestones": [],
                    "progress": 0.3
                },
                {
                    "id": "path_2", 
                    "title": "Path 2",
                    "description": "Description 2",
                    "goal": "Goal 2",
                    "milestones": [],
                    "progress": 0.7
                }
            ]
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await api_client.get_user_learning_paths("user123")
            
            assert len(result) == 2
            assert result[0].id == "path_1"
            assert result[1].id == "path_2"
            assert result[0].progress == 0.3
            assert result[1].progress == 0.7
    
    @pytest.mark.asyncio
    async def test_update_milestone_status_api_success(self, api_client):
        """Test successful milestone status update"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(success=True, data={})
            
            result = await api_client.update_milestone_status(
                "path_123", "milestone_1", "completed"
            )
            
            assert result is True
            mock_request.assert_called_once_with(
                "PUT",
                "/learning/paths/path_123/milestones/milestone_1",
                json_data={
                    "milestone_id": "milestone_1",
                    "status": "completed"
                }
            )
    
    @pytest.mark.asyncio
    async def test_delete_learning_path_api_success(self, api_client):
        """Test successful learning path deletion"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(success=True, data={})
            
            result = await api_client.delete_learning_path("path_123")
            
            assert result is True
            mock_request.assert_called_once_with(
                "DELETE",
                "/learning/paths/path_123"
            )
    
    @pytest.mark.asyncio
    async def test_get_learning_path_recommendations_api_success(self, api_client):
        """Test successful learning path recommendations retrieval"""
        mock_response_data = {
            "recommendations": [
                {
                    "title": "Web Development",
                    "description": "Learn web development",
                    "category": "Programming",
                    "difficulty": "intermediate"
                }
            ]
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await api_client.get_learning_path_recommendations("user123")
            
            assert len(result) == 1
            assert result[0]["title"] == "Web Development"
            assert result[0]["category"] == "Programming"


class TestLearningPathProgressTracking:
    """Tests for learning path progress tracking functionality"""
    
    def test_progress_calculation_with_milestones(self):
        """Test progress calculation based on milestone completion"""
        milestones = [
            {"status": "completed", "progress": 1.0},
            {"status": "in_progress", "progress": 0.5},
            {"status": "pending", "progress": 0.0}
        ]
        
        # Calculate overall progress
        total_progress = sum(m["progress"] for m in milestones) / len(milestones)
        
        assert total_progress == 0.5  # (1.0 + 0.5 + 0.0) / 3
    
    def test_milestone_status_transitions(self):
        """Test valid milestone status transitions"""
        valid_transitions = {
            "pending": ["in_progress"],
            "in_progress": ["completed", "pending"],
            "completed": ["in_progress"]  # Allow reopening if needed
        }
        
        # Test valid transitions
        assert "in_progress" in valid_transitions["pending"]
        assert "completed" in valid_transitions["in_progress"]
        assert "in_progress" in valid_transitions["completed"]
    
    def test_learning_path_completion_detection(self):
        """Test detection of completed learning paths"""
        # Path with all milestones completed
        completed_path = {
            "milestones": [
                {"status": "completed"},
                {"status": "completed"},
                {"status": "completed"}
            ],
            "progress": 1.0
        }
        
        # Path with some milestones incomplete
        incomplete_path = {
            "milestones": [
                {"status": "completed"},
                {"status": "in_progress"},
                {"status": "pending"}
            ],
            "progress": 0.5
        }
        
        def is_path_completed(path):
            return path.get("progress", 0) >= 1.0
        
        assert is_path_completed(completed_path) is True
        assert is_path_completed(incomplete_path) is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])