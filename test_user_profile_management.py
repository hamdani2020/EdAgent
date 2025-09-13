"""
Comprehensive tests for User Profile Management System

Tests cover:
- Profile data loading and caching
- Skills management (add/update/remove)
- Goals management (add/remove)
- Preferences management
- Profile completion tracking
- Profile setup wizard
- API integration and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st

# Import the components to test
from streamlit_user_profile_components import (
    UserProfileManager, 
    UserProfileData,
    render_user_profile_dashboard,
    render_profile_setup_wizard,
    get_profile_completion_status
)
from streamlit_api_client import EnhancedEdAgentAPI
from streamlit_session_manager import SessionManager, UserInfo, UserPreferences


class TestUserProfileData:
    """Test UserProfileData dataclass"""
    
    def test_user_profile_data_initialization(self):
        """Test UserProfileData initialization with defaults"""
        profile = UserProfileData(
            user_id="test_user_123",
            email="test@example.com"
        )
        
        assert profile.user_id == "test_user_123"
        assert profile.email == "test@example.com"
        assert profile.name is None
        assert profile.current_skills == {}
        assert profile.career_goals == []
        assert profile.learning_preferences is None
        assert profile.profile_completion == 0.0
    
    def test_user_profile_data_with_data(self):
        """Test UserProfileData with complete data"""
        skills = {
            "Python": {
                "level": "advanced",
                "confidence_score": 0.9,
                "last_updated": "2024-01-01T00:00:00"
            }
        }
        
        goals = ["Become a senior developer", "Learn machine learning"]
        
        preferences = {
            "learning_style": "visual",
            "time_commitment": "10-20",
            "budget_preference": "moderate"
        }
        
        profile = UserProfileData(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            current_skills=skills,
            career_goals=goals,
            learning_preferences=preferences,
            profile_completion=85.0
        )
        
        assert profile.name == "Test User"
        assert len(profile.current_skills) == 1
        assert len(profile.career_goals) == 2
        assert profile.learning_preferences["learning_style"] == "visual"
        assert profile.profile_completion == 85.0


class TestUserProfileManager:
    """Test UserProfileManager class"""
    
    @pytest.fixture
    def mock_api(self):
        """Create mock API client"""
        api = Mock(spec=EnhancedEdAgentAPI)
        api.get_user_profile = AsyncMock()
        api.update_user_preferences = AsyncMock()
        api.update_user_skills = AsyncMock()
        api.get_user_goals = AsyncMock()
        api.update_user_goals = AsyncMock()
        return api
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        session_manager.get_cached_data.return_value = None
        session_manager.set_cached_data = Mock()
        session_manager.clear_cached_data = Mock()
        session_manager.get_user_preferences.return_value = None
        session_manager.update_user_preferences = Mock()
        return session_manager
    
    @pytest.fixture
    def profile_manager(self, mock_api, mock_session_manager):
        """Create UserProfileManager instance"""
        return UserProfileManager(mock_api, mock_session_manager)
    
    @pytest.mark.asyncio
    async def test_load_user_profile_success(self, profile_manager, mock_api):
        """Test successful user profile loading"""
        # Mock API response
        mock_profile_data = {
            "user": {
                "user_id": "test_user_123",
                "current_skills": {
                    "Python": {
                        "level": "intermediate",
                        "confidence_score": 0.8
                    }
                },
                "career_goals": ["Learn Python", "Build web apps"],
                "learning_preferences": {
                    "learning_style": "visual",
                    "time_commitment": "5-10"
                }
            }
        }
        
        mock_api.get_user_profile.return_value = mock_profile_data
        
        # Load profile
        profile = await profile_manager.load_user_profile("test_user_123")
        
        # Verify results
        assert profile is not None
        assert profile.user_id == "test_user_123"
        assert len(profile.current_skills) == 1
        assert len(profile.career_goals) == 2
        assert profile.learning_preferences["learning_style"] == "visual"
        assert profile.profile_completion > 0
        
        # Verify API was called
        mock_api.get_user_profile.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    async def test_load_user_profile_cached(self, profile_manager, mock_session_manager):
        """Test loading profile from cache"""
        # Mock cached data
        cached_profile = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "current_skills": {},
            "career_goals": [],
            "profile_completion": 20.0
        }
        
        mock_session_manager.get_cached_data.return_value = cached_profile
        
        # Load profile (should use cache)
        profile = await profile_manager.load_user_profile("test_user_123")
        
        # Verify results
        assert profile is not None
        assert profile.user_id == "test_user_123"
        assert profile.profile_completion == 20.0
        
        # Verify cache was used
        mock_session_manager.get_cached_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_user_profile_api_error(self, profile_manager, mock_api):
        """Test profile loading with API error"""
        mock_api.get_user_profile.return_value = None
        
        # Load profile
        profile = await profile_manager.load_user_profile("test_user_123")
        
        # Verify error handling
        assert profile is None
        mock_api.get_user_profile.assert_called_once_with("test_user_123")
    
    def test_calculate_profile_completion(self, profile_manager):
        """Test profile completion calculation"""
        # Test empty profile
        empty_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com"
        )
        completion = profile_manager._calculate_profile_completion(empty_profile)
        assert completion == 0.0
        
        # Test partial profile
        partial_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            current_skills={"Python": {"level": "intermediate"}},
            career_goals=["Learn programming"]
        )
        completion = profile_manager._calculate_profile_completion(partial_profile)
        assert completion == 60.0  # 3 out of 5 sections completed
        
        # Test complete profile
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
        completion = profile_manager._calculate_profile_completion(complete_profile)
        assert completion == 100.0  # All sections completed
    
    @pytest.mark.asyncio
    async def test_add_or_update_skill_success(self, profile_manager, mock_api):
        """Test successful skill addition/update"""
        mock_api.update_user_skills.return_value = True
        
        # Add skill
        success = profile_manager._add_or_update_skill(
            "test_user_123",
            "Python",
            "intermediate",
            0.8
        )
        
        # Verify success
        assert success is True
        
        # Verify API call
        mock_api.update_user_skills.assert_called_once()
        call_args = mock_api.update_user_skills.call_args[0]
        assert call_args[0] == "test_user_123"
        assert "Python" in call_args[1]
        assert call_args[1]["Python"]["level"] == "intermediate"
        assert call_args[1]["Python"]["confidence_score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_add_or_update_skill_failure(self, profile_manager, mock_api):
        """Test skill addition/update failure"""
        mock_api.update_user_skills.return_value = False
        
        # Try to add skill
        success = profile_manager._add_or_update_skill(
            "test_user_123",
            "Python",
            "intermediate",
            0.8
        )
        
        # Verify failure
        assert success is False
    
    @pytest.mark.asyncio
    async def test_remove_skill_success(self, profile_manager, mock_api):
        """Test successful skill removal"""
        # Mock current profile with skills
        mock_profile_data = {
            "user": {
                "user_id": "test_user_123",
                "current_skills": {
                    "Python": {"level": "intermediate"},
                    "JavaScript": {"level": "beginner"}
                }
            }
        }
        
        mock_api.get_user_profile.return_value = mock_profile_data
        mock_api.update_user_skills.return_value = True
        
        # Remove skill
        success = profile_manager._remove_skill("test_user_123", "Python")
        
        # Verify success
        assert success is True
        
        # Verify API calls
        mock_api.get_user_profile.assert_called_once()
        mock_api.update_user_skills.assert_called_once()
        
        # Verify remaining skills
        call_args = mock_api.update_user_skills.call_args[0]
        remaining_skills = call_args[1]
        assert "Python" not in remaining_skills
        assert "JavaScript" in remaining_skills
    
    @pytest.mark.asyncio
    async def test_add_goal_success(self, profile_manager, mock_api):
        """Test successful goal addition"""
        mock_api.get_user_goals.return_value = ["Existing goal"]
        mock_api.update_user_goals.return_value = True
        
        # Add goal
        success = profile_manager._add_goal("test_user_123", "New goal")
        
        # Verify success
        assert success is True
        
        # Verify API calls
        mock_api.get_user_goals.assert_called_once_with("test_user_123")
        mock_api.update_user_goals.assert_called_once_with(
            "test_user_123", 
            ["Existing goal", "New goal"]
        )
    
    @pytest.mark.asyncio
    async def test_add_duplicate_goal(self, profile_manager, mock_api):
        """Test adding duplicate goal"""
        mock_api.get_user_goals.return_value = ["Existing goal"]
        
        # Try to add duplicate goal
        success = profile_manager._add_goal("test_user_123", "Existing goal")
        
        # Verify success (no change needed)
        assert success is True
        
        # Verify no update call was made
        mock_api.update_user_goals.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_goal_success(self, profile_manager, mock_api):
        """Test successful goal removal"""
        mock_api.get_user_goals.return_value = ["Goal 1", "Goal 2", "Goal 3"]
        mock_api.update_user_goals.return_value = True
        
        # Remove goal
        success = profile_manager._remove_goal("test_user_123", "Goal 2")
        
        # Verify success
        assert success is True
        
        # Verify API calls
        mock_api.get_user_goals.assert_called_once_with("test_user_123")
        mock_api.update_user_goals.assert_called_once_with(
            "test_user_123", 
            ["Goal 1", "Goal 3"]
        )
    
    def test_generate_profile_insights(self, profile_manager):
        """Test profile insights generation"""
        # Test profile with no skills or goals
        empty_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com"
        )
        
        insights = profile_manager._generate_profile_insights(empty_profile)
        
        # Should have warnings for missing skills and goals
        warning_insights = [i for i in insights if i["type"] == "warning"]
        assert len(warning_insights) >= 2  # At least skills and goals warnings
        
        # Test complete profile
        complete_profile = UserProfileData(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            current_skills={f"Skill_{i}": {"level": "intermediate"} for i in range(6)},
            career_goals=["Goal 1", "Goal 2", "Goal 3"],
            learning_preferences={"learning_style": "visual"},
            profile_completion=90.0
        )
        
        insights = profile_manager._generate_profile_insights(complete_profile)
        
        # Should have success insights
        success_insights = [i for i in insights if i["type"] == "success"]
        assert len(success_insights) >= 2  # At least skills and goals success


class TestStreamlitIntegration:
    """Test Streamlit integration components"""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components"""
        with patch('streamlit_user_profile_components.st') as mock_st:
            # Mock common Streamlit functions
            mock_st.header = Mock()
            mock_st.subheader = Mock()
            mock_st.write = Mock()
            mock_st.info = Mock()
            mock_st.warning = Mock()
            mock_st.error = Mock()
            mock_st.success = Mock()
            mock_st.spinner = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock()])
            mock_st.tabs = Mock(return_value=[Mock() for _ in range(5)])
            mock_st.expander = Mock()
            mock_st.form = Mock()
            mock_st.button = Mock(return_value=False)
            mock_st.selectbox = Mock(return_value="default")
            mock_st.multiselect = Mock(return_value=[])
            mock_st.text_input = Mock(return_value="")
            mock_st.text_area = Mock(return_value="")
            mock_st.slider = Mock(return_value=50)
            mock_st.checkbox = Mock(return_value=False)
            mock_st.dataframe = Mock()
            mock_st.plotly_chart = Mock()
            mock_st.progress = Mock()
            mock_st.rerun = Mock()
            mock_st.balloons = Mock()
            
            # Mock session state
            mock_st.session_state = {}
            
            yield mock_st
    
    @pytest.fixture
    def mock_components(self, mock_streamlit):
        """Setup mocked components for testing"""
        mock_api = Mock(spec=EnhancedEdAgentAPI)
        mock_session_manager = Mock(spec=SessionManager)
        
        # Setup authentication
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        return mock_api, mock_session_manager
    
    @patch('streamlit_user_profile_components.asyncio.run')
    def test_render_user_profile_dashboard_authenticated(
        self, 
        mock_asyncio_run, 
        mock_streamlit, 
        mock_components
    ):
        """Test rendering profile dashboard for authenticated user"""
        mock_api, mock_session_manager = mock_components
        
        # Mock profile data
        mock_profile = UserProfileData(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            current_skills={"Python": {"level": "intermediate"}},
            career_goals=["Learn programming"],
            profile_completion=60.0
        )
        
        mock_asyncio_run.return_value = mock_profile
        
        # Render dashboard
        render_user_profile_dashboard(mock_api, mock_session_manager)
        
        # Verify authentication check
        mock_session_manager.is_authenticated.assert_called()
        
        # Verify profile loading
        mock_asyncio_run.assert_called()
        
        # Verify UI rendering
        mock_streamlit.header.assert_called_with("👤 User Profile")
        mock_streamlit.tabs.assert_called()
    
    def test_render_user_profile_dashboard_unauthenticated(
        self, 
        mock_streamlit, 
        mock_components
    ):
        """Test rendering profile dashboard for unauthenticated user"""
        mock_api, mock_session_manager = mock_components
        
        # Setup unauthenticated state
        mock_session_manager.is_authenticated.return_value = False
        
        # Render dashboard
        render_user_profile_dashboard(mock_api, mock_session_manager)
        
        # Verify authentication check
        mock_session_manager.is_authenticated.assert_called()
        
        # Verify warning message
        mock_streamlit.warning.assert_called_with("🔐 Please log in to view your profile.")
    
    @patch('streamlit_user_profile_components.asyncio.run')
    def test_render_profile_setup_wizard(
        self, 
        mock_asyncio_run, 
        mock_streamlit, 
        mock_components
    ):
        """Test rendering profile setup wizard"""
        mock_api, mock_session_manager = mock_components
        
        # Mock session state for wizard
        mock_streamlit.session_state = {"wizard_step": 1}
        
        # Render wizard
        render_profile_setup_wizard(mock_api, mock_session_manager)
        
        # Verify authentication check
        mock_session_manager.is_authenticated.assert_called()
        
        # Verify wizard UI rendering
        mock_streamlit.header.assert_called_with("🚀 Profile Setup Wizard")
        mock_streamlit.progress.assert_called()
    
    @patch('streamlit_user_profile_components.asyncio.run')
    def test_get_profile_completion_status(
        self, 
        mock_asyncio_run, 
        mock_components
    ):
        """Test getting profile completion status"""
        mock_api, mock_session_manager = mock_components
        
        # Mock profile with completion
        mock_profile = UserProfileData(
            user_id="test_user_123",
            email="test@example.com",
            profile_completion=75.0
        )
        
        mock_asyncio_run.return_value = mock_profile
        
        # Get completion status
        completion = get_profile_completion_status(mock_api, mock_session_manager, "test_user_123")
        
        # Verify result
        assert completion == 75.0
        mock_asyncio_run.assert_called()
    
    @patch('streamlit_user_profile_components.asyncio.run')
    def test_get_profile_completion_status_error(
        self, 
        mock_asyncio_run, 
        mock_components
    ):
        """Test getting profile completion status with error"""
        mock_api, mock_session_manager = mock_components
        
        # Mock error
        mock_asyncio_run.side_effect = Exception("API Error")
        
        # Get completion status
        completion = get_profile_completion_status(mock_api, mock_session_manager, "test_user_123")
        
        # Verify error handling
        assert completion == 0.0


