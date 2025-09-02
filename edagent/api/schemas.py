"""
Pydantic schemas for API request/response validation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums for validation
class SkillLevelEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningStyleEnum(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"


class MessageTypeEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ASSESSMENT = "assessment"
    LEARNING_PATH = "learning_path"


class ResponseTypeEnum(str, Enum):
    TEXT = "text"
    ASSESSMENT = "assessment"
    LEARNING_PATH = "learning_path"
    CONTENT_RECOMMENDATION = "content_recommendation"


class DifficultyLevelEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MilestoneStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# Base schemas
class BaseResponse(BaseModel):
    """Base response schema"""
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: Dict[str, Any]


# User-related schemas
class UserPreferencesSchema(BaseModel):
    """User preferences schema"""
    learning_style: LearningStyleEnum
    time_commitment: str = Field(..., description="e.g., '2-3 hours/week'")
    budget_preference: Literal["free", "low_cost", "any"] = "free"
    preferred_platforms: List[str] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=lambda: ["video", "article", "interactive"])
    difficulty_preference: Literal["gradual", "challenging", "mixed"] = "gradual"
    
    @validator('content_types')
    def validate_content_types(cls, v):
        valid_types = {"video", "article", "interactive", "course", "tutorial", "book"}
        for content_type in v:
            if content_type not in valid_types:
                raise ValueError(f"Invalid content type: {content_type}")
        return v


class SkillLevelSchema(BaseModel):
    """Skill level schema"""
    skill_name: str
    level: SkillLevelEnum
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.now)


class UserContextSchema(BaseModel):
    """User context schema"""
    user_id: str
    current_skills: Dict[str, SkillLevelSchema] = Field(default_factory=dict)
    career_goals: List[str] = Field(default_factory=list)
    learning_preferences: Optional[UserPreferencesSchema] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)


class CreateUserRequest(BaseModel):
    """Request schema for creating a user (registration)"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    name: Optional[str] = Field(None, description="User's full name")
    career_goals: List[str] = Field(default_factory=list)
    learning_preferences: Optional[UserPreferencesSchema] = None
    
    @validator('email')
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()


class LoginResponse(BaseModel):
    """Response schema for user login"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    expires_at: datetime = Field(..., description="Token expiration time")


class UpdateUserPreferencesRequest(BaseModel):
    """Request schema for updating user preferences"""
    learning_preferences: UserPreferencesSchema


class UpdateUserSkillsRequest(BaseModel):
    """Request schema for updating user skills"""
    skills: Dict[str, SkillLevelSchema]


# Conversation-related schemas
class MessageSchema(BaseModel):
    """Message schema"""
    id: str
    content: str
    message_type: MessageTypeEnum
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationRequest(BaseModel):
    """Request schema for conversation"""
    user_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ContentRecommendationSchema(BaseModel):
    """Content recommendation schema"""
    title: str
    url: str
    platform: str
    content_type: str
    duration: Optional[int] = Field(None, description="Duration in seconds")
    rating: float = Field(..., ge=0.0, le=5.0)
    is_free: bool
    skill_match_score: float = Field(..., ge=0.0, le=1.0)


class ConversationResponseSchema(BaseModel):
    """Conversation response schema"""
    message: str
    response_type: ResponseTypeEnum = ResponseTypeEnum.TEXT
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)
    suggested_actions: List[str] = Field(default_factory=list)
    content_recommendations: List[ContentRecommendationSchema] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Assessment-related schemas
class StartAssessmentRequest(BaseModel):
    """Request schema for starting an assessment"""
    user_id: str
    skill_area: str = Field(..., description="The skill area to assess")


class AssessmentQuestionSchema(BaseModel):
    """Assessment question schema"""
    question: str
    type: str = "open"
    options: List[str] = Field(default_factory=list)
    index: int


class AssessmentResponseRequest(BaseModel):
    """Request schema for assessment response"""
    assessment_id: str
    response: str = Field(..., min_length=1)
    question_index: Optional[int] = None


class AssessmentSessionSchema(BaseModel):
    """Assessment session schema"""
    id: str
    user_id: str
    skill_area: str
    questions: List[AssessmentQuestionSchema] = Field(default_factory=list)
    current_question_index: int = 0
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = Field(..., ge=0.0, le=1.0)


class SkillAssessmentResultSchema(BaseModel):
    """Skill assessment result schema"""
    id: str
    user_id: str
    skill_area: str
    overall_level: DifficultyLevelEnum
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    detailed_scores: Dict[str, float] = Field(default_factory=dict)
    assessment_date: datetime


# Learning path schemas
class ResourceSchema(BaseModel):
    """Learning resource schema"""
    title: str
    url: str
    type: str
    is_free: bool = True
    duration: Optional[int] = Field(None, description="Duration in seconds")


class MilestoneSchema(BaseModel):
    """Milestone schema"""
    id: str
    title: str
    description: str = ""
    skills_to_learn: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    estimated_duration: Optional[int] = Field(None, description="Duration in seconds")
    difficulty_level: DifficultyLevelEnum
    status: MilestoneStatusEnum
    resources: List[ResourceSchema] = Field(default_factory=list)
    assessment_criteria: List[str] = Field(default_factory=list)
    order_index: int = 0


class LearningPathSchema(BaseModel):
    """Learning path schema"""
    id: str
    title: str
    description: str = ""
    goal: str
    milestones: List[MilestoneSchema] = Field(default_factory=list)
    estimated_duration: Optional[int] = Field(None, description="Duration in seconds")
    difficulty_level: DifficultyLevelEnum
    prerequisites: List[str] = Field(default_factory=list)
    target_skills: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    progress: float = Field(..., ge=0.0, le=1.0)


class CreateLearningPathRequest(BaseModel):
    """Request schema for creating a learning path"""
    user_id: str
    goal: str = Field(..., min_length=1, description="Learning or career goal")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UpdateMilestoneStatusRequest(BaseModel):
    """Request schema for updating milestone status"""
    milestone_id: str
    status: MilestoneStatusEnum


# Response schemas
class ConversationHistoryResponse(BaseResponse):
    """Response schema for conversation history"""
    messages: List[MessageSchema]
    total_count: int


class UserProfileResponse(BaseResponse):
    """Response schema for user profile"""
    user: UserContextSchema


class AssessmentListResponse(BaseResponse):
    """Response schema for assessment list"""
    assessments: List[AssessmentSessionSchema]
    total_count: int


class LearningPathListResponse(BaseResponse):
    """Response schema for learning path list"""
    learning_paths: List[LearningPathSchema]
    total_count: int
# WebSocket Message Schemas
class WebSocketMessageType(str, Enum):
    CONNECTION_ESTABLISHED = "connection_established"
    AI_RESPONSE = "ai_response"
    TYPING_INDICATOR = "typing_indicator"
    ERROR = "error"
    BROADCAST = "broadcast"
    DISCONNECTION = "disconnection"


class WebSocketIncomingMessage(BaseModel):
    """Schema for incoming WebSocket messages from client"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional message metadata")


