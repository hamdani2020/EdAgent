"""
Data models for EdAgent application
"""

from .user_context import UserContext, SkillLevel, UserPreferences
from .conversation import Message, ConversationResponse, AssessmentSession
from .learning import LearningPath, Milestone, SkillAssessment
from .content import ContentRecommendation, Course, YouTubeVideo
from .resume import Resume, ResumeAnalysis, ResumeFeedback, WorkExperience, Education
from .interview import (
    InterviewQuestion, InterviewSession, InterviewFeedback, IndustryGuidance,
    InterviewType, DifficultyLevel, FeedbackType
)
from .auth import (
    UserSession, APIKey, AuthenticationRequest, AuthenticationResponse,
    TokenValidationResult, SessionStatus
)

__all__ = [
    "UserContext",
    "SkillLevel", 
    "UserPreferences",
    "Message",
    "ConversationResponse",
    "AssessmentSession",
    "LearningPath",
    "Milestone",
    "SkillAssessment",
    "ContentRecommendation",
    "Course",
    "YouTubeVideo",
    "Resume",
    "ResumeAnalysis",
    "ResumeFeedback",
    "WorkExperience",
    "Education",
    "InterviewQuestion",
    "InterviewSession",
    "InterviewFeedback",
    "IndustryGuidance",
    "InterviewType",
    "DifficultyLevel",
    "FeedbackType",
    "UserSession",
    "APIKey",
    "AuthenticationRequest",
    "AuthenticationResponse",
    "TokenValidationResult",
    "SessionStatus",
]