"""
Interview preparation models for EdAgent
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any
from enum import Enum
import json
import uuid


class InterviewType(str, Enum):
    """Enumeration for interview types"""
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CASE_STUDY = "case_study"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"
    GENERAL = "general"


class DifficultyLevel(str, Enum):
    """Enumeration for question difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class FeedbackType(str, Enum):
    """Enumeration for feedback types"""
    POSITIVE = "positive"
    IMPROVEMENT = "improvement"
    SUGGESTION = "suggestion"
    WARNING = "warning"


@dataclass
class InterviewQuestion:
    """Represents an interview question"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    question_type: InterviewType = InterviewType.GENERAL
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    industry: str = ""
    role_level: str = ""  # entry, mid, senior, executive
    sample_answer: str = ""
    key_points: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate interview question data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate interview question data"""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        
        if not isinstance(self.question_type, InterviewType):
            if isinstance(self.question_type, str):
                try:
                    self.question_type = InterviewType(self.question_type.lower())
                except ValueError:
                    raise ValueError(f"Invalid question type: {self.question_type}")
            else:
                raise ValueError("Question type must be an InterviewType or valid string")
        
        if not isinstance(self.difficulty, DifficultyLevel):
            if isinstance(self.difficulty, str):
                try:
                    self.difficulty = DifficultyLevel(self.difficulty.lower())
                except ValueError:
                    raise ValueError(f"Invalid difficulty level: {self.difficulty}")
            else:
                raise ValueError("Difficulty must be a DifficultyLevel or valid string")
        
        if self.role_level and self.role_level not in ["entry", "mid", "senior", "executive"]:
            raise ValueError("Role level must be 'entry', 'mid', 'senior', or 'executive'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "question": self.question,
            "question_type": self.question_type.value,
            "difficulty": self.difficulty.value,
            "industry": self.industry,
            "role_level": self.role_level,
            "sample_answer": self.sample_answer,
            "key_points": self.key_points,
            "follow_up_questions": self.follow_up_questions,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterviewQuestion':
        """Create InterviewQuestion from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            question=data["question"],
            question_type=InterviewType(data.get("question_type", "general")),
            difficulty=DifficultyLevel(data.get("difficulty", "intermediate")),
            industry=data.get("industry", ""),
            role_level=data.get("role_level", ""),
            sample_answer=data.get("sample_answer", ""),
            key_points=data.get("key_points", []),
            follow_up_questions=data.get("follow_up_questions", []),
            tags=data.get("tags", [])
        )


@dataclass
class InterviewFeedback:
    """Represents feedback for an interview response"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    user_response: str = ""
    feedback_type: FeedbackType = FeedbackType.IMPROVEMENT
    feedback_text: str = ""
    score: float = 0.0  # 0.0 to 10.0
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate interview feedback data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate interview feedback data"""
        if not self.question_id or not self.question_id.strip():
            raise ValueError("Question ID cannot be empty")
        
        if not isinstance(self.user_response, str):
            raise ValueError("User response must be a string")
        
        if not isinstance(self.feedback_type, FeedbackType):
            if isinstance(self.feedback_type, str):
                try:
                    self.feedback_type = FeedbackType(self.feedback_type.lower())
                except ValueError:
                    raise ValueError(f"Invalid feedback type: {self.feedback_type}")
            else:
                raise ValueError("Feedback type must be a FeedbackType or valid string")
        
        if not 0.0 <= self.score <= 10.0:
            raise ValueError("Score must be between 0.0 and 10.0")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "user_response": self.user_response,
            "feedback_type": self.feedback_type.value,
            "feedback_text": self.feedback_text,
            "score": self.score,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterviewFeedback':
        """Create InterviewFeedback from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            question_id=data["question_id"],
            user_response=data.get("user_response", ""),
            feedback_type=FeedbackType(data.get("feedback_type", "improvement")),
            feedback_text=data.get("feedback_text", ""),
            score=data.get("score", 0.0),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
            suggestions=data.get("suggestions", []),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        )


