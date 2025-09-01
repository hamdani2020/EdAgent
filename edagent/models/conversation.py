"""
Conversation and messaging models for EdAgent
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any, Union
from enum import Enum
import json
import uuid


class MessageType(str, Enum):
    """Enumeration for message types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ASSESSMENT = "assessment"
    LEARNING_PATH = "learning_path"


class ConversationStatus(str, Enum):
    """Enumeration for conversation status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Message:
    """Represents a single message in a conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    message_type: MessageType = MessageType.USER
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate message data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate message data"""
        if not self.id or not self.id.strip():
            raise ValueError("Message ID cannot be empty")
        
        if not isinstance(self.content, str):
            raise ValueError("Message content must be a string")
        
        if not isinstance(self.message_type, MessageType):
            if isinstance(self.message_type, str):
                try:
                    self.message_type = MessageType(self.message_type.lower())
                except ValueError:
                    raise ValueError(f"Invalid message type: {self.message_type}")
            else:
                raise ValueError("Message type must be a MessageType or valid string")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create Message from dictionary"""
        return cls(
            id=data["id"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationResponse:
    """Represents a response from the AI agent"""
    message: str
    response_type: Literal["text", "assessment", "learning_path", "content_recommendation"] = "text"
    confidence_score: float = 1.0
    suggested_actions: List[str] = field(default_factory=list)
    content_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate response data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate conversation response data"""
        if not isinstance(self.message, str):
            raise ValueError("Response message must be a string")
        
        if self.response_type not in ["text", "assessment", "learning_path", "content_recommendation"]:
            raise ValueError("Invalid response type")
        
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if not isinstance(self.suggested_actions, list):
            raise ValueError("Suggested actions must be a list")
        
        if not isinstance(self.content_recommendations, list):
            raise ValueError("Content recommendations must be a list")
        
        if not isinstance(self.follow_up_questions, list):
            raise ValueError("Follow up questions must be a list")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
    
    def add_content_recommendation(self, recommendation: Dict[str, Any]) -> None:
        """Add a content recommendation to the response"""
        if not isinstance(recommendation, dict):
            raise ValueError("Recommendation must be a dictionary")
        self.content_recommendations.append(recommendation)
    
    def add_follow_up_question(self, question: str) -> None:
        """Add a follow-up question to the response"""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")
        self.follow_up_questions.append(question)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "message": self.message,
            "response_type": self.response_type,
            "confidence_score": self.confidence_score,
            "suggested_actions": self.suggested_actions,
            "content_recommendations": self.content_recommendations,
            "follow_up_questions": self.follow_up_questions,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationResponse':
        """Create ConversationResponse from dictionary"""
        return cls(
            message=data["message"],
            response_type=data.get("response_type", "text"),
            confidence_score=data.get("confidence_score", 1.0),
            suggested_actions=data.get("suggested_actions", []),
            content_recommendations=data.get("content_recommendations", []),
            follow_up_questions=data.get("follow_up_questions", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class AssessmentSession:
    """Represents a skill assessment session"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    skill_area: str = ""
    questions: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    current_question_index: int = 0
    status: ConversationStatus = ConversationStatus.ACTIVE
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    assessment_results: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate assessment session data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate assessment session data"""
        if not self.id or not self.id.strip():
            raise ValueError("Assessment session ID cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.skill_area or not self.skill_area.strip():
            raise ValueError("Skill area cannot be empty")
        
        if not isinstance(self.questions, list):
            raise ValueError("Questions must be a list")
        
        if not isinstance(self.responses, list):
            raise ValueError("Responses must be a list")
        
        if not isinstance(self.current_question_index, int) or self.current_question_index < 0:
            raise ValueError("Current question index must be a non-negative integer")
        
        if not isinstance(self.status, ConversationStatus):
            if isinstance(self.status, str):
                try:
                    self.status = ConversationStatus(self.status.lower())
                except ValueError:
                    raise ValueError(f"Invalid conversation status: {self.status}")
            else:
                raise ValueError("Status must be a ConversationStatus or valid string")
        
        if not isinstance(self.started_at, datetime):
            raise ValueError("Started at must be a datetime object")
        
        if self.completed_at is not None and not isinstance(self.completed_at, datetime):
            raise ValueError("Completed at must be a datetime object or None")
    
    def add_question(self, question: str, options: Optional[List[str]] = None, 
                    question_type: str = "open") -> None:
        """Add a question to the assessment"""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        question_data = {
            "question": question,
            "type": question_type,
            "options": options or [],
            "index": len(self.questions)
        }
        self.questions.append(question_data)
    
    def add_response(self, response: str, question_index: Optional[int] = None) -> None:
        """Add a response to the assessment"""
        if not response or not response.strip():
            raise ValueError("Response cannot be empty")
        
        if question_index is None:
            question_index = self.current_question_index
        
        if question_index >= len(self.questions):
            raise ValueError("Question index out of range")
        
        response_data = {
            "question_index": question_index,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        self.responses.append(response_data)
        
        # Move to next question
        if question_index == self.current_question_index:
            self.current_question_index += 1
    
    def is_complete(self) -> bool:
        """Check if the assessment is complete"""
        return (self.current_question_index >= len(self.questions) or 
                self.status == ConversationStatus.COMPLETED)
    
    def complete_assessment(self, results: Dict[str, Any]) -> None:
        """Mark the assessment as complete with results"""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now()
        self.assessment_results = results
    
    def get_progress(self) -> float:
        """Get assessment progress as a percentage"""
        if not self.questions:
            return 0.0
        return min(self.current_question_index / len(self.questions), 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_area": self.skill_area,
            "questions": self.questions,
            "responses": self.responses,
            "current_question_index": self.current_question_index,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assessment_results": self.assessment_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssessmentSession':
        """Create AssessmentSession from dictionary"""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            skill_area=data["skill_area"],
            questions=data.get("questions", []),
            responses=data.get("responses", []),
            current_question_index=data.get("current_question_index", 0),
            status=ConversationStatus(data.get("status", "active")),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            assessment_results=data.get("assessment_results")
        )