class TestProfileWizardWorkflow:
    """Test profile setup wizard workflow"""
    
    @pytest.fixture
    def wizard_manager(self):
        """Create profile manager for wizard testing"""
        mock_api = Mock(spec=EnhancedEdAgentAPI)
        mock_session_manager = Mock(spec=SessionManager)
        
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        return UserProfileManager(mock_api, mock_session_manager)
    
    @patch('streamlit_user_profile_components.st')
    def test_wizard_step_navigation(self, mock_st, wizard_manager):
        """Test wizard step navigation"""
        # Mock session state
        mock_st.session_state = {"wizard_step": 1}
        
        # Mock user info
        user_info = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        # Test step 1 (basic info)
        wizard_manager._wizard_step_basic_info(user_info)
        
        # Verify UI elements
        mock_st.subheader.assert_called_with("👤 Basic Information")
        mock_st.form.assert_called()
    
    @patch('streamlit_user_profile_components.st')
    def test_wizard_goals_step(self, mock_st, wizard_manager):
        """Test wizard goals step"""
        # Mock session state
        mock_st.session_state = {"wizard_step": 2, "wizard_goals": []}
        
        # Mock user info
        user_info = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        # Test step 2 (career goals)
        wizard_manager._wizard_step_career_goals(user_info)
        
        # Verify UI elements
        mock_st.subheader.assert_called_with("🎯 Career Goals")
        mock_st.columns.assert_called()
    
    @patch('streamlit_user_profile_components.st')
    def test_wizard_skills_step(self, mock_st, wizard_manager):
        """Test wizard skills step"""
        # Mock session state
        mock_st.session_state = {"wizard_step": 3, "wizard_skills": {}}
        
        # Mock user info
        user_info = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        # Test step 3 (skills)
        wizard_manager._wizard_step_skills(user_info)
        
        # Verify UI elements
        mock_st.subheader.assert_called_with("🎯 Skills Assessment")
        mock_st.selectbox.assert_called()
    
    @patch('streamlit_user_profile_components.asyncio.run')
    def test_save_wizard_profile_success(self, mock_asyncio_run, wizard_manager):
        """Test successful wizard profile save"""
        # Mock API responses
        mock_asyncio_run.return_value = True
        
        # Mock session state with wizard data
        with patch('streamlit_user_profile_components.st.session_state', {
            "wizard_goals": ["Learn Python", "Build web apps"],
            "wizard_skills": {
                "Python": {"level": "beginner", "confidence": 0.6}
            },
            "wizard_preferences": {
                "learning_style": "visual",
                "time_commitment": "5-10"
            }
        }):
            # Mock user info
            user_info = UserInfo(
                user_id="test_user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Save wizard profile
            success = wizard_manager._save_wizard_profile(user_info)
            
            # Verify success
            assert success is True
            
            # Verify API calls were made
            assert mock_asyncio_run.call_count >= 2  # At least goals and skills


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])