"""
Resume analysis models for EdAgent
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
import json
import uuid


class IndustryType(str, Enum):
    """Enumeration for industry types"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    MARKETING = "marketing"
    CONSULTING = "consulting"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    OTHER = "other"


class ExperienceLevel(str, Enum):
    """Enumeration for experience levels"""
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    EXECUTIVE = "executive"


class FeedbackSeverity(str, Enum):
    """Enumeration for feedback severity levels"""
    CRITICAL = "critical"
    IMPORTANT = "important"
    SUGGESTION = "suggestion"
    POSITIVE = "positive"


@dataclass
class WorkExperience:
    """Represents a work experience entry"""
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    description: str = ""
    achievements: List[str] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)
    is_current: bool = False
    
    def __post_init__(self):
        """Validate work experience data"""
        if not self.job_title or not self.job_title.strip():
            raise ValueError("Job title cannot be empty")
        
        if not self.company or not self.company.strip():
            raise ValueError("Company name cannot be empty")
        
        if not isinstance(self.start_date, date):
            raise ValueError("Start date must be a date object")
        
        if self.end_date and not isinstance(self.end_date, date):
            raise ValueError("End date must be a date object or None")
        
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        
        if self.is_current and self.end_date:
            raise ValueError("Current job cannot have an end date")
    
    def duration_months(self) -> int:
        """Calculate duration in months"""
        end = self.end_date or date.today()
        years = end.year - self.start_date.year
        months = end.month - self.start_date.month
        return years * 12 + months
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "job_title": self.job_title,
            "company": self.company,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "achievements": self.achievements,
            "skills_used": self.skills_used,
            "is_current": self.is_current
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkExperience':
        """Create WorkExperience from dictionary"""
        return cls(
            job_title=data["job_title"],
            company=data["company"],
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            description=data.get("description", ""),
            achievements=data.get("achievements", []),
            skills_used=data.get("skills_used", []),
            is_current=data.get("is_current", False)
        )


