"""
Unit tests for conversation and messaging models
"""

import pytest
import json
from datetime import datetime, timedelta
from edagent.models.conversation import (
    Message, 
    ConversationResponse, 
    AssessmentSession,
    MessageType,
    ConversationStatus
)


class TestMessage:
    """Test cases for Message model"""
    
    def test_valid_message_creation(self):
        """Test creating a valid message"""
        message = Message(
            content="Hello, I want to learn Python",
            message_type=MessageType.USER
        )
        
        assert message.content == "Hello, I want to learn Python"
        assert message.message_type == MessageType.USER
        assert isinstance(message.id, str)
        assert len(message.id) > 0
        assert isinstance(message.timestamp, datetime)
        assert message.metadata == {}
    
    def test_message_with_string_enum(self):
        """Test creating message with string enum value"""
        message = Message(
            content="Here's my response",
            message_type="assistant"
        )
        
        assert message.message_type == MessageType.ASSISTANT
    
    def test_invalid_message_type(self):
        """Test validation with invalid message type"""
        with pytest.raises(ValueError, match="Invalid message type"):
            Message(
                content="Test message",
                message_type="invalid_type"
            )
    
    def test_message_with_metadata(self):
        """Test message with metadata"""
        metadata = {"skill_area": "python", "confidence": 0.8}
        message = Message(
            content="I'm confident in Python basics",
            message_type=MessageType.USER,
            metadata=metadata
        )
        
        assert message.metadata == metadata
    
    def test_message_serialization(self):
        """Test serialization to dictionary"""
        now = datetime.now()
        message = Message(
            id="test-123",
            content="Test content",
            message_type=MessageType.SYSTEM,
            timestamp=now,
            metadata={"test": "value"}
        )
        
        data = message.to_dict()
        expected = {
            "id": "test-123",
            "content": "Test content",
            "message_type": "system",
            "timestamp": now.isoformat(),
            "metadata": {"test": "value"}
        }
        
        assert data == expected
    
    def test_message_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        data = {
            "id": "test-456",
            "content": "Deserialized message",
            "message_type": "assessment",
            "timestamp": now.isoformat(),
            "metadata": {"category": "skill_check"}
        }
        
        message = Message.from_dict(data)
        
        assert message.id == "test-456"
        assert message.content == "Deserialized message"
        assert message.message_type == MessageType.ASSESSMENT
        assert message.timestamp == now
        assert message.metadata == {"category": "skill_check"}


class TestConversationResponse:
    """Test cases for ConversationResponse model"""
    
    def test_valid_response_creation(self):
        """Test creating a valid conversation response"""
        response = ConversationResponse(
            message="Great! Let's start with Python basics.",
            response_type="text",
            confidence_score=0.9
        )
        
        assert response.message == "Great! Let's start with Python basics."
        assert response.response_type == "text"
        assert response.confidence_score == 0.9
        assert response.suggested_actions == []
        assert response.content_recommendations == []
        assert response.follow_up_questions == []
        assert response.metadata == {}
    
    def test_invalid_response_type(self):
        """Test validation with invalid response type"""
        with pytest.raises(ValueError, match="Invalid response type"):
            ConversationResponse(
                message="Test response",
                response_type="invalid_type"
            )
    
    def test_invalid_confidence_score(self):
        """Test validation with invalid confidence score"""
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            ConversationResponse(
                message="Test response",
                confidence_score=1.5
            )
    
    def test_add_content_recommendation(self):
        """Test adding content recommendation"""
        response = ConversationResponse(message="Here are some resources:")
        
        recommendation = {
            "title": "Python Tutorial",
            "url": "https://example.com/python",
            "type": "video"
        }
        
        response.add_content_recommendation(recommendation)
        
        assert len(response.content_recommendations) == 1
        assert response.content_recommendations[0] == recommendation
    
    def test_add_follow_up_question(self):
        """Test adding follow-up question"""
        response = ConversationResponse(message="I can help with that.")
        
        response.add_follow_up_question("What specific area would you like to focus on?")
        
        assert len(response.follow_up_questions) == 1
        assert response.follow_up_questions[0] == "What specific area would you like to focus on?"
    
    def test_invalid_follow_up_question(self):
        """Test validation with invalid follow-up question"""
        response = ConversationResponse(message="Test")
        
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            response.add_follow_up_question("")
    
    def test_response_serialization(self):
        """Test serialization to dictionary"""
        response = ConversationResponse(
            message="Let's assess your skills",
            response_type="assessment",
            confidence_score=0.85,
            suggested_actions=["take_assessment"],
            follow_up_questions=["What's your experience level?"]
        )
        
        data = response.to_dict()
        
        assert data["message"] == "Let's assess your skills"
        assert data["response_type"] == "assessment"
        assert data["confidence_score"] == 0.85
        assert data["suggested_actions"] == ["take_assessment"]
        assert data["follow_up_questions"] == ["What's your experience level?"]
    
    def test_response_deserialization(self):
        """Test deserialization from dictionary"""
        data = {
            "message": "Here's your learning path",
            "response_type": "learning_path",
            "confidence_score": 0.95,
            "suggested_actions": ["start_learning"],
            "content_recommendations": [{"title": "Course 1"}],
            "follow_up_questions": ["Ready to start?"],
            "metadata": {"path_id": "123"}
        }
        
        response = ConversationResponse.from_dict(data)
        
        assert response.message == "Here's your learning path"
        assert response.response_type == "learning_path"
        assert response.confidence_score == 0.95
        assert response.suggested_actions == ["start_learning"]
        assert response.content_recommendations == [{"title": "Course 1"}]
        assert response.follow_up_questions == ["Ready to start?"]
        assert response.metadata == {"path_id": "123"}


