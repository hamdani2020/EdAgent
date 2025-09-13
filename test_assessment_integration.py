"""
Comprehensive tests for the assessment system integration
Tests the complete assessment workflow including API integration, state management, and UI components.
"""

import pytest
import asyncio
import streamlit as st
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

# Import the components to test
from streamlit_assessment_components import (
    AssessmentManager,
    render_assessment_dashboard,
    render_assessment_history_section,
    render_active_assessment_section,
    start_assessment_session,
    submit_assessment_response,
    complete_assessment_session,
    render_assessment_results
)
from streamlit_api_client import EnhancedEdAgentAPI, AssessmentSession
from streamlit_session_manager import SessionManager


class TestAssessmentManager:
    """Test the AssessmentManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        self.assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Clear streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    def test_assessment_manager_initialization(self):
        """Test AssessmentManager initialization"""
        assert self.assessment_manager.api == self.mock_api
        assert self.assessment_manager.session_manager == self.mock_session_manager
        assert self.assessment_manager.session_key_prefix == "assessment_"
    
    def test_get_set_current_assessment(self):
        """Test getting and setting current assessment"""
        # Test when no assessment exists
        assert self.assessment_manager.get_current_assessment() is None
        
        # Test setting and getting assessment
        mock_assessment = Mock(spec=AssessmentSession)
        mock_assessment.id = "test_assessment_123"
        mock_assessment.skill_area = "python"
        
        self.assessment_manager.set_current_assessment(mock_assessment)
        retrieved_assessment = self.assessment_manager.get_current_assessment()
        
        assert retrieved_assessment == mock_assessment
        assert retrieved_assessment.id == "test_assessment_123"
    
    def test_get_set_assessment_history(self):
        """Test getting and setting assessment history"""
        # Test empty history
        assert self.assessment_manager.get_assessment_history() == []
        
        # Test setting and getting history
        test_history = [
            {"id": "1", "skill_area": "python", "status": "completed"},
            {"id": "2", "skill_area": "javascript", "status": "in_progress"}
        ]
        
        self.assessment_manager.set_assessment_history(test_history)
        retrieved_history = self.assessment_manager.get_assessment_history()
        
        assert retrieved_history == test_history
        assert len(retrieved_history) == 2
    
    def test_assessment_responses_management(self):
        """Test assessment response management"""
        # Test empty responses
        assert self.assessment_manager.get_assessment_responses() == {}
        
        # Test setting responses
        self.assessment_manager.set_assessment_response(0, "Answer to question 1")
        self.assessment_manager.set_assessment_response(1, "Answer to question 2")
        
        responses = self.assessment_manager.get_assessment_responses()
        assert responses[0] == "Answer to question 1"
        assert responses[1] == "Answer to question 2"
        assert len(responses) == 2
    
    def test_clear_assessment_state(self):
        """Test clearing assessment state"""
        # Set up some state
        mock_assessment = Mock(spec=AssessmentSession)
        self.assessment_manager.set_current_assessment(mock_assessment)
        self.assessment_manager.set_assessment_response(0, "Test response")
        self.assessment_manager.set_assessment_start_time(datetime.now())
        
        # Clear state
        self.assessment_manager.clear_assessment_state()
        
        # Verify state is cleared
        assert self.assessment_manager.get_current_assessment() is None
        assert self.assessment_manager.get_assessment_responses() == {}
        assert self.assessment_manager.get_assessment_start_time() is None
    
    def test_assessment_timing(self):
        """Test assessment timing functionality"""
        # Test when no start time is set
        assert self.assessment_manager.get_assessment_start_time() is None
        
        # Test setting and getting start time
        start_time = datetime.now()
        self.assessment_manager.set_assessment_start_time(start_time)
        retrieved_time = self.assessment_manager.get_assessment_start_time()
        
        assert retrieved_time == start_time


class TestAssessmentWorkflow:
    """Test the complete assessment workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        
        # Mock user info
        self.mock_user = Mock()
        self.mock_user.user_id = "test_user_123"
        self.mock_user.email = "test@example.com"
        self.mock_user.name = "Test User"
        
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.get_current_user.return_value = self.mock_user
        
        # Clear streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    @pytest.mark.asyncio
    async def test_start_assessment_session_success(self):
        """Test successful assessment session start"""
        # Mock API response
        mock_assessment = Mock(spec=AssessmentSession)
        mock_assessment.id = "assessment_123"
        mock_assessment.skill_area = "python"
        mock_assessment.status = "active"
        mock_assessment.questions = [
            {"question": "What is Python?", "type": "open", "index": 0},
            {"question": "Rate your Python skills", "type": "rating", "index": 1}
        ]
        mock_assessment.current_question_index = 0
        mock_assessment.progress = 0.0
        
        self.mock_api.start_assessment = AsyncMock(return_value=mock_assessment)
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.success = Mock()
            mock_st.info = Mock()
            mock_st.rerun = Mock()
            
            # Test the function
            start_assessment_session(assessment_manager, "test_user_123", "python", "Standard (10 questions)")
            
            # Verify API was called
            self.mock_api.start_assessment.assert_called_once_with("test_user_123", "python")
            
            # Verify success message was shown
            mock_st.success.assert_called_once()
            mock_st.rerun.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_assessment_session_failure(self):
        """Test assessment session start failure"""
        # Mock API failure
        self.mock_api.start_assessment = AsyncMock(return_value=None)
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()
            
            # Test the function
            start_assessment_session(assessment_manager, "test_user_123", "python", "Standard (10 questions)")
            
            # Verify error message was shown
            mock_st.error.assert_called_once_with("Failed to start assessment. Please try again.")
    
    @pytest.mark.asyncio
    async def test_submit_assessment_response_success(self):
        """Test successful assessment response submission"""
        # Mock updated assessment
        mock_updated_assessment = Mock(spec=AssessmentSession)
        mock_updated_assessment.id = "assessment_123"
        mock_updated_assessment.current_question_index = 1
        mock_updated_assessment.progress = 0.5
        
        self.mock_api.submit_assessment_response = AsyncMock(return_value=mock_updated_assessment)
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.success = Mock()
            mock_st.rerun = Mock()
            
            # Test the function
            submit_assessment_response(
                assessment_manager, 
                "assessment_123", 
                "Python is a programming language", 
                0, 
                "test_user_123"
            )
            
            # Verify API was called
            self.mock_api.submit_assessment_response.assert_called_once_with("assessment_123", "Python is a programming language")
            
            # Verify success message and rerun
            mock_st.success.assert_called_once_with("✅ Response submitted!")
            mock_st.rerun.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_assessment_session_success(self):
        """Test successful assessment completion"""
        # Mock assessment results
        mock_results = {
            "id": "assessment_123",
            "user_id": "test_user_123",
            "skill_area": "python",
            "overall_score": 85.5,
            "overall_level": "intermediate",
            "confidence_score": 0.8,
            "strengths": ["Good understanding of syntax", "Strong problem-solving"],
            "weaknesses": ["Need to improve on advanced topics"],
            "recommendations": ["Practice more complex algorithms", "Study object-oriented programming"],
            "detailed_scores": {"syntax": 90, "algorithms": 75, "oop": 80}
        }
        
        mock_history = [
            {"id": "assessment_123", "skill_area": "python", "status": "completed", "overall_score": 85.5}
        ]
        
        self.mock_api.complete_assessment = AsyncMock(return_value=mock_results)
        self.mock_api.get_user_assessments = AsyncMock(return_value=mock_history)
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st, \
             patch('streamlit_assessment_components.render_assessment_results') as mock_render_results:
            
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.success = Mock()
            mock_st.balloons = Mock()
            
            # Test the function
            complete_assessment_session(assessment_manager, "assessment_123", "test_user_123")
            
            # Verify API calls
            self.mock_api.complete_assessment.assert_called_once_with("assessment_123")
            self.mock_api.get_user_assessments.assert_called_once_with("test_user_123")
            
            # Verify results rendering
            mock_render_results.assert_called_once_with(mock_results)
            
            # Verify success indicators
            mock_st.success.assert_called_once_with("🎉 Assessment completed successfully!")
            mock_st.balloons.assert_called_once()