class WebSocketOutgoingMessage(BaseModel):
    """Schema for outgoing WebSocket messages to client"""
    type: WebSocketMessageType = Field(..., description="Message type")
    message: Optional[str] = Field(None, description="Message content")
    timestamp: str = Field(..., description="ISO timestamp of message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional message metadata")


class WebSocketAIResponse(WebSocketOutgoingMessage):
    """Schema for AI response messages via WebSocket"""
    type: Literal[WebSocketMessageType.AI_RESPONSE] = WebSocketMessageType.AI_RESPONSE
    message: str = Field(..., description="AI response message")
    response_type: ResponseTypeEnum = Field(..., description="Type of AI response")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested user actions")
    content_recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Content recommendations")
    follow_up_questions: Optional[List[str]] = Field(None, description="Follow-up questions")


class WebSocketTypingIndicator(WebSocketOutgoingMessage):
    """Schema for typing indicator messages"""
    type: Literal[WebSocketMessageType.TYPING_INDICATOR] = WebSocketMessageType.TYPING_INDICATOR
    is_typing: bool = Field(..., description="Whether AI is currently typing")


class WebSocketError(WebSocketOutgoingMessage):
    """Schema for error messages via WebSocket"""
    type: Literal[WebSocketMessageType.ERROR] = WebSocketMessageType.ERROR
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")


class WebSocketConnectionStatus(BaseModel):
    """Schema for WebSocket connection status"""
    active_connections: int = Field(..., description="Number of active connections")
    active_users: List[str] = Field(..., description="List of connected user IDs")
    connection_details: Dict[str, Dict[str, Any]] = Field(..., description="Detailed connection info")


class BroadcastRequest(BaseModel):
    """Schema for broadcast message requests"""
    message: str = Field(..., min_length=1, max_length=1000, description="Message to broadcast")
    user_ids: Optional[List[str]] = Field(None, description="Specific user IDs to send to (optional)")


class BroadcastResponse(BaseModel):
    """Schema for broadcast response"""
    message: str = Field(..., description="Status message")
    sent_to: int = Field(..., description="Number of users message was sent to")
    total_requested: int = Field(..., description="Total number of users requested")