class TestAssessmentSession:
    """Test cases for AssessmentSession model"""
    
    def test_valid_assessment_creation(self):
        """Test creating a valid assessment session"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="Python Programming"
        )
        
        assert assessment.user_id == "user123"
        assert assessment.skill_area == "Python Programming"
        assert isinstance(assessment.id, str)
        assert len(assessment.id) > 0
        assert assessment.questions == []
        assert assessment.responses == []
        assert assessment.current_question_index == 0
        assert assessment.status == ConversationStatus.ACTIVE
        assert isinstance(assessment.started_at, datetime)
        assert assessment.completed_at is None
        assert assessment.assessment_results is None
    
    def test_invalid_user_id(self):
        """Test validation with invalid user ID"""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            AssessmentSession(
                user_id="",
                skill_area="Python"
            )
    
    def test_invalid_skill_area(self):
        """Test validation with invalid skill area"""
        with pytest.raises(ValueError, match="Skill area cannot be empty"):
            AssessmentSession(
                user_id="user123",
                skill_area=""
            )
    
    def test_add_question(self):
        """Test adding a question to assessment"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="JavaScript"
        )
        
        assessment.add_question(
            "What is a closure in JavaScript?",
            options=["A function", "A variable", "A loop", "An object"],
            question_type="multiple_choice"
        )
        
        assert len(assessment.questions) == 1
        question = assessment.questions[0]
        assert question["question"] == "What is a closure in JavaScript?"
        assert question["type"] == "multiple_choice"
        assert question["options"] == ["A function", "A variable", "A loop", "An object"]
        assert question["index"] == 0
    
    def test_add_response(self):
        """Test adding a response to assessment"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="Python"
        )
        
        assessment.add_question("What is Python?")
        assessment.add_response("Python is a programming language")
        
        assert len(assessment.responses) == 1
        response = assessment.responses[0]
        assert response["question_index"] == 0
        assert response["response"] == "Python is a programming language"
        assert "timestamp" in response
        assert assessment.current_question_index == 1
    
    def test_invalid_response(self):
        """Test validation with invalid response"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="Python"
        )
        
        with pytest.raises(ValueError, match="Response cannot be empty"):
            assessment.add_response("")
    
    def test_is_complete(self):
        """Test assessment completion check"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="Python"
        )
        
        # Empty assessment is complete
        assert assessment.is_complete()
        
        # Add questions
        assessment.add_question("Question 1")
        assessment.add_question("Question 2")
        
        # Not complete yet
        assert not assessment.is_complete()
        
        # Answer questions
        assessment.add_response("Answer 1")
        assessment.add_response("Answer 2")
        
        # Now complete
        assert assessment.is_complete()
    
    def test_complete_assessment(self):
        """Test completing assessment with results"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="Python"
        )
        
        results = {
            "overall_score": 0.8,
            "level": "intermediate",
            "strengths": ["syntax", "data structures"],
            "weaknesses": ["algorithms"]
        }
        
        assessment.complete_assessment(results)
        
        assert assessment.status == ConversationStatus.COMPLETED
        assert assessment.completed_at is not None
        assert assessment.assessment_results == results
    
    def test_get_progress(self):
        """Test getting assessment progress"""
        assessment = AssessmentSession(
            user_id="user123",
            skill_area="Python"
        )
        
        # No questions = 0% progress
        assert assessment.get_progress() == 0.0
        
        # Add 3 questions
        for i in range(3):
            assessment.add_question(f"Question {i+1}")
        
        # No answers yet = 0% progress
        assert assessment.get_progress() == 0.0
        
        # Answer 1 question = 33% progress
        assessment.add_response("Answer 1")
        assert abs(assessment.get_progress() - 0.333) < 0.01
        
        # Answer all questions = 100% progress
        assessment.add_response("Answer 2")
        assessment.add_response("Answer 3")
        assert assessment.get_progress() == 1.0
    
    def test_assessment_serialization(self):
        """Test serialization to dictionary"""
        now = datetime.now()
        assessment = AssessmentSession(
            id="assess-123",
            user_id="user456",
            skill_area="Data Science",
            started_at=now
        )
        
        assessment.add_question("What is machine learning?")
        assessment.add_response("ML is a subset of AI")
        
        data = assessment.to_dict()
        
        assert data["id"] == "assess-123"
        assert data["user_id"] == "user456"
        assert data["skill_area"] == "Data Science"
        assert data["status"] == "active"
        assert data["started_at"] == now.isoformat()
        assert data["completed_at"] is None
        assert len(data["questions"]) == 1
        assert len(data["responses"]) == 1
    
    def test_assessment_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        completed_time = now + timedelta(minutes=30)
        
        data = {
            "id": "assess-789",
            "user_id": "user789",
            "skill_area": "Web Development",
            "questions": [{"question": "What is HTML?", "type": "open", "options": [], "index": 0}],
            "responses": [{"question_index": 0, "response": "Markup language", "timestamp": now.isoformat()}],
            "current_question_index": 1,
            "status": "completed",
            "started_at": now.isoformat(),
            "completed_at": completed_time.isoformat(),
            "assessment_results": {"score": 0.9}
        }
        
        assessment = AssessmentSession.from_dict(data)
        
        assert assessment.id == "assess-789"
        assert assessment.user_id == "user789"
        assert assessment.skill_area == "Web Development"
        assert assessment.status == ConversationStatus.COMPLETED
        assert assessment.started_at == now
        assert assessment.completed_at == completed_time
        assert assessment.assessment_results == {"score": 0.9}
        assert len(assessment.questions) == 1
        assert len(assessment.responses) == 1


if __name__ == "__main__":
    pytest.main([__file__])