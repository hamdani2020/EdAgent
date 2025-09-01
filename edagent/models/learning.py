"""
Learning path and milestone models for EdAgent
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any
from enum import Enum
import json
import uuid


class DifficultyLevel(str, Enum):
    """Enumeration for difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MilestoneStatus(str, Enum):
    """Enumeration for milestone status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class Milestone:
    """Represents a milestone in a learning path"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    skills_to_learn: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED
    resources: List[Dict[str, Any]] = field(default_factory=list)
    assessment_criteria: List[str] = field(default_factory=list)
    order_index: int = 0
    
    def __post_init__(self):
        """Validate milestone data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate milestone data"""
        if not self.id or not self.id.strip():
            raise ValueError("Milestone ID cannot be empty")
        
        if not self.title or not self.title.strip():
            raise ValueError("Milestone title cannot be empty")
        
        if not isinstance(self.skills_to_learn, list):
            raise ValueError("Skills to learn must be a list")
        
        if not isinstance(self.prerequisites, list):
            raise ValueError("Prerequisites must be a list")
        
        if not isinstance(self.difficulty_level, DifficultyLevel):
            if isinstance(self.difficulty_level, str):
                try:
                    self.difficulty_level = DifficultyLevel(self.difficulty_level.lower())
                except ValueError:
                    raise ValueError(f"Invalid difficulty level: {self.difficulty_level}")
            else:
                raise ValueError("Difficulty level must be a DifficultyLevel or valid string")
        
        if not isinstance(self.status, MilestoneStatus):
            if isinstance(self.status, str):
                try:
                    self.status = MilestoneStatus(self.status.lower())
                except ValueError:
                    raise ValueError(f"Invalid milestone status: {self.status}")
            else:
                raise ValueError("Status must be a MilestoneStatus or valid string")
        
        if not isinstance(self.resources, list):
            raise ValueError("Resources must be a list")
        
        if not isinstance(self.assessment_criteria, list):
            raise ValueError("Assessment criteria must be a list")
        
        if not isinstance(self.order_index, int) or self.order_index < 0:
            raise ValueError("Order index must be a non-negative integer")
    
    def add_resource(self, title: str, url: str, resource_type: str, 
                    is_free: bool = True, duration: Optional[timedelta] = None) -> None:
        """Add a learning resource to the milestone"""
        if not title or not title.strip():
            raise ValueError("Resource title cannot be empty")
        
        if not url or not url.strip():
            raise ValueError("Resource URL cannot be empty")
        
        resource = {
            "title": title,
            "url": url,
            "type": resource_type,
            "is_free": is_free,
            "duration": duration.total_seconds() if duration else None
        }
        self.resources.append(resource)
    
    def mark_completed(self) -> None:
        """Mark the milestone as completed"""
        self.status = MilestoneStatus.COMPLETED
    
    def mark_in_progress(self) -> None:
        """Mark the milestone as in progress"""
        self.status = MilestoneStatus.IN_PROGRESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "skills_to_learn": self.skills_to_learn,
            "prerequisites": self.prerequisites,
            "estimated_duration": self.estimated_duration.total_seconds() if self.estimated_duration else None,
            "difficulty_level": self.difficulty_level.value,
            "status": self.status.value,
            "resources": self.resources,
            "assessment_criteria": self.assessment_criteria,
            "order_index": self.order_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Milestone':
        """Create Milestone from dictionary"""
        duration = None
        if data.get("estimated_duration"):
            duration = timedelta(seconds=data["estimated_duration"])
        
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            skills_to_learn=data.get("skills_to_learn", []),
            prerequisites=data.get("prerequisites", []),
            estimated_duration=duration,
            difficulty_level=DifficultyLevel(data.get("difficulty_level", "beginner")),
            status=MilestoneStatus(data.get("status", "not_started")),
            resources=data.get("resources", []),
            assessment_criteria=data.get("assessment_criteria", []),
            order_index=data.get("order_index", 0)
        )