@dataclass
class Education:
    """Represents an education entry"""
    degree: str
    institution: str
    graduation_date: Optional[date] = None
    gpa: Optional[float] = None
    relevant_coursework: List[str] = field(default_factory=list)
    honors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate education data"""
        if not self.degree or not self.degree.strip():
            raise ValueError("Degree cannot be empty")
        
        if not self.institution or not self.institution.strip():
            raise ValueError("Institution cannot be empty")
        
        if self.gpa is not None and not 0.0 <= self.gpa <= 4.0:
            raise ValueError("GPA must be between 0.0 and 4.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "degree": self.degree,
            "institution": self.institution,
            "graduation_date": self.graduation_date.isoformat() if self.graduation_date else None,
            "gpa": self.gpa,
            "relevant_coursework": self.relevant_coursework,
            "honors": self.honors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Education':
        """Create Education from dictionary"""
        return cls(
            degree=data["degree"],
            institution=data["institution"],
            graduation_date=date.fromisoformat(data["graduation_date"]) if data.get("graduation_date") else None,
            gpa=data.get("gpa"),
            relevant_coursework=data.get("relevant_coursework", []),
            honors=data.get("honors", [])
        )


@dataclass
class ResumeFeedback:
    """Represents feedback for a specific aspect of the resume"""
    category: str
    severity: FeedbackSeverity
    message: str
    suggestion: str
    industry_specific: bool = False
    
    def __post_init__(self):
        """Validate feedback data"""
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")
        
        if not self.message or not self.message.strip():
            raise ValueError("Message cannot be empty")
        
        if not self.suggestion or not self.suggestion.strip():
            raise ValueError("Suggestion cannot be empty")
        
        if not isinstance(self.severity, FeedbackSeverity):
            if isinstance(self.severity, str):
                try:
                    self.severity = FeedbackSeverity(self.severity.lower())
                except ValueError:
                    raise ValueError(f"Invalid feedback severity: {self.severity}")
            else:
                raise ValueError("Severity must be a FeedbackSeverity or valid string")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "industry_specific": self.industry_specific
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResumeFeedback':
        """Create ResumeFeedback from dictionary"""
        return cls(
            category=data["category"],
            severity=FeedbackSeverity(data["severity"]),
            message=data["message"],
            suggestion=data["suggestion"],
            industry_specific=data.get("industry_specific", False)
        )


@dataclass
class Resume:
    """Represents a complete resume for analysis"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    work_experience: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    target_industry: Optional[IndustryType] = None
    target_role: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate resume data"""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")
        
        # Validate work experience entries
        for exp in self.work_experience:
            if not isinstance(exp, WorkExperience):
                raise ValueError("All work experience entries must be WorkExperience objects")
        
        # Validate education entries
        for edu in self.education:
            if not isinstance(edu, Education):
                raise ValueError("All education entries must be Education objects")
    
    def get_total_experience_months(self) -> int:
        """Calculate total work experience in months"""
        return sum(exp.duration_months() for exp in self.work_experience)
    
    def get_experience_level(self) -> ExperienceLevel:
        """Determine experience level based on work history"""
        total_months = self.get_total_experience_months()
        
        if total_months < 12:
            return ExperienceLevel.ENTRY_LEVEL
        elif total_months < 36:
            return ExperienceLevel.JUNIOR
        elif total_months < 84:
            return ExperienceLevel.MID_LEVEL
        elif total_months < 120:
            return ExperienceLevel.SENIOR
        else:
            return ExperienceLevel.EXECUTIVE
    
    def get_all_skills(self) -> List[str]:
        """Get all skills mentioned across the resume"""
        all_skills = set(self.skills)
        
        # Add skills from work experience
        for exp in self.work_experience:
            all_skills.update(exp.skills_used)
        
        # Add skills from education coursework
        for edu in self.education:
            all_skills.update(edu.relevant_coursework)
        
        return list(all_skills)
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "summary": self.summary,
            "work_experience": [exp.to_dict() for exp in self.work_experience],
            "education": [edu.to_dict() for edu in self.education],
            "skills": self.skills,
            "certifications": self.certifications,
            "projects": self.projects,
            "languages": self.languages,
            "target_industry": self.target_industry.value if self.target_industry else None,
            "target_role": self.target_role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Resume':
        """Create Resume from dictionary"""
        work_experience = [
            WorkExperience.from_dict(exp_data) 
            for exp_data in data.get("work_experience", [])
        ]
        
        education = [
            Education.from_dict(edu_data) 
            for edu_data in data.get("education", [])
        ]
        
        target_industry = None
        if data.get("target_industry"):
            target_industry = IndustryType(data["target_industry"])
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data["user_id"],
            name=data["name"],
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            location=data.get("location", ""),
            summary=data.get("summary", ""),
            work_experience=work_experience,
            education=education,
            skills=data.get("skills", []),
            certifications=data.get("certifications", []),
            projects=data.get("projects", []),
            languages=data.get("languages", []),
            target_industry=target_industry,
            target_role=data.get("target_role", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class ResumeAnalysis:
    """Represents the complete analysis of a resume"""
    resume_id: str
    user_id: str
    overall_score: float
    feedback: List[ResumeFeedback] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    industry_alignment: float = 0.0
    ats_compatibility: float = 0.0
    keyword_optimization: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate analysis data"""
        if not self.resume_id or not self.resume_id.strip():
            raise ValueError("Resume ID cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError("Overall score must be between 0.0 and 100.0")
        
        if not 0.0 <= self.industry_alignment <= 1.0:
            raise ValueError("Industry alignment must be between 0.0 and 1.0")
        
        if not 0.0 <= self.ats_compatibility <= 1.0:
            raise ValueError("ATS compatibility must be between 0.0 and 1.0")
        
        if not 0.0 <= self.keyword_optimization <= 1.0:
            raise ValueError("Keyword optimization must be between 0.0 and 1.0")
        
        # Validate feedback entries
        for feedback in self.feedback:
            if not isinstance(feedback, ResumeFeedback):
                raise ValueError("All feedback entries must be ResumeFeedback objects")
    
    def add_feedback(self, category: str, severity: FeedbackSeverity, 
                    message: str, suggestion: str, industry_specific: bool = False) -> None:
        """Add feedback to the analysis"""
        feedback = ResumeFeedback(
            category=category,
            severity=severity,
            message=message,
            suggestion=suggestion,
            industry_specific=industry_specific
        )
        self.feedback.append(feedback)
    
    def get_feedback_by_severity(self, severity: FeedbackSeverity) -> List[ResumeFeedback]:
        """Get feedback filtered by severity"""
        return [fb for fb in self.feedback if fb.severity == severity]
    
    def get_feedback_by_category(self, category: str) -> List[ResumeFeedback]:
        """Get feedback filtered by category"""
        return [fb for fb in self.feedback if fb.category.lower() == category.lower()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "resume_id": self.resume_id,
            "user_id": self.user_id,
            "overall_score": self.overall_score,
            "feedback": [fb.to_dict() for fb in self.feedback],
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "industry_alignment": self.industry_alignment,
            "ats_compatibility": self.ats_compatibility,
            "keyword_optimization": self.keyword_optimization,
            "recommendations": self.recommendations,
            "analyzed_at": self.analyzed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResumeAnalysis':
        """Create ResumeAnalysis from dictionary"""
        feedback = [
            ResumeFeedback.from_dict(fb_data) 
            for fb_data in data.get("feedback", [])
        ]
        
        return cls(
            resume_id=data["resume_id"],
            user_id=data["user_id"],
            overall_score=data["overall_score"],
            feedback=feedback,
            strengths=data.get("strengths", []),
            improvement_areas=data.get("improvement_areas", []),
            industry_alignment=data.get("industry_alignment", 0.0),
            ats_compatibility=data.get("ats_compatibility", 0.0),
            keyword_optimization=data.get("keyword_optimization", 0.0),
            recommendations=data.get("recommendations", []),
            analyzed_at=datetime.fromisoformat(data.get("analyzed_at", datetime.now().isoformat()))
        )