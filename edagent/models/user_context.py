"""
User context and skill models for EdAgent
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from enum import Enum
import json
from pydantic import BaseModel, validator, Field


class SkillLevelEnum(str, Enum):
    """Enumeration for skill levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningStyleEnum(str, Enum):
    """Enumeration for learning styles"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"


@dataclass
class SkillLevel:
    """Represents a user's skill level in a specific area"""
    skill_name: str
    level: SkillLevelEnum
    confidence_score: float
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate skill level data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate skill level data"""
        if not self.skill_name or not self.skill_name.strip():
            raise ValueError("Skill name cannot be empty")
        
        if not isinstance(self.level, SkillLevelEnum):
            if isinstance(self.level, str):
                try:
                    self.level = SkillLevelEnum(self.level.lower())
                except ValueError:
                    raise ValueError(f"Invalid skill level: {self.level}")
            else:
                raise ValueError("Skill level must be a SkillLevelEnum or valid string")
        
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if not isinstance(self.last_updated, datetime):
            raise ValueError("Last updated must be a datetime object")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "skill_name": self.skill_name,
            "level": self.level.value,
            "confidence_score": self.confidence_score,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillLevel':
        """Create SkillLevel from dictionary"""
        return cls(
            skill_name=data["skill_name"],
            level=SkillLevelEnum(data["level"]),
            confidence_score=data["confidence_score"],
            last_updated=datetime.fromisoformat(data["last_updated"])
        )


@dataclass
class UserPreferences:
    """User learning preferences and constraints"""
    learning_style: LearningStyleEnum
    time_commitment: str  # e.g., "2-3 hours/week"
    budget_preference: Literal["free", "low_cost", "any"] = "free"
    preferred_platforms: List[str] = field(default_factory=list)
    content_types: List[str] = field(default_factory=lambda: ["video", "article", "interactive"])
    difficulty_preference: Literal["gradual", "challenging", "mixed"] = "gradual"
    
    def __post_init__(self):
        """Validate user preferences after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate user preferences"""
        if not isinstance(self.learning_style, LearningStyleEnum):
            if isinstance(self.learning_style, str):
                try:
                    self.learning_style = LearningStyleEnum(self.learning_style.lower())
                except ValueError:
                    raise ValueError(f"Invalid learning style: {self.learning_style}")
            else:
                raise ValueError("Learning style must be a LearningStyleEnum or valid string")
        
        if not self.time_commitment or not self.time_commitment.strip():
            raise ValueError("Time commitment cannot be empty")
        
        if self.budget_preference not in ["free", "low_cost", "any"]:
            raise ValueError("Budget preference must be 'free', 'low_cost', or 'any'")
        
        if self.difficulty_preference not in ["gradual", "challenging", "mixed"]:
            raise ValueError("Difficulty preference must be 'gradual', 'challenging', or 'mixed'")
        
        # Validate content types
        valid_content_types = {"video", "article", "interactive", "course", "tutorial", "book"}
        for content_type in self.content_types:
            if content_type not in valid_content_types:
                raise ValueError(f"Invalid content type: {content_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "learning_style": self.learning_style.value,
            "time_commitment": self.time_commitment,
            "budget_preference": self.budget_preference,
            "preferred_platforms": self.preferred_platforms,
            "content_types": self.content_types,
            "difficulty_preference": self.difficulty_preference
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create UserPreferences from dictionary"""
        return cls(
            learning_style=LearningStyleEnum(data["learning_style"]),
            time_commitment=data["time_commitment"],
            budget_preference=data.get("budget_preference", "free"),
            preferred_platforms=data.get("preferred_platforms", []),
            content_types=data.get("content_types", ["video", "article", "interactive"]),
            difficulty_preference=data.get("difficulty_preference", "gradual")
        )


@dataclass
class UserContext:
    """Complete user context including skills, goals, and preferences"""
    user_id: str
    current_skills: Dict[str, SkillLevel] = field(default_factory=dict)
    career_goals: List[str] = field(default_factory=list)
    learning_preferences: Optional[UserPreferences] = None
    conversation_history: List[str] = field(default_factory=list)  # Will be Message objects later
    assessment_results: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate user context after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate user context data"""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        # Validate all skill levels
        for skill_name, skill_level in self.current_skills.items():
            if not isinstance(skill_level, SkillLevel):
                raise ValueError(f"Invalid skill level object for {skill_name}")
            skill_level.validate()
        
        # Validate preferences if provided
        if self.learning_preferences is not None:
            if not isinstance(self.learning_preferences, UserPreferences):
                raise ValueError("Learning preferences must be UserPreferences object")
            self.learning_preferences.validate()
        
        # Validate timestamps
        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime object")
        
        if not isinstance(self.last_active, datetime):
            raise ValueError("Last active must be a datetime object")
    
    def add_skill(self, skill_name: str, level: SkillLevelEnum, confidence_score: float) -> None:
        """Add or update a skill"""
        skill_level = SkillLevel(
            skill_name=skill_name,
            level=level,
            confidence_score=confidence_score
        )
        self.current_skills[skill_name] = skill_level
        self.last_active = datetime.now()
    
    def get_skill_level(self, skill_name: str) -> Optional[SkillLevel]:
        """Get skill level for a specific skill"""
        return self.current_skills.get(skill_name)
    
    def update_last_active(self) -> None:
        """Update the last active timestamp"""
        self.last_active = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "current_skills": {
                name: skill.to_dict() for name, skill in self.current_skills.items()
            },
            "career_goals": self.career_goals,
            "learning_preferences": self.learning_preferences.to_dict() if self.learning_preferences else None,
            "conversation_history": self.conversation_history,
            "assessment_results": self.assessment_results,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserContext':
        """Create UserContext from dictionary"""
        # Convert skills dictionary
        skills = {}
        for name, skill_data in data.get("current_skills", {}).items():
            skills[name] = SkillLevel.from_dict(skill_data)
        
        # Convert preferences
        preferences = None
        if data.get("learning_preferences"):
            preferences = UserPreferences.from_dict(data["learning_preferences"])
        
        return cls(
            user_id=data["user_id"],
            current_skills=skills,
            career_goals=data.get("career_goals", []),
            learning_preferences=preferences,
            conversation_history=data.get("conversation_history", []),
            assessment_results=data.get("assessment_results"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.now().isoformat()))
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UserContext':
        """Create UserContext from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)