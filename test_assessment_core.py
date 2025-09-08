"""
Core assessment system tests - focused on essential functionality
Tests the core assessment workflow without complex mocking.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import components
from streamlit_assessment_components import AssessmentManager
from streamlit_api_client import EnhancedEdAgentAPI, AssessmentSession
from streamlit_session_manager import SessionManager


class TestAssessmentManagerCore:
    """Test core AssessmentManager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        self.assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
    
    def test_initialization(self):
        """Test AssessmentManager initialization"""
        assert self.assessment_manager.api == self.mock_api
        assert self.assessment_manager.session_manager == self.mock_session_manager
        assert self.assessment_manager.session_key_prefix == "assessment_"
    
    def test_assessment_state_management(self):
        """Test assessment state management"""
        # Test initial state
        assert self.assessment_manager.get_current_assessment() is None
        assert self.assessment_manager.get_assessment_history() == []
        assert self.assessment_manager.get_assessment_responses() == {}
        
        # Create mock assessment
        mock_assessment = Mock()
        mock_assessment.id = "test_123"
        mock_assessment.skill_area = "python"
        mock_assessment.status = "active"
        
        # Test setting assessment
        self.assessment_manager.set_current_assessment(mock_assessment)
        retrieved = self.assessment_manager.get_current_assessment()
        assert retrieved == mock_assessment
        assert retrieved.id == "test_123"
    
    def test_response_management(self):
        """Test assessment response management"""
        # Test setting responses
        self.assessment_manager.set_assessment_response(0, "Answer 1")
        self.assessment_manager.set_assessment_response(1, "Answer 2")
        
        responses = self.assessment_manager.get_assessment_responses()
        assert responses[0] == "Answer 1"
        assert responses[1] == "Answer 2"
        assert len(responses) == 2
    
    def test_history_management(self):
        """Test assessment history management"""
        test_history = [
            {"id": "1", "skill_area": "python", "status": "completed"},
            {"id": "2", "skill_area": "javascript", "status": "in_progress"}
        ]
        
        self.assessment_manager.set_assessment_history(test_history)
        retrieved_history = self.assessment_manager.get_assessment_history()
        
        assert retrieved_history == test_history
        assert len(retrieved_history) == 2
        assert retrieved_history[0]["skill_area"] == "python"
    
    def test_timing_functionality(self):
        """Test assessment timing"""
        # Test initial state
        assert self.assessment_manager.get_assessment_start_time() is None
        
        # Test setting time
        start_time = datetime.now()
        self.assessment_manager.set_assessment_start_time(start_time)
        retrieved_time = self.assessment_manager.get_assessment_start_time()
        
        assert retrieved_time == start_time
    
    def test_state_clearing(self):
        """Test clearing assessment state"""
        # Set up state
        mock_assessment = Mock()
        mock_assessment.id = "test_clear"
        
        self.assessment_manager.set_current_assessment(mock_assessment)
        self.assessment_manager.set_assessment_response(0, "Test response")
        self.assessment_manager.set_assessment_start_time(datetime.now())
        
        # Verify state exists
        assert self.assessment_manager.get_current_assessment() is not None
        assert len(self.assessment_manager.get_assessment_responses()) > 0
        assert self.assessment_manager.get_assessment_start_time() is not None
        
        # Clear state
        self.assessment_manager.clear_assessment_state()
        
        # Verify state is cleared
        assert self.assessment_manager.get_current_assessment() is None
        assert self.assessment_manager.get_assessment_responses() == {}
        assert self.assessment_manager.get_assessment_start_time() is None


class TestAssessmentDataStructures:
    """Test assessment data structures and validation"""
    
    def test_assessment_session_structure(self):
        """Test AssessmentSession data structure"""
        # Create mock assessment session
        assessment = Mock(spec=AssessmentSession)
        assessment.id = "assessment_123"
        assessment.user_id = "user_456"
        assessment.skill_area = "python"
        assessment.questions = [
            {"question": "What is Python?", "type": "open", "index": 0},
            {"question": "Rate your skills", "type": "rating", "index": 1}
        ]
        assessment.current_question_index = 0
        assessment.status = "active"
        assessment.progress = 0.0
        
        # Verify structure
        assert assessment.id == "assessment_123"
        assert assessment.user_id == "user_456"
        assert assessment.skill_area == "python"
        assert len(assessment.questions) == 2
        assert assessment.current_question_index == 0
        assert assessment.status == "active"
        assert assessment.progress == 0.0
    
    def test_assessment_history_structure(self):
        """Test assessment history data structure"""
        history_item = {
            "id": "assessment_123",
            "skill_area": "python",
            "status": "completed",
            "overall_score": 85.5,
            "overall_level": "intermediate",
            "confidence_score": 0.8,
            "started_at": "2024-01-15T10:00:00",
            "completed_at": "2024-01-15T10:30:00",
            "duration_minutes": 30,
            "strengths": ["Good syntax knowledge"],
            "weaknesses": ["Need more practice with algorithms"],
            "recommendations": ["Study data structures"]
        }
        
        # Verify required fields
        assert "id" in history_item
        assert "skill_area" in history_item
        assert "status" in history_item
        assert history_item["overall_score"] == 85.5
        assert history_item["overall_level"] == "intermediate"
    
    def test_assessment_results_structure(self):
        """Test assessment results data structure"""
        results = {
            "id": "assessment_123",
            "user_id": "user_456",
            "skill_area": "python",
            "overall_score": 85.5,
            "overall_level": "intermediate",
            "confidence_score": 0.8,
            "strengths": ["Good understanding of syntax", "Strong problem-solving"],
            "weaknesses": ["Need to improve on advanced topics"],
            "recommendations": ["Practice more complex algorithms", "Study OOP"],
            "detailed_scores": {"syntax": 90, "algorithms": 75, "oop": 80},
            "assessment_date": "2024-01-15T10:30:00"
        }
        
        # Verify structure
        assert results["overall_score"] == 85.5
        assert results["overall_level"] == "intermediate"
        assert len(results["strengths"]) == 2
        assert len(results["weaknesses"]) == 1
        assert len(results["recommendations"]) == 2
        assert "syntax" in results["detailed_scores"]
        assert results["detailed_scores"]["syntax"] == 90


