"""
Tests for interview preparation functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from edagent.models.interview import (
    InterviewQuestion, InterviewSession, InterviewFeedback, IndustryGuidance,
    InterviewType, DifficultyLevel, FeedbackType
)
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences
from edagent.services.interview_preparation import InterviewPreparationService
from edagent.services.ai_service import GeminiAIService


class TestInterviewModels:
    """Test interview data models"""
    
    def test_interview_question_creation(self):
        """Test creating an interview question"""
        question = InterviewQuestion(
            question="Tell me about yourself",
            question_type=InterviewType.BEHAVIORAL,
            difficulty=DifficultyLevel.BEGINNER,
            industry="Technology",
            role_level="entry",
            sample_answer="I am a software developer with 2 years of experience...",
            key_points=["Background", "Experience", "Goals"],
            follow_up_questions=["What interests you about this role?"],
            tags=["introduction", "behavioral"]
        )
        
        assert question.question == "Tell me about yourself"
        assert question.question_type == InterviewType.BEHAVIORAL
        assert question.difficulty == DifficultyLevel.BEGINNER
        assert question.industry == "Technology"
        assert len(question.key_points) == 3
        assert len(question.follow_up_questions) == 1
        assert "introduction" in question.tags
    
    def test_interview_question_validation(self):
        """Test interview question validation"""
        # Test empty question
        with pytest.raises(ValueError, match="Question cannot be empty"):
            InterviewQuestion(question="")
        
        # Test invalid question type
        with pytest.raises(ValueError):
            InterviewQuestion(
                question="Valid question",
                question_type="invalid_type"
            )
        
        # Test invalid difficulty
        with pytest.raises(ValueError):
            InterviewQuestion(
                question="Valid question",
                difficulty="invalid_difficulty"
            )
        
        # Test invalid role level
        with pytest.raises(ValueError):
            InterviewQuestion(
                question="Valid question",
                role_level="invalid_level"
            )
    
    def test_interview_question_serialization(self):
        """Test interview question serialization"""
        question = InterviewQuestion(
            question="Describe a challenging project",
            question_type=InterviewType.TECHNICAL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            key_points=["Technical complexity", "Problem solving", "Results"]
        )
        
        # Test to_dict
        data = question.to_dict()
        assert data["question"] == "Describe a challenging project"
        assert data["question_type"] == "technical"
        assert data["difficulty"] == "intermediate"
        assert len(data["key_points"]) == 3
        
        # Test from_dict
        restored = InterviewQuestion.from_dict(data)
        assert restored.question == question.question
        assert restored.question_type == question.question_type
        assert restored.difficulty == question.difficulty
        assert restored.key_points == question.key_points
    
    def test_interview_feedback_creation(self):
        """Test creating interview feedback"""
        feedback = InterviewFeedback(
            question_id="test-question-123",
            user_response="I worked on a challenging project where...",
            feedback_type=FeedbackType.IMPROVEMENT,
            feedback_text="Good start, but could use more specific examples",
            score=7.5,
            strengths=["Clear communication", "Relevant experience"],
            improvements=["Add specific metrics", "Structure using STAR method"],
            suggestions=["Practice with more examples", "Focus on results"]
        )
        
        assert feedback.question_id == "test-question-123"
        assert feedback.score == 7.5
        assert feedback.feedback_type == FeedbackType.IMPROVEMENT
        assert len(feedback.strengths) == 2
        assert len(feedback.improvements) == 2
        assert len(feedback.suggestions) == 2
    
    def test_interview_feedback_validation(self):
        """Test interview feedback validation"""
        # Test empty question ID
        with pytest.raises(ValueError, match="Question ID cannot be empty"):
            InterviewFeedback(question_id="")
        
        # Test invalid score
        with pytest.raises(ValueError, match="Score must be between 0.0 and 10.0"):
            InterviewFeedback(
                question_id="test-123",
                score=15.0
            )
        
        # Test invalid feedback type
        with pytest.raises(ValueError):
            InterviewFeedback(
                question_id="test-123",
                feedback_type="invalid_type"
            )
    
    def test_interview_session_creation(self):
        """Test creating an interview session"""
        session = InterviewSession(
            user_id="user-123",
            session_name="Software Developer Interview Practice",
            target_role="Software Developer",
            target_industry="Technology",
            session_type=InterviewType.TECHNICAL,
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        assert session.user_id == "user-123"
        assert session.target_role == "Software Developer"
        assert session.target_industry == "Technology"
        assert session.session_type == InterviewType.TECHNICAL
        assert session.difficulty_level == DifficultyLevel.INTERMEDIATE
        assert session.current_question_index == 0
        assert len(session.questions) == 0
        assert len(session.responses) == 0
    
    def test_interview_session_question_management(self):
        """Test adding and managing questions in a session"""
        session = InterviewSession(
            user_id="user-123",
            session_name="Test Session"
        )
        
        # Add questions
        question1 = InterviewQuestion(question="Question 1")
        question2 = InterviewQuestion(question="Question 2")
        
        session.add_question(question1)
        session.add_question(question2)
        
        assert len(session.questions) == 2
        assert session.get_current_question() == question1
        assert not session.is_complete()
        
        # Add responses
        session.add_response("Response to question 1")
        assert session.current_question_index == 1
        assert session.get_current_question() == question2
        
        session.add_response("Response to question 2")
        assert session.current_question_index == 2
        assert session.is_complete()
    
    def test_interview_session_completion(self):
        """Test completing an interview session"""
        session = InterviewSession(
            user_id="user-123",
            session_name="Test Session"
        )
        
        # Add questions and responses
        question = InterviewQuestion(question="Test question")
        session.add_question(question)
        session.add_response("Test response")
        
        # Add feedback
        feedback = InterviewFeedback(
            question_id=question.id,
            user_response="Test response",
            score=8.0,
            strengths=["Good example"],
            improvements=["Add more detail"]
        )
        session.add_feedback(feedback)
        
        # Complete session
        session.complete_session()
        
        assert session.completed_at is not None
        assert session.session_summary is not None
        assert session.session_summary["total_questions"] == 1
        assert session.session_summary["average_score"] == 8.0
    
    def test_industry_guidance_creation(self):
        """Test creating industry guidance"""
        guidance = IndustryGuidance(
            industry="Technology",
            common_questions=[
                "Describe your technical background",
                "How do you approach debugging?"
            ],
            key_skills=["Programming", "Problem solving", "Communication"],
            interview_format="Technical screening, coding challenge, system design",
            preparation_tips=[
                "Practice coding problems",
                "Review system design concepts"
            ],
            red_flags=["Lack of technical depth", "Poor communication"],
            success_factors=["Strong technical skills", "Clear communication"]
        )
        
        assert guidance.industry == "Technology"
        assert len(guidance.common_questions) == 2
        assert len(guidance.key_skills) == 3
        assert "Programming" in guidance.key_skills
        assert len(guidance.preparation_tips) == 2


class TestInterviewPreparationService:
    """Test interview preparation service"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service"""
        mock_service = Mock(spec=GeminiAIService)
        mock_service._make_api_call = AsyncMock()
        mock_service._get_model = Mock()
        mock_service._get_generation_config = Mock()
        return mock_service
    
    @pytest.fixture
    def interview_service(self, mock_ai_service):
        """Create interview preparation service with mock AI"""
        return InterviewPreparationService(ai_service=mock_ai_service)
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context"""
        return UserContext(
            user_id="test-user-123",
            current_skills={
                "python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7),
                "javascript": SkillLevel("javascript", SkillLevelEnum.BEGINNER, 0.4)
            },
            career_goals=["become a full-stack developer"],
            learning_preferences=UserPreferences(
                learning_style="visual",
                time_commitment="10 hours/week"
            )
        )
    
    @pytest.mark.asyncio
    async def test_create_interview_session(self, interview_service, mock_ai_service):
        """Test creating an interview session"""
        # Mock AI response for question generation
        mock_ai_service._make_api_call.return_value = '''
        {
            "questions": [
                {
                    "question": "Tell me about yourself",
                    "key_points": ["Background", "Experience", "Goals"],
                    "sample_answer": "I am a developer with...",
                    "follow_up_questions": ["What interests you about this role?"],
                    "tags": ["introduction"]
                },
                {
                    "question": "Describe a challenging project",
                    "key_points": ["Challenge", "Solution", "Result"],
                    "sample_answer": "I worked on a project where...",
                    "follow_up_questions": ["What would you do differently?"],
                    "tags": ["experience"]
                }
            ]
        }
        '''
        
        session = await interview_service.create_interview_session(
            user_id="test-user-123",
            target_role="Software Developer",
            target_industry="Technology",
            session_type=InterviewType.BEHAVIORAL,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            num_questions=2
        )
        
        assert session.user_id == "test-user-123"
        assert session.target_role == "Software Developer"
        assert session.target_industry == "Technology"
        assert session.session_type == InterviewType.BEHAVIORAL
        assert len(session.questions) == 2
        assert session.questions[0].question == "Tell me about yourself"
        assert session.questions[1].question == "Describe a challenging project"
    
    @pytest.mark.asyncio
    async def test_create_interview_session_fallback(self, interview_service, mock_ai_service):
        """Test creating interview session with AI failure (fallback questions)"""
        # Mock AI service to raise an exception
        mock_ai_service._make_api_call.side_effect = Exception("API Error")
        
        session = await interview_service.create_interview_session(
            user_id="test-user-123",
            target_role="Software Developer",
            target_industry="Technology",
            session_type=InterviewType.BEHAVIORAL,
            num_questions=3
        )
        
        assert session.user_id == "test-user-123"
        assert len(session.questions) == 3
        # Should have fallback questions
        assert all(q.question for q in session.questions)
        assert all("fallback" in q.tags for q in session.questions)
    
    @pytest.mark.asyncio
    async def test_provide_feedback(self, interview_service, mock_ai_service):
        """Test providing feedback for an interview response"""
        question = InterviewQuestion(
            question="Tell me about a time you faced a challenge",
            question_type=InterviewType.BEHAVIORAL,
            key_points=["Situation", "Challenge", "Action", "Result"]
        )
        
        user_response = "I was working on a project with a tight deadline..."
        
        # Mock AI response for feedback
        mock_ai_service._make_api_call.return_value = '''
        {
            "score": 7.5,
            "feedback_text": "Good response with clear structure",
            "strengths": ["Clear situation description", "Specific actions taken"],
            "improvements": ["Add more quantifiable results", "Elaborate on the challenge"],
            "suggestions": ["Use the STAR method more explicitly", "Include metrics"],
            "feedback_type": "improvement"
        }
        '''
        
        feedback = await interview_service.provide_feedback(question, user_response)
        
        assert feedback.question_id == question.id
        assert feedback.user_response == user_response
        assert feedback.score == 7.5
        assert feedback.feedback_type == FeedbackType.IMPROVEMENT
        assert len(feedback.strengths) == 2
        assert len(feedback.improvements) == 2
        assert len(feedback.suggestions) == 2
        assert "Clear situation description" in feedback.strengths
    
    @pytest.mark.asyncio
    async def test_provide_feedback_fallback(self, interview_service, mock_ai_service):
        """Test providing feedback with AI failure (fallback feedback)"""
        question = InterviewQuestion(question="Test question")
        user_response = "Test response"
        
        # Mock AI service to raise an exception
        mock_ai_service._make_api_call.side_effect = Exception("API Error")
        
        feedback = await interview_service.provide_feedback(question, user_response)
        
        assert feedback.question_id == question.id
        assert feedback.user_response == user_response
        assert feedback.score == 6.0  # Default fallback score
        assert feedback.feedback_type == FeedbackType.IMPROVEMENT
        assert len(feedback.improvements) > 0
        assert len(feedback.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_get_industry_guidance(self, interview_service, mock_ai_service):
        """Test getting industry-specific guidance"""
        # Mock AI response for industry guidance
        mock_ai_service._make_api_call.return_value = '''
        {
            "common_questions": [
                "Describe your technical background",
                "How do you approach problem-solving?",
                "Tell me about a technical challenge you faced"
            ],
            "key_skills": ["Programming", "Problem-solving", "Communication", "Teamwork"],
            "interview_format": "Phone screening, technical assessment, on-site interviews",
            "preparation_tips": [
                "Practice coding problems on LeetCode",
                "Review system design concepts",
                "Prepare behavioral examples"
            ],
            "red_flags": ["Lack of technical depth", "Poor communication skills"],
            "success_factors": ["Strong technical foundation", "Clear communication", "Cultural fit"]
        }
        '''
        
        guidance = await interview_service.get_industry_guidance("Technology")
        
        assert guidance.industry == "Technology"
        assert len(guidance.common_questions) == 3
        assert len(guidance.key_skills) == 4
        assert "Programming" in guidance.key_skills
        assert len(guidance.preparation_tips) == 3
        assert "Practice coding problems on LeetCode" in guidance.preparation_tips
        assert len(guidance.red_flags) == 2
        assert len(guidance.success_factors) == 3
    
    @pytest.mark.asyncio
    async def test_get_industry_guidance_caching(self, interview_service, mock_ai_service):
        """Test that industry guidance is cached"""
        # Mock AI response
        mock_ai_service._make_api_call.return_value = '''
        {
            "common_questions": ["Question 1"],
            "key_skills": ["Skill 1"],
            "interview_format": "Standard format",
            "preparation_tips": ["Tip 1"],
            "red_flags": ["Red flag 1"],
            "success_factors": ["Factor 1"]
        }
        '''
        
        # First call
        guidance1 = await interview_service.get_industry_guidance("Technology")
        
        # Second call should use cache
        guidance2 = await interview_service.get_industry_guidance("Technology")
        
        # AI service should only be called once
        assert mock_ai_service._make_api_call.call_count == 1
        assert guidance1.industry == guidance2.industry
        assert guidance1.common_questions == guidance2.common_questions
    
    @pytest.mark.asyncio
    async def test_generate_practice_questions(self, interview_service, mock_ai_service, sample_user_context):
        """Test generating practice questions based on user context"""
        # Mock AI responses for different question types
        mock_ai_service._make_api_call.return_value = '''
        {
            "questions": [
                {
                    "question": "Tell me about a time you had to learn a new technology quickly",
                    "key_points": ["Learning approach", "Timeline", "Results"],
                    "sample_answer": "When I needed to learn React for a project...",
                    "follow_up_questions": ["How do you stay updated with new technologies?"],
                    "tags": ["learning", "adaptability"]
                }
            ]
        }
        '''
        
        questions = await interview_service.generate_practice_questions(
            user_context=sample_user_context,
            target_role="Full Stack Developer",
            num_questions=3
        )
        
        assert len(questions) <= 3
        assert all(isinstance(q, InterviewQuestion) for q in questions)
        # Should have called AI service for both behavioral and technical questions
        assert mock_ai_service._make_api_call.call_count >= 1
    
    def test_determine_difficulty_from_context(self, interview_service, sample_user_context):
        """Test determining difficulty level from user context"""
        # Test with intermediate skills
        difficulty = interview_service._determine_difficulty_from_context(sample_user_context)
        assert difficulty == DifficultyLevel.INTERMEDIATE
        
        # Test with no skills (beginner)
        empty_context = UserContext(user_id="test", current_skills={})
        difficulty = interview_service._determine_difficulty_from_context(empty_context)
        assert difficulty == DifficultyLevel.BEGINNER
        
        # Test with advanced skills
        advanced_context = UserContext(
            user_id="test",
            current_skills={
                "python": SkillLevel("python", SkillLevelEnum.ADVANCED, 0.9),
                "javascript": SkillLevel("javascript", SkillLevelEnum.ADVANCED, 0.8),
                "react": SkillLevel("react", SkillLevelEnum.ADVANCED, 0.85)
            }
        )
        difficulty = interview_service._determine_difficulty_from_context(advanced_context)
        assert difficulty == DifficultyLevel.ADVANCED
    
    def test_infer_industry_from_context(self, interview_service, sample_user_context):
        """Test inferring industry from user context"""
        industry = interview_service._infer_industry_from_context(sample_user_context)
        assert industry == "Technology"
        
        # Test with healthcare goals
        healthcare_context = UserContext(
            user_id="test",
            career_goals=["become a nurse", "work in healthcare"]
        )
        industry = interview_service._infer_industry_from_context(healthcare_context)
        assert industry == "Healthcare"
        
        # Test with no clear industry (default)
        unclear_context = UserContext(
            user_id="test",
            career_goals=["get a better job"]
        )
        industry = interview_service._infer_industry_from_context(unclear_context)
        assert industry == "General"


class TestInterviewIntegration:
    """Integration tests for interview preparation"""
    
    @pytest.mark.asyncio
    async def test_complete_interview_workflow(self):
        """Test complete interview preparation workflow"""
        # Create service with mock AI
        mock_ai_service = Mock(spec=GeminiAIService)
        mock_ai_service._make_api_call = AsyncMock()
        mock_ai_service._get_model = Mock()
        mock_ai_service._get_generation_config = Mock()
        
        service = InterviewPreparationService(ai_service=mock_ai_service)
        
        # Mock question generation
        mock_ai_service._make_api_call.return_value = '''
        {
            "questions": [
                {
                    "question": "Why do you want to work here?",
                    "key_points": ["Company research", "Role alignment", "Career goals"],
                    "sample_answer": "I'm excited about this opportunity because...",
                    "follow_up_questions": ["What do you know about our products?"],
                    "tags": ["motivation", "company"]
                }
            ]
        }
        '''
        
        # 1. Create interview session
        session = await service.create_interview_session(
            user_id="test-user",
            target_role="Product Manager",
            target_industry="Technology",
            num_questions=1
        )
        
        assert len(session.questions) == 1
        question = session.questions[0]
        
        # 2. Simulate user response
        user_response = "I want to work here because I'm passionate about your mission..."
        session.add_response(user_response)
        
        # 3. Mock feedback generation
        mock_ai_service._make_api_call.return_value = '''
        {
            "score": 8.0,
            "feedback_text": "Strong response showing genuine interest",
            "strengths": ["Shows research", "Connects to personal values"],
            "improvements": ["Could mention specific products", "Add career growth aspect"],
            "suggestions": ["Research recent company news", "Practice with more examples"],
            "feedback_type": "positive"
        }
        '''
        
        # 4. Get feedback
        feedback = await service.provide_feedback(question, user_response)
        session.add_feedback(feedback)
        
        # 5. Complete session
        session.complete_session()
        
        assert session.is_complete()
        assert session.completed_at is not None
        assert session.session_summary is not None
        assert session.session_summary["average_score"] == 8.0
        assert len(session.feedback) == 1
        assert session.feedback[0].score == 8.0
    
    @pytest.mark.asyncio
    async def test_interview_session_persistence(self):
        """Test that interview session data can be serialized and restored"""
        # Create a complete session
        session = InterviewSession(
            user_id="test-user",
            session_name="Test Interview",
            target_role="Developer",
            target_industry="Tech"
        )
        
        # Add question and response
        question = InterviewQuestion(
            question="Describe your experience",
            key_points=["Background", "Skills", "Projects"]
        )
        session.add_question(question)
        session.add_response("I have 3 years of experience...")
        
        # Add feedback
        feedback = InterviewFeedback(
            question_id=question.id,
            user_response="I have 3 years of experience...",
            score=7.5,
            strengths=["Clear timeline"],
            improvements=["Add specific examples"]
        )
        session.add_feedback(feedback)
        session.complete_session()
        
        # Serialize to dict
        session_data = session.to_dict()
        
        # Restore from dict
        restored_session = InterviewSession.from_dict(session_data)
        
        assert restored_session.user_id == session.user_id
        assert restored_session.session_name == session.session_name
        assert len(restored_session.questions) == len(session.questions)
        assert len(restored_session.responses) == len(session.responses)
        assert len(restored_session.feedback) == len(session.feedback)
        assert restored_session.session_summary == session.session_summary
        assert restored_session.completed_at == session.completed_at


if __name__ == "__main__":
    pytest.main([__file__])