"""
Content recommendation and course models for EdAgent
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any, Union
from enum import Enum
import json
import uuid


class ContentType(str, Enum):
    """Enumeration for content types"""
    VIDEO = "video"
    ARTICLE = "article"
    COURSE = "course"
    TUTORIAL = "tutorial"
    BOOK = "book"
    INTERACTIVE = "interactive"
    PODCAST = "podcast"
    DOCUMENTATION = "documentation"


class Platform(str, Enum):
    """Enumeration for content platforms"""
    YOUTUBE = "youtube"
    COURSERA = "coursera"
    UDEMY = "udemy"
    EDUX = "edx"
    KHAN_ACADEMY = "khan_academy"
    CODECADEMY = "codecademy"
    FREECODECAMP = "freecodecamp"
    MEDIUM = "medium"
    GITHUB = "github"
    OTHER = "other"


class DifficultyLevel(str, Enum):
    """Enumeration for content difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class ContentRecommendation:
    """Represents a recommended piece of educational content"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    url: str = ""
    platform: Platform = Platform.OTHER
    content_type: ContentType = ContentType.ARTICLE
    description: str = ""
    duration: Optional[timedelta] = None
    rating: float = 0.0
    is_free: bool = True
    price: Optional[float] = None
    currency: str = "USD"
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    skills_covered: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = ""
    published_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    skill_match_score: float = 0.0
    relevance_score: float = 0.0
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate content recommendation data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate content recommendation data"""
        if not self.id or not self.id.strip():
            raise ValueError("Content ID cannot be empty")
        
        if not self.title or not self.title.strip():
            raise ValueError("Content title cannot be empty")
        
        if not self.url or not self.url.strip():
            raise ValueError("Content URL cannot be empty")
        
        if not isinstance(self.platform, Platform):
            if isinstance(self.platform, str):
                try:
                    self.platform = Platform(self.platform.lower())
                except ValueError:
                    raise ValueError(f"Invalid platform: {self.platform}")
            else:
                raise ValueError("Platform must be a Platform or valid string")
        
        if not isinstance(self.content_type, ContentType):
            if isinstance(self.content_type, str):
                try:
                    self.content_type = ContentType(self.content_type.lower())
                except ValueError:
                    raise ValueError(f"Invalid content type: {self.content_type}")
            else:
                raise ValueError("Content type must be a ContentType or valid string")
        
        if not isinstance(self.difficulty_level, DifficultyLevel):
            if isinstance(self.difficulty_level, str):
                try:
                    self.difficulty_level = DifficultyLevel(self.difficulty_level.lower())
                except ValueError:
                    raise ValueError(f"Invalid difficulty level: {self.difficulty_level}")
            else:
                raise ValueError("Difficulty level must be a DifficultyLevel or valid string")
        
        if not 0.0 <= self.rating <= 5.0:
            raise ValueError("Rating must be between 0.0 and 5.0")
        
        if self.price is not None and self.price < 0:
            raise ValueError("Price cannot be negative")
        
        if not 0.0 <= self.skill_match_score <= 1.0:
            raise ValueError("Skill match score must be between 0.0 and 1.0")
        
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")
        
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        
        if not isinstance(self.skills_covered, list):
            raise ValueError("Skills covered must be a list")
        
        if not isinstance(self.prerequisites, list):
            raise ValueError("Prerequisites must be a list")
        
        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
    
    def calculate_overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate overall recommendation score based on weighted factors"""
        if weights is None:
            weights = {
                "skill_match": 0.4,
                "relevance": 0.3,
                "quality": 0.2,
                "rating": 0.1
            }
        
        normalized_rating = self.rating / 5.0 if self.rating > 0 else 0.0
        
        overall_score = (
            weights.get("skill_match", 0.4) * self.skill_match_score +
            weights.get("relevance", 0.3) * self.relevance_score +
            weights.get("quality", 0.2) * self.quality_score +
            weights.get("rating", 0.1) * normalized_rating
        )
        
        return min(max(overall_score, 0.0), 1.0)
    
    def matches_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Check if content matches user preferences"""
        # Check budget preference
        budget_pref = preferences.get("budget_preference", "free")
        if budget_pref == "free" and not self.is_free:
            return False
        
        # Check content type preference
        preferred_types = preferences.get("content_types", [])
        if preferred_types and self.content_type.value not in preferred_types:
            return False
        
        # Check platform preference
        preferred_platforms = preferences.get("preferred_platforms", [])
        if preferred_platforms and self.platform.value not in [p.lower() for p in preferred_platforms]:
            return False
        
        # Check difficulty preference
        difficulty_pref = preferences.get("difficulty_preference", "gradual")
        if difficulty_pref == "gradual" and self.difficulty_level == DifficultyLevel.EXPERT:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "platform": self.platform.value,
            "content_type": self.content_type.value,
            "description": self.description,
            "duration": self.duration.total_seconds() if self.duration else None,
            "rating": self.rating,
            "is_free": self.is_free,
            "price": self.price,
            "currency": self.currency,
            "difficulty_level": self.difficulty_level.value,
            "skills_covered": self.skills_covered,
            "prerequisites": self.prerequisites,
            "tags": self.tags,
            "author": self.author,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "skill_match_score": self.skill_match_score,
            "relevance_score": self.relevance_score,
            "quality_score": self.quality_score,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentRecommendation':
        """Create ContentRecommendation from dictionary"""
        duration = None
        if data.get("duration"):
            duration = timedelta(seconds=data["duration"])
        
        published_date = None
        if data.get("published_date"):
            published_date = datetime.fromisoformat(data["published_date"])
        
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])
        
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            platform=Platform(data.get("platform", "other")),
            content_type=ContentType(data.get("content_type", "article")),
            description=data.get("description", ""),
            duration=duration,
            rating=data.get("rating", 0.0),
            is_free=data.get("is_free", True),
            price=data.get("price"),
            currency=data.get("currency", "USD"),
            difficulty_level=DifficultyLevel(data.get("difficulty_level", "beginner")),
            skills_covered=data.get("skills_covered", []),
            prerequisites=data.get("prerequisites", []),
            tags=data.get("tags", []),
            author=data.get("author", ""),
            published_date=published_date,
            last_updated=last_updated,
            skill_match_score=data.get("skill_match_score", 0.0),
            relevance_score=data.get("relevance_score", 0.0),
            quality_score=data.get("quality_score", 0.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class YouTubeVideo(ContentRecommendation):
    """Specialized content recommendation for YouTube videos"""
    video_id: str = ""
    channel_name: str = ""
    channel_id: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    subscriber_count: int = 0
    thumbnail_url: str = ""
    captions_available: bool = False
    
    def __post_init__(self):
        """Validate YouTube video data after initialization"""
        # Set platform to YouTube
        self.platform = Platform.YOUTUBE
        self.content_type = ContentType.VIDEO
        super().__post_init__()
        
        if not self.video_id or not self.video_id.strip():
            raise ValueError("Video ID cannot be empty")
    
    def calculate_engagement_score(self) -> float:
        """Calculate engagement score based on likes, views, and comments"""
        if self.view_count == 0:
            return 0.0
        
        like_ratio = self.like_count / self.view_count if self.view_count > 0 else 0.0
        comment_ratio = self.comment_count / self.view_count if self.view_count > 0 else 0.0
        
        # Normalize and weight the engagement metrics (scale to 0-1 range)
        engagement_score = (like_ratio * 0.6 + comment_ratio * 0.4)
        return min(engagement_score, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        base_dict = super().to_dict()
        base_dict.update({
            "video_id": self.video_id,
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "subscriber_count": self.subscriber_count,
            "thumbnail_url": self.thumbnail_url,
            "captions_available": self.captions_available
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YouTubeVideo':
        """Create YouTubeVideo from dictionary"""
        # Create base ContentRecommendation first
        base_content = ContentRecommendation.from_dict(data)
        
        # Create YouTubeVideo with additional fields
        return cls(
            id=base_content.id,
            title=base_content.title,
            url=base_content.url,
            platform=Platform.YOUTUBE,
            content_type=ContentType.VIDEO,
            description=base_content.description,
            duration=base_content.duration,
            rating=base_content.rating,
            is_free=base_content.is_free,
            price=base_content.price,
            currency=base_content.currency,
            difficulty_level=base_content.difficulty_level,
            skills_covered=base_content.skills_covered,
            prerequisites=base_content.prerequisites,
            tags=base_content.tags,
            author=base_content.author,
            published_date=base_content.published_date,
            last_updated=base_content.last_updated,
            skill_match_score=base_content.skill_match_score,
            relevance_score=base_content.relevance_score,
            quality_score=base_content.quality_score,
            metadata=base_content.metadata,
            video_id=data.get("video_id", ""),
            channel_name=data.get("channel_name", ""),
            channel_id=data.get("channel_id", ""),
            view_count=data.get("view_count", 0),
            like_count=data.get("like_count", 0),
            comment_count=data.get("comment_count", 0),
            subscriber_count=data.get("subscriber_count", 0),
            thumbnail_url=data.get("thumbnail_url", ""),
            captions_available=data.get("captions_available", False)
        )


@dataclass
class Course(ContentRecommendation):
    """Specialized content recommendation for structured courses"""
    course_id: str = ""
    instructor: str = ""
    institution: str = ""
    enrollment_count: int = 0
    completion_rate: float = 0.0
    certificate_available: bool = False
    modules: List[Dict[str, Any]] = field(default_factory=list)
    assignments: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate course data after initialization"""
        # Set content type to course
        self.content_type = ContentType.COURSE
        super().__post_init__()
        
        if not 0.0 <= self.completion_rate <= 1.0:
            raise ValueError("Completion rate must be between 0.0 and 1.0")
        
        if not isinstance(self.modules, list):
            raise ValueError("Modules must be a list")
        
        if not isinstance(self.assignments, list):
            raise ValueError("Assignments must be a list")
    
    def add_module(self, title: str, description: str, duration: Optional[timedelta] = None) -> None:
        """Add a module to the course"""
        if not title or not title.strip():
            raise ValueError("Module title cannot be empty")
        
        module = {
            "title": title,
            "description": description,
            "duration": duration.total_seconds() if duration else None,
            "order": len(self.modules) + 1
        }
        self.modules.append(module)
    
    def add_assignment(self, title: str, description: str, assignment_type: str = "project") -> None:
        """Add an assignment to the course"""
        if not title or not title.strip():
            raise ValueError("Assignment title cannot be empty")
        
        assignment = {
            "title": title,
            "description": description,
            "type": assignment_type,
            "order": len(self.assignments) + 1
        }
        self.assignments.append(assignment)
    
    def calculate_course_score(self) -> float:
        """Calculate course quality score based on various factors"""
        base_score = self.calculate_overall_score()
        
        # Bonus for high completion rate
        completion_bonus = self.completion_rate * 0.1
        
        # Bonus for certificate availability
        certificate_bonus = 0.05 if self.certificate_available else 0.0
        
        # Bonus for structured content (modules and assignments)
        structure_bonus = 0.05 if (self.modules and self.assignments) else 0.0
        
        total_score = base_score + completion_bonus + certificate_bonus + structure_bonus
        return min(total_score, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        base_dict = super().to_dict()
        base_dict.update({
            "course_id": self.course_id,
            "instructor": self.instructor,
            "institution": self.institution,
            "enrollment_count": self.enrollment_count,
            "completion_rate": self.completion_rate,
            "certificate_available": self.certificate_available,
            "modules": self.modules,
            "assignments": self.assignments
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Course':
        """Create Course from dictionary"""
        # Create base ContentRecommendation first
        base_content = ContentRecommendation.from_dict(data)
        
        # Create Course with additional fields
        return cls(
            id=base_content.id,
            title=base_content.title,
            url=base_content.url,
            platform=base_content.platform,
            content_type=ContentType.COURSE,
            description=base_content.description,
            duration=base_content.duration,
            rating=base_content.rating,
            is_free=base_content.is_free,
            price=base_content.price,
            currency=base_content.currency,
            difficulty_level=base_content.difficulty_level,
            skills_covered=base_content.skills_covered,
            prerequisites=base_content.prerequisites,
            tags=base_content.tags,
            author=base_content.author,
            published_date=base_content.published_date,
            last_updated=base_content.last_updated,
            skill_match_score=base_content.skill_match_score,
            relevance_score=base_content.relevance_score,
            quality_score=base_content.quality_score,
            metadata=base_content.metadata,
            course_id=data.get("course_id", ""),
            instructor=data.get("instructor", ""),
            institution=data.get("institution", ""),
            enrollment_count=data.get("enrollment_count", 0),
            completion_rate=data.get("completion_rate", 0.0),
            certificate_available=data.get("certificate_available", False),
            modules=data.get("modules", []),
            assignments=data.get("assignments", [])
        )