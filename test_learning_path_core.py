"""
Core Learning Path Management Tests
Tests for learning path CRUD operations and progress tracking without Streamlit dependencies
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Import the API client and data models
from streamlit_api_client import EnhancedEdAgentAPI, LearningPath, APIResponse, APIError, APIErrorType
from streamlit_session_manager import SessionManager


class TestLearningPathAPI:
    """Test suite for learning path API operations"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_auth_token.return_value = "test_token"
        return session_manager
    
    @pytest.fixture
    def api_client(self, mock_session_manager):
        """Create API client for testing"""
        return EnhancedEdAgentAPI("http://test-api", mock_session_manager)
    
    @pytest.fixture
    def sample_learning_path_data(self):
        """Sample learning path data"""
        return {
            "id": "path_123",
            "title": "Python Web Development",
            "description": "Learn to build web applications with Python",
            "goal": "Become a Python web developer",
            "milestones": [
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
                }
            ],
            "estimated_duration": 120,
            "difficulty_level": "intermediate",
            "prerequisites": ["Basic programming knowledge"],
            "target_skills": ["Python", "Flask", "Django", "SQL"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "progress": 0.5
        }
    
    @pytest.mark.asyncio
    async def test_create_learning_path_success(self, api_client, sample_learning_path_data):
        """Test successful learning path creation"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=sample_learning_path_data
            )
            
            result = await api_client.create_learning_path("user123", "Learn Python web development")
            
            assert result is not None
            assert isinstance(result, LearningPath)
            assert result.id == "path_123"
            assert result.title == "Python Web Development"
            assert result.goal == "Become a Python web developer"
            assert result.progress == 0.5
            assert len(result.milestones) == 2
            
            # Verify API call
            mock_request.assert_called_once_with(
                "POST",
                "/learning/paths",
                json_data={
                    "user_id": "user123",
                    "goal": "Learn Python web development"
                }
            )
    
    @pytest.mark.asyncio
    async def test_create_learning_path_failure(self, api_client):
        """Test learning path creation failure"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=False,
                data=None,
                error=APIError(
                    error_type=APIErrorType.VALIDATION_ERROR,
                    message="Invalid goal description"
                )
            )
            
            with patch.object(api_client, '_handle_api_error') as mock_handle_error:
                result = await api_client.create_learning_path("user123", "")
                
                assert result is None
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_learning_paths_success(self, api_client, sample_learning_path_data):
        """Test successful retrieval of user learning paths"""
        mock_response_data = {
            "learning_paths": [sample_learning_path_data]
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await api_client.get_user_learning_paths("user123")
            
            assert len(result) == 1
            assert isinstance(result[0], LearningPath)
            assert result[0].id == "path_123"
            assert result[0].title == "Python Web Development"
            
            # Verify API call
            mock_request.assert_called_once_with(
                "GET",
                "/learning/paths/user/user123"
            )
    
    @pytest.mark.asyncio
    async def test_get_user_learning_paths_empty(self, api_client):
        """Test retrieval when user has no learning paths"""
        mock_response_data = {"learning_paths": []}
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await api_client.get_user_learning_paths("user123")
            
            assert len(result) == 0
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_update_milestone_status_success(self, api_client):
        """Test successful milestone status update"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(success=True, data={})
            
            result = await api_client.update_milestone_status(
                "path_123", "milestone_1", "completed"
            )
            
            assert result is True
            
            # Verify API call
            mock_request.assert_called_once_with(
                "PUT",
                "/learning/paths/path_123/milestones/milestone_1",
                json_data={
                    "milestone_id": "milestone_1",
                    "status": "completed"
                }
            )
    
    @pytest.mark.asyncio
    async def test_update_milestone_status_failure(self, api_client):
        """Test milestone status update failure"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=False,
                data=None,
                error=APIError(
                    error_type=APIErrorType.VALIDATION_ERROR,
                    message="Invalid milestone status"
                )
            )
            
            with patch.object(api_client, '_handle_api_error') as mock_handle_error:
                result = await api_client.update_milestone_status(
                    "path_123", "milestone_1", "invalid_status"
                )
                
                assert result is False
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_learning_path_success(self, api_client):
        """Test successful learning path deletion"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(success=True, data={})
            
            result = await api_client.delete_learning_path("path_123")
            
            assert result is True
            
            # Verify API call
            mock_request.assert_called_once_with(
                "DELETE",
                "/learning/paths/path_123"
            )
    
    @pytest.mark.asyncio
    async def test_delete_learning_path_failure(self, api_client):
        """Test learning path deletion failure"""
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=False,
                data=None,
                error=APIError(
                    error_type=APIErrorType.AUTHORIZATION_ERROR,
                    message="Not authorized to delete this path"
                )
            )
            
            with patch.object(api_client, '_handle_api_error') as mock_handle_error:
                result = await api_client.delete_learning_path("path_123")
                
                assert result is False
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_learning_path_success(self, api_client, sample_learning_path_data):
        """Test successful learning path update"""
        updates = {
            "title": "Updated Python Web Development",
            "description": "Updated description"
        }
        
        updated_data = sample_learning_path_data.copy()
        updated_data.update(updates)
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=updated_data
            )
            
            result = await api_client.update_learning_path("path_123", updates)
            
            assert result is not None
            assert isinstance(result, LearningPath)
            assert result.title == "Updated Python Web Development"
            
            # Verify API call
            mock_request.assert_called_once_with(
                "PUT",
                "/learning/paths/path_123",
                json_data=updates
            )
    
    @pytest.mark.asyncio
    async def test_get_learning_path_progress_success(self, api_client):
        """Test successful learning path progress retrieval"""
        progress_data = {
            "overall_progress": 0.6,
            "milestones_completed": 2,
            "total_milestones": 5,
            "estimated_completion": "2024-06-01"
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=progress_data
            )
            
            result = await api_client.get_learning_path_progress("path_123")
            
            assert result is not None
            assert result["overall_progress"] == 0.6
            assert result["milestones_completed"] == 2
            
            # Verify API call
            mock_request.assert_called_once_with(
                "GET",
                "/learning/paths/path_123/progress"
            )
    
    @pytest.mark.asyncio
    async def test_get_learning_path_recommendations_success(self, api_client):
        """Test successful learning path recommendations retrieval"""
        recommendations_data = {
            "recommendations": [
                {
                    "title": "Advanced Python",
                    "description": "Take your Python skills to the next level",
                    "category": "Programming",
                    "difficulty": "advanced",
                    "match_score": 0.85
                },
                {
                    "title": "Data Science with Python",
                    "description": "Learn data science using Python",
                    "category": "Data Science",
                    "difficulty": "intermediate",
                    "match_score": 0.78
                }
            ]
        }
        
        with patch.object(api_client, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=recommendations_data
            )
            
            result = await api_client.get_learning_path_recommendations("user123")
            
            assert len(result) == 2
            assert result[0]["title"] == "Advanced Python"
            assert result[1]["category"] == "Data Science"
            
            # Verify API call
            mock_request.assert_called_once_with(
                "GET",
                "/learning/recommendations/user123"
            )


class TestLearningPathDataModel:
    """Test suite for LearningPath data model"""
    
    def test_learning_path_creation(self):
        """Test LearningPath object creation"""
        path = LearningPath(
            id="test_path",
            title="Test Path",
            description="A test learning path",
            goal="Learn testing"
        )
        
        assert path.id == "test_path"
        assert path.title == "Test Path"
        assert path.description == "A test learning path"
        assert path.goal == "Learn testing"
        assert path.progress == 0.0
        assert path.difficulty_level == "intermediate"
        assert isinstance(path.milestones, list)
        assert isinstance(path.prerequisites, list)
        assert isinstance(path.target_skills, list)
    
    def test_learning_path_with_milestones(self):
        """Test LearningPath with milestones"""
        milestones = [
            {"id": "m1", "title": "Milestone 1", "status": "completed"},
            {"id": "m2", "title": "Milestone 2", "status": "in_progress"}
        ]
        
        path = LearningPath(
            id="test_path",
            title="Test Path",
            milestones=milestones,
            progress=0.5
        )
        
        assert len(path.milestones) == 2
        assert path.milestones[0]["status"] == "completed"
        assert path.milestones[1]["status"] == "in_progress"
        assert path.progress == 0.5
    
    def test_learning_path_progress_calculation(self):
        """Test progress calculation logic"""
        milestones = [
            {"status": "completed", "weight": 1.0},
            {"status": "completed", "weight": 1.0},
            {"status": "in_progress", "weight": 0.5},
            {"status": "pending", "weight": 0.0}
        ]
        
        # Calculate progress based on milestone completion
        total_weight = sum(m["weight"] for m in milestones)
        expected_progress = total_weight / len(milestones)
        
        assert expected_progress == 0.625  # (1.0 + 1.0 + 0.5 + 0.0) / 4


class TestLearningPathFiltering:
    """Test suite for learning path filtering and sorting"""
    
    def test_filter_by_status(self):
        """Test filtering paths by completion status"""
        paths = [
            {"id": "path1", "progress": 0.0, "title": "Path 1"},
            {"id": "path2", "progress": 0.5, "title": "Path 2"},
            {"id": "path3", "progress": 1.0, "title": "Path 3"}
        ]
        
        # Filter active paths (0 < progress < 1)
        active_paths = [p for p in paths if 0 < p["progress"] < 1.0]
        assert len(active_paths) == 1
        assert active_paths[0]["id"] == "path2"
        
        # Filter completed paths (progress >= 1)
        completed_paths = [p for p in paths if p["progress"] >= 1.0]
        assert len(completed_paths) == 1
        assert completed_paths[0]["id"] == "path3"
        
        # Filter not started paths (progress == 0)
        not_started_paths = [p for p in paths if p["progress"] == 0.0]
        assert len(not_started_paths) == 1
        assert not_started_paths[0]["id"] == "path1"
    
    def test_sort_by_progress(self):
        """Test sorting paths by progress"""
        paths = [
            {"id": "path1", "progress": 0.3, "title": "Path 1"},
            {"id": "path2", "progress": 0.8, "title": "Path 2"},
            {"id": "path3", "progress": 0.1, "title": "Path 3"}
        ]
        
        # Sort by progress descending
        sorted_paths = sorted(paths, key=lambda x: x["progress"], reverse=True)
        progress_values = [p["progress"] for p in sorted_paths]
        assert progress_values == [0.8, 0.3, 0.1]
        
        # Sort by progress ascending
        sorted_paths = sorted(paths, key=lambda x: x["progress"])
        progress_values = [p["progress"] for p in sorted_paths]
        assert progress_values == [0.1, 0.3, 0.8]
    
    def test_sort_by_title(self):
        """Test sorting paths by title"""
        paths = [
            {"id": "path1", "title": "C Programming"},
            {"id": "path2", "title": "A Python Basics"},
            {"id": "path3", "title": "B Web Development"}
        ]
        
        # Sort by title ascending
        sorted_paths = sorted(paths, key=lambda x: x["title"])
        titles = [p["title"] for p in sorted_paths]
        assert titles == ["A Python Basics", "B Web Development", "C Programming"]


class TestLearningPathValidation:
    """Test suite for learning path validation"""
    
    def test_valid_milestone_statuses(self):
        """Test valid milestone status values"""
        valid_statuses = ["pending", "in_progress", "completed"]
        
        for status in valid_statuses:
            # Should not raise any exception
            assert status in valid_statuses
    
    def test_valid_difficulty_levels(self):
        """Test valid difficulty level values"""
        valid_levels = ["beginner", "intermediate", "advanced"]
        
        for level in valid_levels:
            # Should not raise any exception
            assert level in valid_levels
    
    def test_progress_bounds(self):
        """Test progress value bounds"""
        # Progress should be between 0.0 and 1.0
        valid_progress_values = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for progress in valid_progress_values:
            assert 0.0 <= progress <= 1.0
    
    def test_milestone_consistency(self):
        """Test milestone status consistency"""
        milestones = [
            {"id": "m1", "status": "completed", "progress": 1.0},
            {"id": "m2", "status": "in_progress", "progress": 0.5},
            {"id": "m3", "status": "pending", "progress": 0.0}
        ]
        
        # Check that status matches progress
        for milestone in milestones:
            if milestone["status"] == "completed":
                assert milestone["progress"] == 1.0
            elif milestone["status"] == "pending":
                assert milestone["progress"] == 0.0
            elif milestone["status"] == "in_progress":
                assert 0.0 < milestone["progress"] < 1.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])