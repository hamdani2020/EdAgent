"""
Unit tests for ConversationManager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

from edagent.services.conversation_manager import ConversationManager, ConversationState
from edagent.models.conversation import (
    ConversationResponse, AssessmentSession, Message, MessageType, ConversationStatus
)
from edagent.models.learning import LearningPath, Milestone, DifficultyLevel
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum
from edagent.models.content import ContentRecommendation


class TestConversationState:
    """Test ConversationState class"""
    
    def test_conversation_state_initialization(self):
        """Test ConversationState initialization"""
        user_id = "test-user-123"
        state = ConversationState(user_id)
        
        assert state.user_id == user_id
        assert state.current_context is None
        assert state.active_assessment is None
        assert state.pending_learning_path is None
        assert isinstance(state.last_activity, datetime)
        assert state.message_count == 0
    
    def test_update_activity(self):
        """Test activity update"""
        state = ConversationState("test-user")
        initial_time = state.last_activity
        initial_count = state.message_count
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        
        state.update_activity()
        
        assert state.last_activity > initial_time
        assert state.message_count == initial_count + 1
    
    def test_is_in_assessment(self):
        """Test assessment state detection"""
        state = ConversationState("test-user")
        
        # No assessment
        assert not state.is_in_assessment()
        
        # Active assessment
        assessment = AssessmentSession(user_id="test-user", skill_area="Python")
        state.active_assessment = assessment
        assert state.is_in_assessment()
        
        # Completed assessment
        assessment.status = ConversationStatus.COMPLETED
        assert not state.is_in_assessment()
    
    def test_is_creating_learning_path(self):
        """Test learning path creation state"""
        state = ConversationState("test-user")
        
        assert not state.is_creating_learning_path()
        
        state.pending_learning_path = "become a developer"
        assert state.is_creating_learning_path()


class TestConversationManager:
    """Test ConversationManager class"""
    
    @pytest.fixture
    def conversation_manager(self):
        """Create ConversationManager instance with mocked dependencies"""
        with patch('edagent.services.conversation_manager.GeminiAIService') as mock_ai, \
             patch('edagent.services.conversation_manager.UserContextManager') as mock_ucm, \
             patch('edagent.services.conversation_manager.ContentRecommender') as mock_cr:
            
            manager = ConversationManager()
            manager.ai_service = mock_ai.return_value
            manager.user_context_manager = mock_ucm.return_value
            manager.content_recommender = mock_cr.return_value
            
            return manager
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context"""
        return UserContext(
            user_id="test-user-123",
            current_skills={
                "python": SkillLevel(
                    skill_name="python",
                    level=SkillLevelEnum.BEGINNER,
                    confidence_score=0.6,
                    last_updated=datetime.now()
                )
            },
            career_goals=["become a software developer"],
            created_at=datetime.now(),
            last_active=datetime.now()
        )
    
    def test_get_conversation_state(self, conversation_manager):
        """Test conversation state management"""
        user_id = "test-user-123"
        
        # First call creates new state
        state1 = conversation_manager._get_conversation_state(user_id)
        assert isinstance(state1, ConversationState)
        assert state1.user_id == user_id
        assert state1.message_count == 1
        
        # Second call returns same state
        state2 = conversation_manager._get_conversation_state(user_id)
        assert state2 is state1
        assert state2.message_count == 2
    
    def test_detect_intent_assessment(self, conversation_manager):
        """Test intent detection for assessment"""
        test_cases = [
            "Can you assess my skills?",
            "I want to test my programming knowledge",
            "How good am I at Python?",
            "Evaluate my skill level",
            "Check my skills in web development"
        ]
        
        for message in test_cases:
            intent = conversation_manager._detect_intent(message)
            assert intent == "assessment", f"Failed for message: {message}"
    
    def test_detect_intent_learning_path(self, conversation_manager):
        """Test intent detection for learning path"""
        test_cases = [
            "Create a learning path for me",
            "I want to become a data scientist",
            "Show me a roadmap for Python",
            "What's the study plan for machine learning?",
            "I need a career path in AI"
        ]
        
        for message in test_cases:
            intent = conversation_manager._detect_intent(message)
            assert intent == "learning_path", f"Failed for message: {message}"
    
    def test_detect_intent_content_recommendation(self, conversation_manager):
        """Test intent detection for content recommendation"""
        test_cases = [
            "Recommend some Python courses",
            "Find me tutorials on React",
            "Suggest resources for data science",
            "I need materials for learning JavaScript",
            "Show me videos about machine learning"
        ]
        
        for message in test_cases:
            intent = conversation_manager._detect_intent(message)
            assert intent == "content_recommendation", f"Failed for message: {message}"
    
    def test_detect_intent_general(self, conversation_manager):
        """Test intent detection for general conversation"""
        test_cases = [
            "Hello, how are you?",
            "What can you help me with?",
            "I'm feeling confused about my career",
            "Tell me about yourself",
            "I need some motivation"
        ]
        
        for message in test_cases:
            intent = conversation_manager._detect_intent(message)
            assert intent == "general", f"Failed for message: {message}"
    
    @pytest.mark.asyncio
    async def test_handle_message_general(self, conversation_manager, sample_user_context):
        """Test handling general conversation messages"""
        # Mock dependencies
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.ai_service.generate_response = AsyncMock(return_value="Hello! I'm here to help with your career goals.")
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        user_id = "test-user-123"
        message = "Hello, what can you help me with?"
        
        response = await conversation_manager.handle_message(user_id, message)
        
        assert isinstance(response, ConversationResponse)
        assert response.response_type == "text"
        assert "Hello!" in response.message
        assert response.confidence_score > 0.5
        
        # Verify AI service was called
        conversation_manager.ai_service.generate_response.assert_called_once_with(message, sample_user_context)
    
    @pytest.mark.asyncio
    async def test_handle_message_new_user(self, conversation_manager):
        """Test handling message from new user"""
        # Mock user context manager to return None first, then create new context
        new_user_context = UserContext(
            user_id="new-user-456",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=None)
        conversation_manager.user_context_manager.create_user_context = AsyncMock(return_value=new_user_context)
        conversation_manager.ai_service.generate_response = AsyncMock(return_value="Welcome! I'm EdAgent.")
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        user_id = "new-user-456"
        message = "Hi there!"
        
        response = await conversation_manager.handle_message(user_id, message)
        
        assert isinstance(response, ConversationResponse)
        conversation_manager.user_context_manager.create_user_context.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_start_skill_assessment(self, conversation_manager):
        """Test starting skill assessment"""
        user_id = "test-user-123"
        
        assessment = await conversation_manager.start_skill_assessment(user_id)
        
        assert isinstance(assessment, AssessmentSession)
        assert assessment.user_id == user_id
        assert assessment.skill_area == "General"
        assert assessment.status == ConversationStatus.ACTIVE
        assert len(assessment.questions) > 0
        
        # Check conversation state
        state = conversation_manager._conversation_states[user_id]
        assert state.active_assessment is assessment
        assert state.current_context == "assessment"
    
    @pytest.mark.asyncio
    async def test_generate_learning_path(self, conversation_manager, sample_user_context):
        """Test learning path generation"""
        # Mock dependencies
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.get_user_skills = AsyncMock(return_value=sample_user_context.current_skills)
        
        # Create mock learning path
        mock_learning_path = LearningPath(
            title="Python Developer Path",
            description="Comprehensive path to become a Python developer",
            goal="become a Python developer",
            milestones=[
                Milestone(
                    title="Learn Python Basics",
                    description="Master Python fundamentals",
                    order_index=0,
                    estimated_duration=timedelta(hours=40)
                )
            ],
            estimated_duration=timedelta(days=90),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Mock the enhanced learning path generator instead of AI service directly
        conversation_manager.learning_path_generator.create_comprehensive_learning_path = AsyncMock(return_value=mock_learning_path)
        conversation_manager.user_context_manager.create_learning_path = AsyncMock(return_value="path-123")
        
        user_id = "test-user-123"
        goal = "become a Python developer"
        
        result = await conversation_manager.generate_learning_path(user_id, goal)
        
        assert isinstance(result, LearningPath)
        assert result.title == "Python Developer Path"
        assert result.goal == goal
        assert len(result.milestones) == 1
        
        # Verify enhanced learning path generator was called with correct parameters
        conversation_manager.learning_path_generator.create_comprehensive_learning_path.assert_called_once_with(
            goal=goal,
            current_skills=sample_user_context.current_skills,
            user_context=sample_user_context
        )
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, conversation_manager):
        """Test retrieving conversation history"""
        # Mock conversation history data
        mock_history = [
            {
                "id": "msg-1",
                "content": "Hello",
                "message_type": "user",
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            },
            {
                "id": "msg-2", 
                "content": "Hi there!",
                "message_type": "assistant",
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            }
        ]
        
        conversation_manager.user_context_manager.get_conversation_history = AsyncMock(return_value=mock_history)
        
        user_id = "test-user-123"
        messages = await conversation_manager.get_conversation_history(user_id)
        
        assert len(messages) == 2
        assert all(isinstance(msg, Message) for msg in messages)
        assert messages[0].content == "Hello"
        assert messages[0].message_type == MessageType.USER
        assert messages[1].content == "Hi there!"
        assert messages[1].message_type == MessageType.ASSISTANT
    
    @pytest.mark.asyncio
    async def test_handle_assessment_flow(self, conversation_manager, sample_user_context):
        """Test complete assessment flow"""
        user_id = "test-user-123"
        
        # Mock dependencies
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.ai_service.generate_response = AsyncMock(return_value="Let's assess your skills!")
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        # Start assessment
        message = "Can you assess my Python skills?"
        response = await conversation_manager.handle_message(user_id, message)
        
        assert response.response_type == "assessment"
        assert "assess" in response.message.lower()
        
        # Check that assessment was started
        state = conversation_manager._conversation_states[user_id]
        assert state.is_in_assessment()
        assert state.active_assessment is not None
    
    @pytest.mark.asyncio
    async def test_handle_learning_path_flow(self, conversation_manager, sample_user_context):
        """Test learning path creation flow"""
        user_id = "test-user-123"
        
        # Mock dependencies
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        conversation_manager.user_context_manager.get_user_skills = AsyncMock(return_value=sample_user_context.current_skills)
        
        # Create mock learning path
        mock_learning_path = LearningPath(
            title="Web Developer Path",
            goal="become a web developer",
            milestones=[
                Milestone(title="HTML/CSS Basics", description="Learn web fundamentals", order_index=0, estimated_duration=timedelta(hours=30)),
                Milestone(title="JavaScript Fundamentals", description="Learn JS basics", order_index=1, estimated_duration=timedelta(hours=40))
            ],
            estimated_duration=timedelta(days=120),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        conversation_manager.ai_service.create_learning_path = AsyncMock(return_value=mock_learning_path)
        conversation_manager.user_context_manager.create_learning_path = AsyncMock(return_value="path-456")
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        # Test learning path request
        message = "I want to become a web developer"
        response = await conversation_manager.handle_message(user_id, message)
        
        assert response.response_type == "learning_path"
        assert "Web Developer Path" in response.message
        assert len(response.suggested_actions) > 0
    
    @pytest.mark.asyncio
    async def test_handle_content_request(self, conversation_manager, sample_user_context):
        """Test content recommendation flow"""
        user_id = "test-user-123"
        
        # Mock dependencies
        conversation_manager.user_context_manager.get_user_context = AsyncMock(return_value=sample_user_context)
        
        # Create mock content recommendations
        mock_recommendations = [
            ContentRecommendation(
                title="Python for Beginners",
                url="https://example.com/python-course",
                platform="YouTube",
                content_type="video",
                rating=4.5,
                is_free=True,
                skill_match_score=0.9
            )
        ]
        
        conversation_manager.content_recommender.get_recommendations = AsyncMock(return_value=mock_recommendations)
        conversation_manager.user_context_manager.add_conversation = AsyncMock()
        
        # Test content request
        message = "Recommend Python tutorials for beginners"
        response = await conversation_manager.handle_message(user_id, message)
        
        assert response.response_type == "content_recommendation"
        assert "Python for Beginners" in response.message
        assert len(response.content_recommendations) == 1
    
    def test_extract_learning_goal(self, conversation_manager):
        """Test learning goal extraction"""
        test_cases = [
            ("I want to become a data scientist", "data scientist"),
            ("Learn to be a web developer", "web developer"),
            ("I want a career in machine learning", "machine learning"),
            ("How do I become an AI engineer?", None),  # Question format
            ("Study Python programming", "Python programming"),
            ("Learn", None)  # Too short
        ]
        
        for message, expected in test_cases:
            result = conversation_manager._extract_learning_goal(message)
            if expected:
                # Allow for some flexibility in goal extraction
                assert expected.lower() in result.lower() if result else False, f"Failed for message: {message}, got: {result}"
            else:
                assert result is None, f"Failed for message: {message}"
    
    def test_extract_content_topic(self, conversation_manager):
        """Test content topic extraction"""
        test_cases = [
            ("Recommend Python courses", "python"),
            ("Find tutorials about React", "react"),
            ("Show me resources for machine learning", "machine learning"),
            ("Suggest videos on data science", "data science"),
            ("Help me find material about JavaScript", "javascript"),
            ("Find", None)  # Too short
        ]
        
        for message, expected in test_cases:
            result = conversation_manager._extract_content_topic(message)
            if expected:
                assert expected.lower() in result.lower(), f"Failed for message: {message}"
            else:
                assert result is None, f"Failed for message: {message}"
    
    def test_format_learning_path_summary(self, conversation_manager):
        """Test learning path formatting"""
        learning_path = LearningPath(
            title="Python Developer Path",
            goal="become a Python developer",
            milestones=[
                Milestone(title="Python Basics", description="Learn Python fundamentals and syntax", order_index=0, estimated_duration=timedelta(hours=40)),
                Milestone(title="Web Frameworks", description="Learn Flask and Django for web development", order_index=1, estimated_duration=timedelta(hours=60)),
                Milestone(title="Database Integration", description="Learn to work with databases", order_index=2, estimated_duration=timedelta(hours=30))
            ],
            estimated_duration=timedelta(days=90),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        summary = conversation_manager._format_learning_path_summary(learning_path)
        
        assert "Python Developer Path" in summary
        assert "Difficulty: beginner" in summary
        assert "90 days" in summary
        assert "Python Basics" in summary
        assert "Web Frameworks" in summary
        assert "Database Integration" in summary
    
    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_manager):
        """Test error handling in message processing"""
        # Mock dependencies to raise exceptions
        conversation_manager.user_context_manager.get_user_context = AsyncMock(side_effect=Exception("Database error"))
        
        user_id = "test-user-123"
        message = "Hello"
        
        response = await conversation_manager.handle_message(user_id, message)
        
        assert isinstance(response, ConversationResponse)
        assert response.confidence_score <= 0.5
        assert "trouble" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_conversation_state_cleanup(self, conversation_manager):
        """Test that conversation states are properly managed"""
        user_id = "test-user-123"
        
        # Create conversation state
        state = conversation_manager._get_conversation_state(user_id)
        assert user_id in conversation_manager._conversation_states
        
        # Simulate assessment flow
        assessment = AssessmentSession(user_id=user_id, skill_area="Python")
        state.active_assessment = assessment
        state.current_context = "assessment"
        
        assert state.is_in_assessment()
        
        # Complete assessment (would happen in real flow)
        assessment.status = ConversationStatus.COMPLETED
        state.active_assessment = None
        state.current_context = None
        
        assert not state.is_in_assessment()


if __name__ == "__main__":
    pytest.main([__file__])