@dataclass
class InterviewSession:
    """Represents an interview practice session"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    session_name: str = ""
    target_role: str = ""
    target_industry: str = ""
    session_type: InterviewType = InterviewType.GENERAL
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    questions: List[InterviewQuestion] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    feedback: List[InterviewFeedback] = field(default_factory=list)
    current_question_index: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    session_summary: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate interview session data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate interview session data"""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.session_name or not self.session_name.strip():
            raise ValueError("Session name cannot be empty")
        
        if not isinstance(self.session_type, InterviewType):
            if isinstance(self.session_type, str):
                try:
                    self.session_type = InterviewType(self.session_type.lower())
                except ValueError:
                    raise ValueError(f"Invalid session type: {self.session_type}")
            else:
                raise ValueError("Session type must be an InterviewType or valid string")
        
        if not isinstance(self.difficulty_level, DifficultyLevel):
            if isinstance(self.difficulty_level, str):
                try:
                    self.difficulty_level = DifficultyLevel(self.difficulty_level.lower())
                except ValueError:
                    raise ValueError(f"Invalid difficulty level: {self.difficulty_level}")
            else:
                raise ValueError("Difficulty level must be a DifficultyLevel or valid string")
        
        if not isinstance(self.current_question_index, int) or self.current_question_index < 0:
            raise ValueError("Current question index must be a non-negative integer")
        
        if not isinstance(self.started_at, datetime):
            raise ValueError("Started at must be a datetime object")
        
        if self.completed_at is not None and not isinstance(self.completed_at, datetime):
            raise ValueError("Completed at must be a datetime object or None")
    
    def add_question(self, question: InterviewQuestion) -> None:
        """Add a question to the session"""
        if not isinstance(question, InterviewQuestion):
            raise ValueError("Question must be an InterviewQuestion object")
        question.validate()
        self.questions.append(question)
    
    def add_response(self, response: str, question_index: Optional[int] = None) -> None:
        """Add a response to the current question"""
        if not response or not response.strip():
            raise ValueError("Response cannot be empty")
        
        if question_index is None:
            question_index = self.current_question_index
        
        if question_index >= len(self.questions):
            raise ValueError("Question index out of range")
        
        response_data = {
            "question_index": question_index,
            "question_id": self.questions[question_index].id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        self.responses.append(response_data)
        
        # Move to next question
        if question_index == self.current_question_index:
            self.current_question_index += 1
    
    def add_feedback(self, feedback: InterviewFeedback) -> None:
        """Add feedback for a response"""
        if not isinstance(feedback, InterviewFeedback):
            raise ValueError("Feedback must be an InterviewFeedback object")
        feedback.validate()
        self.feedback.append(feedback)
    
    def get_current_question(self) -> Optional[InterviewQuestion]:
        """Get the current question"""
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def is_complete(self) -> bool:
        """Check if the session is complete"""
        return self.current_question_index >= len(self.questions)
    
    def complete_session(self) -> None:
        """Mark the session as complete and generate summary"""
        if not self.is_complete():
            raise ValueError("Cannot complete session with unanswered questions")
        
        self.completed_at = datetime.now()
        self.session_summary = self._generate_session_summary()
    
    def _generate_session_summary(self) -> Dict[str, Any]:
        """Generate a summary of the session performance"""
        if not self.feedback:
            return {"message": "No feedback available for summary"}
        
        # Calculate average score
        scores = [f.score for f in self.feedback if f.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Collect all strengths and improvements
        all_strengths = []
        all_improvements = []
        for feedback in self.feedback:
            all_strengths.extend(feedback.strengths)
            all_improvements.extend(feedback.improvements)
        
        # Count question types
        question_types = {}
        for question in self.questions:
            question_types[question.question_type.value] = question_types.get(question.question_type.value, 0) + 1
        
        return {
            "total_questions": len(self.questions),
            "average_score": round(avg_score, 1),
            "question_types": question_types,
            "top_strengths": list(set(all_strengths))[:5],
            "key_improvements": list(set(all_improvements))[:5],
            "session_duration": str(self.completed_at - self.started_at) if self.completed_at else None,
            "completion_date": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_progress(self) -> float:
        """Get session progress as a percentage"""
        if not self.questions:
            return 0.0
        return min(self.current_question_index / len(self.questions), 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_name": self.session_name,
            "target_role": self.target_role,
            "target_industry": self.target_industry,
            "session_type": self.session_type.value,
            "difficulty_level": self.difficulty_level.value,
            "questions": [q.to_dict() for q in self.questions],
            "responses": self.responses,
            "feedback": [f.to_dict() for f in self.feedback],
            "current_question_index": self.current_question_index,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "session_summary": self.session_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterviewSession':
        """Create InterviewSession from dictionary"""
        session = cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data["user_id"],
            session_name=data.get("session_name", ""),
            target_role=data.get("target_role", ""),
            target_industry=data.get("target_industry", ""),
            session_type=InterviewType(data.get("session_type", "general")),
            difficulty_level=DifficultyLevel(data.get("difficulty_level", "intermediate")),
            current_question_index=data.get("current_question_index", 0),
            started_at=datetime.fromisoformat(data.get("started_at", datetime.now().isoformat())),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            session_summary=data.get("session_summary")
        )
        
        # Add questions
        for q_data in data.get("questions", []):
            session.questions.append(InterviewQuestion.from_dict(q_data))
        
        # Add responses
        session.responses = data.get("responses", [])
        
        # Add feedback
        for f_data in data.get("feedback", []):
            session.feedback.append(InterviewFeedback.from_dict(f_data))
        
        return session


@dataclass
class IndustryGuidance:
    """Represents industry-specific interview guidance"""
    industry: str = ""
    common_questions: List[str] = field(default_factory=list)
    key_skills: List[str] = field(default_factory=list)
    interview_format: str = ""
    preparation_tips: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate industry guidance data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate industry guidance data"""
        if not self.industry or not self.industry.strip():
            raise ValueError("Industry cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "industry": self.industry,
            "common_questions": self.common_questions,
            "key_skills": self.key_skills,
            "interview_format": self.interview_format,
            "preparation_tips": self.preparation_tips,
            "red_flags": self.red_flags,
            "success_factors": self.success_factors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndustryGuidance':
        """Create IndustryGuidance from dictionary"""
        return cls(
            industry=data["industry"],
            common_questions=data.get("common_questions", []),
            key_skills=data.get("key_skills", []),
            interview_format=data.get("interview_format", ""),
            preparation_tips=data.get("preparation_tips", []),
            red_flags=data.get("red_flags", []),
            success_factors=data.get("success_factors", [])
        )