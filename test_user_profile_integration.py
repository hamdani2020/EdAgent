"""
Integration test for User Profile Management System
Tests the basic functionality without complex mocking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from streamlit_user_profile_components import UserProfileManager, UserProfileData
from streamlit_api_client import EnhancedEdAgentAPI
from streamlit_session_manager import SessionManager, UserInfo


class TestUserProfileIntegration:
    """Integration tests for user profile management"""
    
    def test_profile_completion_calculation(self):
        """Test profile completion calculation logic"""
        manager = UserProfileManager(Mock(), Mock())
        
        # Empty profile
        empty_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com"
        )
        completion = manager._calculate_profile_completion(empty_profile)
        assert completion == 0.0
        
        # Profile with name only
        profile_with_name = UserProfileData(
            user_id="test_user",
            email="test@example.com",
            name="Test User"
        )
        completion = manager._calculate_profile_completion(profile_with_name)
        assert completion == 20.0  # 1 out of 5 sections
        
        # Profile with name and skills
        profile_with_skills = UserProfileData(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            current_skills={
                "Python": {"level": "intermediate"},
                "JavaScript": {"level": "beginner"},
                "SQL": {"level": "advanced"}
            }
        )
        completion = manager._calculate_profile_completion(profile_with_skills)
        assert completion == 40.0  # 2 out of 5 sections
        
        # Complete profile
        complete_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            current_skills={
                "Python": {"level": "intermediate"},
                "JavaScript": {"level": "beginner"},
                "SQL": {"level": "advanced"}
            },
            career_goals=["Learn programming"],
            learning_preferences={"learning_style": "visual"},
            last_active=datetime.now()
        )
        completion = manager._calculate_profile_completion(complete_profile)
        assert completion == 100.0  # All sections completed
    
    def test_profile_insights_generation(self):
        """Test profile insights generation"""
        manager = UserProfileManager(Mock(), Mock())
        
        # Empty profile should generate warnings
        empty_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com"
        )
        insights = manager._generate_profile_insights(empty_profile)
        
        warning_insights = [i for i in insights if i["type"] == "warning"]
        assert len(warning_insights) >= 2  # Should warn about missing skills and goals
        
        # Complete profile should generate success messages
        complete_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            current_skills={f"Skill_{i}": {"level": "intermediate"} for i in range(6)},
            career_goals=["Goal 1", "Goal 2"],
            learning_preferences={"learning_style": "visual"},
            profile_completion=90.0
        )
        insights = manager._generate_profile_insights(complete_profile)
        
        success_insights = [i for i in insights if i["type"] == "success"]
        assert len(success_insights) >= 2  # Should have success messages for skills and goals
    
    def test_skill_categories_structure(self):
        """Test that skill categories are properly structured"""
        manager = UserProfileManager(Mock(), Mock())
        
        # Verify skill categories exist
        assert len(manager.skill_categories) > 0
        
        # Verify each category has skills
        for category, skills in manager.skill_categories.items():
            assert isinstance(category, str)
            assert isinstance(skills, list)
            assert len(skills) > 0
            
            # Verify all skills are strings
            for skill in skills:
                assert isinstance(skill, str)
                assert len(skill) > 0
    
    def test_career_goal_categories_structure(self):
        """Test that career goal categories are properly structured"""
        manager = UserProfileManager(Mock(), Mock())
        
        # Verify goal categories exist
        assert len(manager.career_goal_categories) > 0
        
        # Verify each category has goals
        for category, goals in manager.career_goal_categories.items():
            assert isinstance(category, str)
            assert isinstance(goals, list)
            assert len(goals) > 0
            
            # Verify all goals are strings
            for goal in goals:
                assert isinstance(goal, str)
                assert len(goal) > 0
    
    def test_skill_levels_definition(self):
        """Test skill levels are properly defined"""
        manager = UserProfileManager(Mock(), Mock())
        
        expected_levels = ["beginner", "intermediate", "advanced"]
        assert manager.skill_levels == expected_levels
    
    @pytest.mark.asyncio
    async def test_load_user_profile_with_mock_api(self):
        """Test loading user profile with mocked API"""
        # Create mock API
        mock_api = Mock(spec=EnhancedEdAgentAPI)
        mock_api.get_user_profile = AsyncMock(return_value={
            "user": {
                "user_id": "test_user_123",
                "current_skills": {"Python": {"level": "intermediate"}},
                "career_goals": ["Learn programming"],
                "learning_preferences": {"learning_style": "visual"}
            }
        })
        
        # Create mock session manager
        mock_session_manager = Mock(spec=SessionManager)
        mock_session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        mock_session_manager.get_cached_data.return_value = None
        mock_session_manager.set_cached_data = Mock()
        
        # Create manager and load profile
        manager = UserProfileManager(mock_api, mock_session_manager)
        profile = await manager.load_user_profile("test_user_123")
        
        # Verify results
        assert profile is not None
        assert profile.user_id == "test_user_123"
        assert len(profile.current_skills) == 1
        assert len(profile.career_goals) == 1
        assert profile.learning_preferences["learning_style"] == "visual"
        assert profile.profile_completion > 0
        
        # Verify API was called
        mock_api.get_user_profile.assert_called_once_with("test_user_123")
        
        # Verify caching was used
        mock_session_manager.set_cached_data.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])