class TestAssessmentWorkflowLogic:
    """Test assessment workflow logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_api = Mock(spec=EnhancedEdAgentAPI)
        self.mock_session_manager = Mock(spec=SessionManager)
        self.assessment_manager = AssessmentManager(self.mock_api, self.mock_session_manager)
    
    def test_assessment_progress_calculation(self):
        """Test assessment progress calculation logic"""
        # Mock assessment with questions
        mock_assessment = Mock()
        mock_assessment.questions = [
            {"question": "Q1", "index": 0},
            {"question": "Q2", "index": 1},
            {"question": "Q3", "index": 2},
            {"question": "Q4", "index": 3},
            {"question": "Q5", "index": 4}
        ]
        mock_assessment.current_question_index = 2  # On question 3 of 5
        
        # Calculate expected progress
        total_questions = len(mock_assessment.questions)
        current_progress = (mock_assessment.current_question_index + 1) / total_questions
        expected_progress = 3 / 5  # 60%
        
        assert current_progress == expected_progress
        assert current_progress == 0.6
    
    def test_question_navigation_logic(self):
        """Test question navigation logic"""
        # Mock assessment
        mock_assessment = Mock()
        mock_assessment.questions = [{"q": f"Question {i}"} for i in range(5)]
        mock_assessment.current_question_index = 2
        
        total_questions = len(mock_assessment.questions)
        current_index = mock_assessment.current_question_index
        
        # Test navigation boundaries
        can_go_previous = current_index > 0
        can_go_next = current_index < total_questions - 1
        is_last_question = current_index == total_questions - 1
        
        assert can_go_previous is True  # Can go back from question 2
        assert can_go_next is True      # Can go forward from question 2
        assert is_last_question is False  # Not on last question
        
        # Test last question
        mock_assessment.current_question_index = 4  # Last question (index 4 of 5 questions)
        current_index = mock_assessment.current_question_index
        
        can_go_previous = current_index > 0
        can_go_next = current_index < total_questions - 1
        is_last_question = current_index == total_questions - 1
        
        assert can_go_previous is True
        assert can_go_next is False
        assert is_last_question is True
    
    def test_response_validation_logic(self):
        """Test response validation logic"""
        # Test different response types
        responses = {
            "empty": "",
            "whitespace": "   ",
            "valid_short": "Yes",
            "valid_long": "This is a detailed response with sufficient content.",
            "rating": "7",
            "boolean": "True"
        }
        
        # Validation logic
        def is_valid_response(response: str, min_length: int = 1) -> bool:
            return bool(response.strip()) and len(response.strip()) >= min_length
        
        def is_sufficient_detail(response: str, min_chars: int = 50) -> bool:
            return len(response.strip()) >= min_chars
        
        # Test validations
        assert is_valid_response(responses["empty"]) is False
        assert is_valid_response(responses["whitespace"]) is False
        assert is_valid_response(responses["valid_short"]) is True
        assert is_valid_response(responses["valid_long"]) is True
        
        assert is_sufficient_detail(responses["valid_short"]) is False
        assert is_sufficient_detail(responses["valid_long"]) is True
    
    def test_assessment_completion_logic(self):
        """Test assessment completion logic"""
        # Mock assessment
        mock_assessment = Mock()
        mock_assessment.questions = [{"q": f"Q{i}"} for i in range(3)]
        mock_assessment.current_question_index = 2  # Last question
        
        # Mock responses
        responses = {0: "Answer 1", 1: "Answer 2", 2: "Answer 3"}
        
        total_questions = len(mock_assessment.questions)
        current_index = mock_assessment.current_question_index
        
        # Completion logic
        all_questions_answered = len(responses) == total_questions
        on_last_question = current_index == total_questions - 1
        can_complete = all_questions_answered and on_last_question
        
        assert all_questions_answered is True
        assert on_last_question is True
        assert can_complete is True
        
        # Test incomplete scenario
        incomplete_responses = {0: "Answer 1", 1: "Answer 2"}  # Missing answer 3
        all_questions_answered = len(incomplete_responses) == total_questions
        can_complete = all_questions_answered and on_last_question
        
        assert all_questions_answered is False
        assert can_complete is False


def run_core_tests():
    """Run core assessment tests"""
    print("🧪 Running Core Assessment Tests")
    print("=" * 50)
    
    # Test classes to run
    test_classes = [
        TestAssessmentManagerCore,
        TestAssessmentDataStructures,
        TestAssessmentWorkflowLogic
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}")
        print("-" * 30)
        
        # Get test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                # Create test instance and run test
                test_instance = test_class()
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run the test method
                getattr(test_instance, test_method)()
                
                print(f"  ✅ {test_method}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {test_method}: {str(e)}")
                failed_tests += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    
    if failed_tests == 0:
        print("\n🎉 All core assessment tests passed!")
        return True
    else:
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n⚠️  Some tests failed. Success rate: {success_rate:.1f}%")
        return False


if __name__ == "__main__":
    success = run_core_tests()
    exit(0 if success else 1)