@dataclass
class LearningPath:
    """Represents a complete learning path with milestones"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    goal: str = ""
    milestones: List[Milestone] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    prerequisites: List[str] = field(default_factory=list)
    target_skills: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate learning path data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate learning path data"""
        if not self.id or not self.id.strip():
            raise ValueError("Learning path ID cannot be empty")
        
        if not self.title or not self.title.strip():
            raise ValueError("Learning path title cannot be empty")
        
        if not self.goal or not self.goal.strip():
            raise ValueError("Learning path goal cannot be empty")
        
        if not isinstance(self.milestones, list):
            raise ValueError("Milestones must be a list")
        
        # Validate all milestones
        for milestone in self.milestones:
            if not isinstance(milestone, Milestone):
                raise ValueError("All milestones must be Milestone objects")
            milestone.validate()
        
        if not isinstance(self.difficulty_level, DifficultyLevel):
            if isinstance(self.difficulty_level, str):
                try:
                    self.difficulty_level = DifficultyLevel(self.difficulty_level.lower())
                except ValueError:
                    raise ValueError(f"Invalid difficulty level: {self.difficulty_level}")
            else:
                raise ValueError("Difficulty level must be a DifficultyLevel or valid string")
        
        if not isinstance(self.prerequisites, list):
            raise ValueError("Prerequisites must be a list")
        
        if not isinstance(self.target_skills, list):
            raise ValueError("Target skills must be a list")
        
        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime object")
        
        if not isinstance(self.updated_at, datetime):
            raise ValueError("Updated at must be a datetime object")
    
    def add_milestone(self, milestone: Milestone) -> None:
        """Add a milestone to the learning path"""
        if not isinstance(milestone, Milestone):
            raise ValueError("Milestone must be a Milestone object")
        
        milestone.order_index = len(self.milestones)
        self.milestones.append(milestone)
        self.updated_at = datetime.now()
        
        # Recalculate estimated duration
        self._update_estimated_duration()
    
    def get_milestone_by_id(self, milestone_id: str) -> Optional[Milestone]:
        """Get a milestone by its ID"""
        for milestone in self.milestones:
            if milestone.id == milestone_id:
                return milestone
        return None
    
    def get_current_milestone(self) -> Optional[Milestone]:
        """Get the current milestone (first not completed)"""
        for milestone in self.milestones:
            if milestone.status != MilestoneStatus.COMPLETED:
                return milestone
        return None
    
    def get_progress(self) -> float:
        """Get learning path progress as a percentage"""
        if not self.milestones:
            return 0.0
        
        completed_count = sum(1 for m in self.milestones if m.status == MilestoneStatus.COMPLETED)
        return completed_count / len(self.milestones)
    
    def get_completed_milestones(self) -> List[Milestone]:
        """Get all completed milestones"""
        return [m for m in self.milestones if m.status == MilestoneStatus.COMPLETED]
    
    def get_remaining_milestones(self) -> List[Milestone]:
        """Get all remaining (not completed) milestones"""
        return [m for m in self.milestones if m.status != MilestoneStatus.COMPLETED]
    
    def _update_estimated_duration(self) -> None:
        """Update the estimated duration based on milestones"""
        total_seconds = 0
        for milestone in self.milestones:
            if milestone.estimated_duration:
                total_seconds += milestone.estimated_duration.total_seconds()
        
        if total_seconds > 0:
            self.estimated_duration = timedelta(seconds=total_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "goal": self.goal,
            "milestones": [m.to_dict() for m in self.milestones],
            "estimated_duration": self.estimated_duration.total_seconds() if self.estimated_duration else None,
            "difficulty_level": self.difficulty_level.value,
            "prerequisites": self.prerequisites,
            "target_skills": self.target_skills,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningPath':
        """Create LearningPath from dictionary"""
        # Convert milestones
        milestones = []
        for milestone_data in data.get("milestones", []):
            milestones.append(Milestone.from_dict(milestone_data))
        
        # Convert duration
        duration = None
        if data.get("estimated_duration"):
            duration = timedelta(seconds=data["estimated_duration"])
        
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            goal=data["goal"],
            milestones=milestones,
            estimated_duration=duration,
            difficulty_level=DifficultyLevel(data.get("difficulty_level", "beginner")),
            prerequisites=data.get("prerequisites", []),
            target_skills=data.get("target_skills", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class SkillAssessment:
    """Represents the results of a skill assessment"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    skill_area: str = ""
    overall_level: DifficultyLevel = DifficultyLevel.BEGINNER
    confidence_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    detailed_scores: Dict[str, float] = field(default_factory=dict)
    assessment_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate skill assessment data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate skill assessment data"""
        if not self.id or not self.id.strip():
            raise ValueError("Assessment ID cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.skill_area or not self.skill_area.strip():
            raise ValueError("Skill area cannot be empty")
        
        if not isinstance(self.overall_level, DifficultyLevel):
            if isinstance(self.overall_level, str):
                try:
                    self.overall_level = DifficultyLevel(self.overall_level.lower())
                except ValueError:
                    raise ValueError(f"Invalid difficulty level: {self.overall_level}")
            else:
                raise ValueError("Overall level must be a DifficultyLevel or valid string")
        
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if not isinstance(self.strengths, list):
            raise ValueError("Strengths must be a list")
        
        if not isinstance(self.weaknesses, list):
            raise ValueError("Weaknesses must be a list")
        
        if not isinstance(self.recommendations, list):
            raise ValueError("Recommendations must be a list")
        
        if not isinstance(self.detailed_scores, dict):
            raise ValueError("Detailed scores must be a dictionary")
        
        # Validate detailed scores
        for key, score in self.detailed_scores.items():
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                raise ValueError(f"Score for {key} must be between 0.0 and 1.0")
        
        if not isinstance(self.assessment_date, datetime):
            raise ValueError("Assessment date must be a datetime object")
    
    def add_strength(self, strength: str) -> None:
        """Add a strength to the assessment"""
        if not strength or not strength.strip():
            raise ValueError("Strength cannot be empty")
        self.strengths.append(strength)
    
    def add_weakness(self, weakness: str) -> None:
        """Add a weakness to the assessment"""
        if not weakness or not weakness.strip():
            raise ValueError("Weakness cannot be empty")
        self.weaknesses.append(weakness)
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation to the assessment"""
        if not recommendation or not recommendation.strip():
            raise ValueError("Recommendation cannot be empty")
        self.recommendations.append(recommendation)
    
    def set_detailed_score(self, category: str, score: float) -> None:
        """Set a detailed score for a specific category"""
        if not category or not category.strip():
            raise ValueError("Category cannot be empty")
        
        if not 0.0 <= score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        
        self.detailed_scores[category] = score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_area": self.skill_area,
            "overall_level": self.overall_level.value,
            "confidence_score": self.confidence_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "detailed_scores": self.detailed_scores,
            "assessment_date": self.assessment_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillAssessment':
        """Create SkillAssessment from dictionary"""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            skill_area=data["skill_area"],
            overall_level=DifficultyLevel(data.get("overall_level", "beginner")),
            confidence_score=data.get("confidence_score", 0.0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            recommendations=data.get("recommendations", []),
            detailed_scores=data.get("detailed_scores", {}),
            assessment_date=datetime.fromisoformat(data.get("assessment_date", datetime.now().isoformat()))
        )