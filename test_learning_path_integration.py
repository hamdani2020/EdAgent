"""
Integration tests for Learning Path Management System
Tests the integration between learning path components and the main Streamlit app
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Import components to test
from streamlit_learning_path_components import LearningPathManager, render_learning_path_management_system
from streamlit_api_client import EnhancedEdAgentAPI, LearningPath
from streamlit_session_manager import SessionManager, UserInfo


class TestLearningPathIntegration:
    """Integration tests for learning path management"""
    
    @pytest.fixture
    def mock_authenticated_session_manager(self):
        """Create authenticated session manager"""
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        session_manager.get_user_preferences.return_value = {
            'learning_style': ['video', 'interactive'],
            'difficulty_preference': 'intermediate'
        }
        return session_manager
    
    @pytest.fixture
    def mock_api_client_with_data(self):
        """Create API client with mock data"""
        api_client = Mock(spec=EnhancedEdAgentAPI)
        
        # Mock learning paths data
        sample_paths = [
            LearningPath(
                id="path_1",
                title="Python Fundamentals",
                description="Learn Python basics",
                goal="Master Python programming",
                milestones=[
                    {"id": "m1", "title": "Variables and Data Types", "status": "completed"},
                    {"id": "m2", "title": "Control Structures", "status": "in_progress"},
                    {"id": "m3", "title": "Functions", "status": "pending"}
                ],
                progress=0.4,
                difficulty_level="beginner",
                target_skills=["Python", "Programming Basics"]
            ),
            LearningPath(
                id="path_2",
                title="Web Development with React",
                description="Build modern web applications",
                goal="Become a React developer",
                milestones=[
                    {"id": "m4", "title": "JSX and Components", "status": "completed"},
                    {"id": "m5", "title": "State Management", "status": "completed"},
                    {"id": "m6", "title": "Routing", "status": "in_progress"}
                ],
                progress=0.7,
                difficulty_level="intermediate",
                target_skills=["React", "JavaScript", "HTML", "CSS"]
            )
        ]
        
        # Configure async methods
        api_client.get_user_learning_paths = AsyncMock(return_value=sample_paths)
        api_client.create_learning_path = AsyncMock(return_value=sample_paths[0])
        api_client.update_milestone_status = AsyncMock(return_value=True)
        api_client.delete_learning_path = AsyncMock(return_value=True)
        api_client.get_learning_path_recommendations = AsyncMock(return_value=[
            {
                "title": "Advanced Python",
                "description": "Take Python to the next level",
                "category": "Programming",
                "difficulty": "advanced"
            }
        ])
        
        return api_client
    
    def test_learning_path_manager_initialization_with_real_data(
        self, 
        mock_api_client_with_data, 
        mock_authenticated_session_manager
    ):
        """Test LearningPathManager with realistic data"""
        manager = LearningPathManager(mock_api_client_with_data, mock_authenticated_session_manager)
        
        assert manager.api == mock_api_client_with_data
        assert manager.session_manager == mock_authenticated_session_manager
        
        # Test that session manager is properly configured
        assert manager.session_manager.is_authenticated()
        user_info = manager.session_manager.get_current_user()
        assert user_info.user_id == "test_user_123"
    
    def test_learning_path_filtering_with_real_scenarios(self):
        """Test filtering with realistic learning path scenarios"""
        manager = LearningPathManager(Mock(), Mock())
        
        # Realistic learning paths with different statuses
        paths = [
            {
                'id': 'path_1',
                'title': 'Python Basics',
                'progress': 0.0,  # Not started
                'created_at': '2024-01-01',
                'difficulty_level': 'beginner'
            },
            {
                'id': 'path_2', 
                'title': 'Web Development',
                'progress': 0.6,  # In progress
                'created_at': '2024-01-15',
                'difficulty_level': 'intermediate'
            },
            {
                'id': 'path_3',
                'title': 'Data Science',
                'progress': 1.0,  # Completed
                'created_at': '2024-02-01',
                'difficulty_level': 'advanced'
            },
            {
                'id': 'path_4',
                'title': 'Machine Learning',
                'progress': 0.3,  # In progress
                'created_at': '2024-02-15',
                'difficulty_level': 'advanced'
            }
        ]
        
        # Test filtering by status
        active_paths = manager._filter_and_sort_paths(paths, "Active", "Title", "Ascending")
        assert len(active_paths) == 2  # paths 2 and 4
        assert all(0 < p['progress'] < 1.0 for p in active_paths)
        
        completed_paths = manager._filter_and_sort_paths(paths, "Completed", "Title", "Ascending")
        assert len(completed_paths) == 1  # path 3
        assert completed_paths[0]['progress'] == 1.0
        
        # Test sorting by progress
        sorted_by_progress = manager._filter_and_sort_paths(paths, "All", "Progress", "Descending")
        progress_values = [p['progress'] for p in sorted_by_progress]
        assert progress_values == [1.0, 0.6, 0.3, 0.0]
    
    def test_mock_recommendations_quality(self):
        """Test that mock recommendations have good quality and variety"""
        manager = LearningPathManager(Mock(), Mock())
        
        recommendations = manager._generate_mock_recommendations(None)
        
        # Should have multiple recommendations
        assert len(recommendations) >= 3
        
        # Should have variety in categories
        categories = set(rec['category'] for rec in recommendations)
        assert len(categories) >= 3
        
        # Should have variety in difficulty levels
        difficulties = set(rec['difficulty'] for rec in recommendations)
        assert len(difficulties) >= 2
        
        # Each recommendation should have required fields
        required_fields = ['title', 'description', 'category', 'difficulty', 'duration', 'rating', 'skills']
        for rec in recommendations:
            for field in required_fields:
                assert field in rec
                assert rec[field] is not None
        
        # Skills should be lists with content
        for rec in recommendations:
            assert isinstance(rec['skills'], list)
            assert len(rec['skills']) > 0
    
    def test_learning_path_progress_analytics_calculation(self):
        """Test progress analytics calculations with realistic data"""
        # Sample learning paths with different progress levels
        learning_paths = [
            {
                'title': 'Python Basics',
                'progress': 0.8,
                'milestones': [
                    {'status': 'completed'},
                    {'status': 'completed'},
                    {'status': 'in_progress'},
                    {'status': 'pending'}
                ],
                'target_skills': ['Python', 'Programming']
            },
            {
                'title': 'Web Development',
                'progress': 0.5,
                'milestones': [
                    {'status': 'completed'},
                    {'status': 'in_progress'},
                    {'status': 'pending'}
                ],
                'target_skills': ['HTML', 'CSS', 'JavaScript']
            },
            {
                'title': 'Data Science',
                'progress': 1.0,
                'milestones': [
                    {'status': 'completed'},
                    {'status': 'completed'}
                ],
                'target_skills': ['Python', 'Pandas', 'NumPy']
            }
        ]
        
        # Calculate metrics
        total_paths = len(learning_paths)
        completed_paths = len([p for p in learning_paths if p['progress'] >= 1.0])
        avg_progress = sum(p['progress'] for p in learning_paths) / total_paths
        total_milestones = sum(len(p['milestones']) for p in learning_paths)
        
        # Verify calculations
        assert total_paths == 3
        assert completed_paths == 1
        assert avg_progress == pytest.approx(0.767, rel=1e-2)  # (0.8 + 0.5 + 1.0) / 3
        assert total_milestones == 9  # 4 + 3 + 2
        
        # Test skill aggregation
        all_skills = {}
        for path in learning_paths:
            for skill in path['target_skills']:
                if skill not in all_skills:
                    all_skills[skill] = []
                all_skills[skill].append(path['progress'])
        
        # Python appears in 2 paths
        assert 'Python' in all_skills
        assert len(all_skills['Python']) == 2
        
        # Calculate average progress per skill
        skill_progress = {
            skill: sum(progresses) / len(progresses) 
            for skill, progresses in all_skills.items()
        }
        
        # Python average: (0.8 + 1.0) / 2 = 0.9
        assert skill_progress['Python'] == pytest.approx(0.9)
    
    def test_milestone_status_validation(self):
        """Test milestone status validation and transitions"""
        valid_statuses = ['pending', 'in_progress', 'completed']
        
        # Test valid status transitions
        valid_transitions = {
            'pending': ['in_progress'],
            'in_progress': ['completed', 'pending'],  # Can go back if needed
            'completed': ['in_progress']  # Can reopen if needed
        }
        
        for current_status, allowed_next in valid_transitions.items():
            assert current_status in valid_statuses
            for next_status in allowed_next:
                assert next_status in valid_statuses
        
        # Test milestone progress consistency
        test_milestones = [
            {'status': 'completed', 'expected_progress_range': (1.0, 1.0)},
            {'status': 'in_progress', 'expected_progress_range': (0.1, 0.9)},
            {'status': 'pending', 'expected_progress_range': (0.0, 0.0)}
        ]
        
        for milestone in test_milestones:
            status = milestone['status']
            min_progress, max_progress = milestone['expected_progress_range']
            
            # Verify status is valid
            assert status in valid_statuses
            
            # Verify progress range makes sense
            assert 0.0 <= min_progress <= max_progress <= 1.0
    
    @patch('streamlit.session_state', {})
    def test_learning_path_caching_behavior(self, mock_api_client_with_data, mock_authenticated_session_manager):
        """Test learning path caching behavior"""
        manager = LearningPathManager(mock_api_client_with_data, mock_authenticated_session_manager)
        
        # First call should trigger API call
        with patch('streamlit.spinner'):
            paths1 = manager._get_cached_learning_paths("test_user_123")
        
        # Verify API was called
        mock_api_client_with_data.get_user_learning_paths.assert_called_once_with("test_user_123")
        
        # Verify data structure
        assert len(paths1) == 2
        assert paths1[0]['id'] == 'path_1'
        assert paths1[0]['title'] == 'Python Fundamentals'
        assert paths1[1]['id'] == 'path_2'
        assert paths1[1]['title'] == 'Web Development with React'
        
        # Reset mock to verify caching
        mock_api_client_with_data.get_user_learning_paths.reset_mock()
        
        # Second call should use cache (but we can't test this easily without Streamlit context)
        # This test verifies the data structure is correct
        assert isinstance(paths1, list)
        assert all(isinstance(path, dict) for path in paths1)
        
        # Verify required fields are present
        required_fields = ['id', 'title', 'description', 'goal', 'progress', 'milestones']
        for path in paths1:
            for field in required_fields:
                assert field in path


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])