class TestAssessmentUI:
    """Test assessment UI components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        
        # Mock user info
        self.mock_user = Mock()
        self.mock_user.user_id = "test_user_123"
        
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.get_current_user.return_value = self.mock_user
        
        # Clear streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    def test_render_assessment_results(self):
        """Test assessment results rendering"""
        mock_results = {
            "skill_area": "python",
            "overall_score": 85.5,
            "overall_level": "intermediate",
            "confidence_score": 0.8,
            "strengths": ["Good syntax knowledge", "Problem-solving skills"],
            "weaknesses": ["Advanced topics", "Performance optimization"],
            "recommendations": ["Study algorithms", "Practice OOP"],
            "detailed_scores": {"syntax": 90, "algorithms": 75, "oop": 80}
        }
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st, \
             patch('streamlit_assessment_components.px') as mock_px:
            
            mock_st.header = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
            mock_st.metric = Mock()
            mock_st.subheader = Mock()
            mock_st.write = Mock()
            mock_st.info = Mock()
            mock_st.plotly_chart = Mock()
            mock_st.button = Mock(return_value=False)
            mock_st.download_button = Mock()
            
            # Mock plotly
            mock_fig = Mock()
            mock_px.bar.return_value = mock_fig
            
            # Test the function
            render_assessment_results(mock_results)
            
            # Verify header was rendered
            mock_st.header.assert_called_with("📊 Assessment Results")
            
            # Verify metrics were displayed
            assert mock_st.metric.call_count >= 4  # At least 4 metrics should be displayed
            
            # Verify chart was created and displayed
            mock_px.bar.assert_called_once()
            mock_st.plotly_chart.assert_called_once_with(mock_fig, use_container_width=True)
    
    @patch('streamlit_assessment_components.asyncio.run')
    def test_render_assessment_dashboard_authenticated(self, mock_asyncio_run):
        """Test assessment dashboard rendering for authenticated user"""
        # Mock assessment history
        mock_history = [
            {"id": "1", "skill_area": "python", "status": "completed", "overall_score": 85},
            {"id": "2", "skill_area": "javascript", "status": "in_progress"}
        ]
        
        mock_asyncio_run.return_value = mock_history
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.header = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock()])
            mock_st.divider = Mock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.success = Mock()
            
            # Mock session state
            mock_st.session_state = {}
            
            # Test the function
            render_assessment_dashboard(self.mock_api, self.mock_session_manager)
            
            # Verify header was rendered
            mock_st.header.assert_called_with("📊 Skill Assessment Dashboard")
            
            # Verify API was called to load history
            mock_asyncio_run.assert_called_once()
    
    def test_render_assessment_dashboard_unauthenticated(self):
        """Test assessment dashboard rendering for unauthenticated user"""
        self.mock_session_manager.is_authenticated.return_value = False
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.header = Mock()
            mock_st.warning = Mock()
            
            # Test the function
            render_assessment_dashboard(self.mock_api, self.mock_session_manager)
            
            # Verify warning was shown
            mock_st.warning.assert_called_with("🔐 Please log in to access skill assessments.")


class TestAssessmentDataPersistence:
    """Test assessment data persistence and state management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        
        # Clear streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    def test_assessment_state_persistence(self):
        """Test that assessment state persists across interactions"""
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Create mock assessment
        mock_assessment = Mock(spec=AssessmentSession)
        mock_assessment.id = "test_assessment"
        mock_assessment.skill_area = "python"
        mock_assessment.current_question_index = 2
        mock_assessment.progress = 0.4
        
        # Set assessment and responses
        assessment_manager.set_current_assessment(mock_assessment)
        assessment_manager.set_assessment_response(0, "Answer 1")
        assessment_manager.set_assessment_response(1, "Answer 2")
        
        # Verify persistence
        retrieved_assessment = assessment_manager.get_current_assessment()
        assert retrieved_assessment.id == "test_assessment"
        assert retrieved_assessment.current_question_index == 2
        
        responses = assessment_manager.get_assessment_responses()
        assert responses[0] == "Answer 1"
        assert responses[1] == "Answer 2"
    
    def test_assessment_history_management(self):
        """Test assessment history management"""
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Test empty history
        assert assessment_manager.get_assessment_history() == []
        
        # Add history items
        history_items = [
            {
                "id": "assessment_1",
                "skill_area": "python",
                "status": "completed",
                "overall_score": 85.0,
                "completed_at": "2024-01-15T10:00:00"
            },
            {
                "id": "assessment_2", 
                "skill_area": "javascript",
                "status": "completed",
                "overall_score": 78.5,
                "completed_at": "2024-01-14T15:30:00"
            }
        ]
        
        assessment_manager.set_assessment_history(history_items)
        retrieved_history = assessment_manager.get_assessment_history()
        
        assert len(retrieved_history) == 2
        assert retrieved_history[0]["skill_area"] == "python"
        assert retrieved_history[1]["overall_score"] == 78.5
    
    def test_assessment_timing_tracking(self):
        """Test assessment timing functionality"""
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Test initial state
        assert assessment_manager.get_assessment_start_time() is None
        
        # Set start time
        start_time = datetime.now()
        assessment_manager.set_assessment_start_time(start_time)
        
        # Verify timing
        retrieved_time = assessment_manager.get_assessment_start_time()
        assert retrieved_time == start_time
        
        # Test elapsed time calculation (would be done in UI)
        elapsed = datetime.now() - retrieved_time
        assert elapsed.total_seconds() >= 0


