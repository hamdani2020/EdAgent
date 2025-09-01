"""
Integration tests for skill assessment workflow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

from edagent.services.conversation_manager import ConversationManager, ConversationState
from edagent.models.conversation import (
    ConversationResponse, AssessmentSession, Message, MessageType, ConversationStatus
)
from edagent.models.learning import SkillAssessment, DifficultyLevel
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum


class TestSkillAssessmentWorkflow:
    """Test complete skill assessment workflow"""
    
    @pytest.fixture
    def conversation_manager(self):
        """Create ConversationManager instance with mocked dependencies"""
        with patch('edagent.services.conversation_manager.GeminiAIService') as mock_ai, \
             patch('edagent.services.conversation_manager.UserContextManager') as mock_ucm, \
             patch('edagent.services.conversation_manager.ContentRecommender') as mock_cr, \
             patch('edagent.services.conversation_manager.PromptBuilder') as mock_pb, \
             patch('edagent.services.conversation_manager.StructuredResponseHandler') as mock_rh:
            
            manager = ConversationManager()
            manager.ai_service = mock_ai.return_value
            manager.user_context_manager = mock_ucm.return_value
            manager.content_recommender = mock_cr.return_value
            manager.prompt_builder = mock_pb.return_value
            manager.response_handler = mock_rh.return_value
            
            return manager
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week",
            budget_preference="free",
            preferred_platforms=["YouTube", "Coursera"],
            content_types=["video", "interactive"],
            difficulty_preference="gradual"
        )
        
        return UserContext(
            user_id="test-user-123",
            current_skills={},
            career_goals=["become a software developer"],
            learning_preferences=preferences,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
    
    @pytest.fixture
    def sample_skill_assessment(self):
        """Create sample skill assessment result"""
        return SkillAssessment(
            user_id="test-user-123",
            skill_area="Programming",
            overall_level=DifficultyLevel.BEGINNER,
            confidence_score=0.6,
            strengths=["Logical thinking", "Problem-solving mindset", "Eager to learn"],
            weaknesses=["Limited coding experience", "Unfamiliar with programming concepts"],
            recommendations=[
                "Start with Python basics",
                "Practice with simple coding exercises",
                "Join beginner programming communities"
            ],
            detailed_scores={
                "syntax_knowledge": 0.2,
                "problem_solving": 0.7,
                "debugging": 0.3,
                "best_practices": 0.1
            }
        )
    
    @pytest.mark.asyncio
    async def test_assessment_initiation(self, conversation_manager, sample_user_context):
        """Test starting a skill assessment"""
        # Mock dependencies
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        user_id = "test-user-123"
        message = "Can you assess my programming skills?"
        
        response = await conversation_manager.handle_message(user_id, message)
        
        # Verify assessment was initiated
        assert response.response_type == "assessment"
        assert "assess" in response.message.lower()
        
        # Check conversation state
        state = conversation_manager._conversation_states[user_id]
        assert state.is_in_assessment()
        assert state.active_assessment is not None
        assert state.active_assessment.skill_area == "General"
        assert len(state.active_assessment.questions) == 5  # Initial questions
    
    @pytest.mark.asyncio
    async def test_assessment_question_flow(self, conversation_manager, sample_user_context):
        """Test the question and response flow during assessment"""
        # Setup
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Get conversation state
        state = conversation_manager._conversation_states[user_id]
        assessment = state.active_assessment
        
        # Simulate answering questions
        responses = [
            "I'm a complete beginner with computers",
            "I've never done any programming before",
            "I want to become a web developer",
            "I can dedicate about 10 hours per week",
            "I prefer learning through videos and hands-on practice"
        ]
        
        for i, user_response in enumerate(responses[:-1]):  # All but last response
            response = await conversation_manager.handle_message(user_id, user_response)
            
            # Should still be in assessment
            assert response.response_type == "assessment"
            assert state.is_in_assessment()
            assert len(assessment.responses) == i + 1
            assert assessment.current_question_index == i + 1
            
            # Should have progress metadata
            assert "progress" in response.metadata
            assert response.metadata["question_index"] == i + 1
    
    @pytest.mark.asyncio
    async def test_adaptive_question_generation(self, conversation_manager, sample_user_context):
        """Test adaptive question generation based on responses"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        conversation_manager.ai_service._infer_skill_area = MagicMock(return_value="Programming")
        conversation_manager.ai_service._get_model = MagicMock()
        conversation_manager.ai_service._get_generation_config = MagicMock()
        conversation_manager.ai_service._make_api_call = AsyncMock(return_value="What programming languages interest you most?\nHave you tried any coding tutorials before?\nWhat type of applications would you like to build?")
        conversation_manager.response_handler.parse_assessment_questions = MagicMock(return_value=[
            "What programming languages interest you most?",
            "Have you tried any coding tutorials before?",
            "What type of applications would you like to build?"
        ])
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my programming skills")
        
        # Answer first 3 questions to trigger adaptive generation
        responses = [
            "I'm interested in learning programming",
            "I've done some basic HTML and CSS",
            "I want to build websites and web applications"
        ]
        
        for response_text in responses:
            await conversation_manager.handle_message(user_id, response_text)
        
        # Check that adaptive questions were added
        state = conversation_manager._conversation_states[user_id]
        assessment = state.active_assessment
        
        # Should have original 5 + 2 adaptive questions
        assert len(assessment.questions) == 7
        assert assessment.skill_area == "Programming"  # Should be updated from "General"
        
        # Verify AI service was called for adaptive questions
        conversation_manager.ai_service._make_api_call.assert_called()
        conversation_manager.response_handler.parse_assessment_questions.assert_called()
    
    @pytest.mark.asyncio
    async def test_assessment_completion(self, conversation_manager, sample_user_context, sample_skill_assessment):
        """Test assessment completion and result processing"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.update_skills = AsyncMock()
        conversation_manager.user_context_manager.save_assessment_results = AsyncMock()
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        conversation_manager.ai_service.assess_skills = AsyncMock(return_value=sample_skill_assessment)
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Get assessment and manually complete all questions
        state = conversation_manager._conversation_states[user_id]
        assessment = state.active_assessment
        
        # Answer all questions (5 initial + 2 adaptive)
        responses = [
            "I'm a beginner with technology",
            "No programming experience",
            "Want to be a web developer", 
            "Can study 10 hours per week",
            "Prefer video tutorials",
            "I haven't worked on any projects yet",
            "My biggest challenge is not knowing where to start"
        ]
        
        final_response = None
        for response_text in responses:
            final_response = await conversation_manager.handle_message(user_id, response_text)
        
        # Verify assessment completion
        assert final_response.response_type == "assessment"
        assert "Assessment complete" in final_response.message
        assert "Programming" in final_response.message  # Should show skill area
        assert "beginner" in final_response.message.lower()  # Should show level
        
        # Verify state cleanup
        assert not state.is_in_assessment()
        assert state.active_assessment is None
        assert state.current_context is None
        
        # Verify services were called
        conversation_manager.ai_service.assess_skills.assert_called_once()
        conversation_manager.user_context_manager.update_skills.assert_called_once()
        conversation_manager.user_context_manager.save_assessment_results.assert_called_once()
        
        # Verify suggested actions
        assert len(final_response.suggested_actions) > 0
        assert any("learning path" in action.lower() for action in final_response.suggested_actions)
    
    @pytest.mark.asyncio
    async def test_assessment_error_handling(self, conversation_manager, sample_user_context):
        """Test error handling during assessment"""
        # Setup mocks with errors
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        conversation_manager.ai_service.assess_skills = AsyncMock(side_effect=Exception("AI service error"))
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Answer all questions to trigger completion and error
        responses = [
            "Beginner level",
            "No experience",
            "Web development",
            "5 hours per week",
            "Videos",
            "No projects yet",
            "Need guidance"
        ]
        
        final_response = None
        for response_text in responses:
            final_response = await conversation_manager.handle_message(user_id, response_text)
        
        # Should handle error gracefully
        assert final_response.response_type == "text"
        assert "trouble" in final_response.message.lower()
        assert final_response.confidence_score <= 0.5
        
        # State should be reset
        state = conversation_manager._conversation_states[user_id]
        assert not state.is_in_assessment()
    
    @pytest.mark.asyncio
    async def test_assessment_encouragement_messages(self, conversation_manager, sample_user_context):
        """Test encouraging messages during assessment"""
        # Setup
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Test different encouragement messages
        responses = [
            "I'm completely new to this",
            "I've tried a few tutorials",
            "I want to learn web development",
            "I can study evenings and weekends"
        ]
        
        encouragement_phrases = []
        
        for response_text in responses:
            response = await conversation_manager.handle_message(user_id, response_text)
            
            # Extract encouragement from response
            message_parts = response.message.split('!')
            if len(message_parts) > 1:
                encouragement = message_parts[0] + '!'
                encouragement_phrases.append(encouragement)
        
        # Should have different encouraging phrases
        assert len(encouragement_phrases) > 0
        expected_phrases = ["Great start!", "Thanks for that answer!", "You're doing great!", "Almost there!"]
        assert any(phrase in encouragement_phrases for phrase in expected_phrases)
    
    @pytest.mark.asyncio
    async def test_assessment_progress_tracking(self, conversation_manager, sample_user_context):
        """Test progress tracking during assessment"""
        # Setup
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Track progress through questions
        responses = ["Answer 1", "Answer 2", "Answer 3"]
        
        for i, response_text in enumerate(responses):
            response = await conversation_manager.handle_message(user_id, response_text)
            
            # Check progress metadata
            assert "progress" in response.metadata
            assert "total_questions" in response.metadata
            assert response.metadata["question_index"] == i + 1
            
            # Progress calculation depends on total questions (which may include adaptive ones)
            total_questions = response.metadata["total_questions"]
            expected_progress = (i + 1) / total_questions
            assert abs(response.metadata["progress"] - expected_progress) < 0.15  # More lenient due to adaptive questions
    
    @pytest.mark.asyncio
    async def test_skill_area_inference(self, conversation_manager, sample_user_context):
        """Test skill area inference from user responses"""
        # Setup
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        conversation_manager.ai_service._infer_skill_area = MagicMock(return_value="Web Development")
        
        user_id = "test-user-123"
        
        # Start assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Provide responses that should indicate web development
        responses = [
            "I'm interested in technology",
            "I want to learn HTML, CSS, and JavaScript",
            "I want to build websites and web applications"
        ]
        
        for response_text in responses:
            await conversation_manager.handle_message(user_id, response_text)
        
        # Check that skill area was inferred and updated
        state = conversation_manager._conversation_states[user_id]
        assessment = state.active_assessment
        
        # Should be called with user responses
        conversation_manager.ai_service._infer_skill_area.assert_called()
        
        # Skill area should be updated from "General"
        assert assessment.skill_area == "Web Development"
    
    @pytest.mark.asyncio
    async def test_assessment_result_summary_formatting(self, conversation_manager, sample_user_context, sample_skill_assessment):
        """Test formatting of assessment result summary"""
        # Setup
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.update_skills = AsyncMock()
        conversation_manager.user_context_manager.save_assessment_results = AsyncMock()
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        conversation_manager.ai_service.assess_skills = AsyncMock(return_value=sample_skill_assessment)
        
        user_id = "test-user-123"
        
        # Complete assessment
        await conversation_manager.handle_message(user_id, "Assess my skills")
        
        # Answer all questions (7 total: 5 initial + 2 adaptive)
        responses = [
            "I'm a beginner",
            "No programming experience", 
            "Want to learn web development",
            "Can study 5 hours per week",
            "Prefer video tutorials",
            "Haven't worked on projects",
            "Need structured learning"
        ]
        
        final_response = None
        for response_text in responses:
            final_response = await conversation_manager.handle_message(user_id, response_text)
        
        # Check summary formatting
        message = final_response.message
        
        # Should contain key assessment information
        assert "Programming" in message  # Skill area
        assert "Beginner" in message or "beginner" in message  # Level
        assert "0.6" in message or "60%" in message  # Confidence score
        
        # Should contain strengths and weaknesses
        assert any(strength in message for strength in sample_skill_assessment.strengths)
        assert any(weakness in message for weakness in sample_skill_assessment.weaknesses)
        
        # Should contain recommendations
        assert any(rec in message for rec in sample_skill_assessment.recommendations)
        
        # Should have next steps
        assert "Next Steps" in message or "next steps" in message
    
    def test_assessment_session_validation(self):
        """Test AssessmentSession validation and methods"""
        # Test valid assessment session
        assessment = AssessmentSession(
            user_id="test-user",
            skill_area="Python Programming"
        )
        
        assert assessment.user_id == "test-user"
        assert assessment.skill_area == "Python Programming"
        assert assessment.status == ConversationStatus.ACTIVE
        assert len(assessment.questions) == 0
        assert len(assessment.responses) == 0
        assert assessment.current_question_index == 0
        
        # Test adding questions
        assessment.add_question("What's your experience with Python?", question_type="open")
        assessment.add_question("Have you built any Python projects?", question_type="open")
        
        assert len(assessment.questions) == 2
        assert assessment.questions[0]["question"] == "What's your experience with Python?"
        assert assessment.questions[0]["type"] == "open"
        
        # Test adding responses
        assessment.add_response("I'm a beginner")
        assert len(assessment.responses) == 1
        assert assessment.current_question_index == 1
        assert not assessment.is_complete()
        
        assessment.add_response("No, I haven't built any projects yet")
        assert len(assessment.responses) == 2
        assert assessment.current_question_index == 2
        assert assessment.is_complete()  # All questions answered
        
        # Test progress calculation
        assessment.current_question_index = 1
        assert assessment.get_progress() == 0.5  # 1 out of 2 questions
        
        # Test completion
        results = {"overall_level": "beginner", "confidence": 0.6}
        assessment.complete_assessment(results)
        assert assessment.status == ConversationStatus.COMPLETED
        assert assessment.completed_at is not None
        assert assessment.assessment_results == results
    
    def test_assessment_session_validation_errors(self):
        """Test AssessmentSession validation errors"""
        # Test empty user ID
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            AssessmentSession(user_id="", skill_area="Python")
        
        # Test empty skill area
        with pytest.raises(ValueError, match="Skill area cannot be empty"):
            AssessmentSession(user_id="test-user", skill_area="")
        
        # Test invalid question
        assessment = AssessmentSession(user_id="test-user", skill_area="Python")
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            assessment.add_question("")
        
        # Test invalid response
        assessment.add_question("Test question?")
        
        with pytest.raises(ValueError, match="Response cannot be empty"):
            assessment.add_response("")


if __name__ == "__main__":
    pytest.main([__file__])