class TestAssessmentErrorHandling:
    """Test error handling in assessment system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        
        # Mock user info
        self.mock_user = Mock()
        self.mock_user.user_id = "test_user_123"
        
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.get_current_user.return_value = self.mock_user
        
        # Clear streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    @pytest.mark.asyncio
    async def test_api_error_handling_start_assessment(self):
        """Test error handling when starting assessment fails"""
        # Mock API exception
        self.mock_api.start_assessment = AsyncMock(side_effect=Exception("API Error"))
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()
            
            # Test the function
            start_assessment_session(assessment_manager, "test_user_123", "python", "Standard (10 questions)")
            
            # Verify error message was shown
            mock_st.error.assert_called_once_with("Error starting assessment: API Error")
    
    @pytest.mark.asyncio
    async def test_api_error_handling_submit_response(self):
        """Test error handling when submitting response fails"""
        # Mock API exception
        self.mock_api.submit_assessment_response = AsyncMock(side_effect=Exception("Network Error"))
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()
            
            # Test the function
            submit_assessment_response(
                assessment_manager,
                "assessment_123",
                "Test response",
                0,
                "test_user_123"
            )
            
            # Verify error message was shown
            mock_st.error.assert_called_once_with("Error submitting response: Network Error")
    
    @pytest.mark.asyncio
    async def test_api_error_handling_complete_assessment(self):
        """Test error handling when completing assessment fails"""
        # Mock API exception
        self.mock_api.complete_assessment = AsyncMock(side_effect=Exception("Server Error"))
        
        assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
        
        # Mock streamlit functions
        with patch('streamlit_assessment_components.st') as mock_st:
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()
            
            # Test the function
            complete_assessment_session(assessment_manager, "assessment_123", "test_user_123")
            
            # Verify error message was shown
            mock_st.error.assert_called_once_with("Error completing assessment: Server Error")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])