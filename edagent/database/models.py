"""
SQLAlchemy models for EdAgent database schema
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, DateTime, Float, Text, Boolean, 
    ForeignKey, JSON, Integer, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User profile and preferences"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())
    preferences = Column(JSON, default=dict)
    
    # Relationships
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, created_at={self.created_at})>"


class UserSkill(Base):
    """User skill levels and assessments"""
    __tablename__ = "user_skills"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    skill_name = Column(String(100), primary_key=True)
    level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    confidence_score = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="skills")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'skill_name', name='unique_user_skill'),
    )
    
    def __repr__(self) -> str:
        return f"<UserSkill(user_id={self.user_id}, skill={self.skill_name}, level={self.level})>"


class Conversation(Base):
    """Conversation history and messages"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_type = Column(String(50), default="general")  # general, assessment, learning_path, etc.
    context_data = Column(JSON, default=dict)  # Additional context data
    
    # Relationship
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, type={self.message_type})>"


class LearningPath(Base):
    """User learning paths and progress"""
    __tablename__ = "learning_paths"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    estimated_duration_days = Column(Integer)
    difficulty_level = Column(String(20))
    is_active = Column(Boolean, default=True)
    completion_percentage = Column(Float, default=0.0)
    
    # Relationship
    user = relationship("User", back_populates="learning_paths")
    milestones = relationship("Milestone", back_populates="learning_path", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<LearningPath(id={self.id}, goal={self.goal}, progress={self.completion_percentage}%)>"


class Milestone(Base):
    """Learning path milestones and progress tracking"""
    __tablename__ = "milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    estimated_hours = Column(Integer)
    prerequisites = Column(JSON, default=list)  # List of prerequisite milestone IDs or skills
    
    # Relationship
    learning_path = relationship("LearningPath", back_populates="milestones")
    
    def __repr__(self) -> str:
        return f"<Milestone(id={self.id}, title={self.title}, completed={self.is_completed})>"


class ContentRecommendation(Base):
    """Cached content recommendations"""
    __tablename__ = "content_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False)
    url = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False)  # youtube, coursera, etc.
    content_type = Column(String(50), nullable=False)  # video, course, article, interactive
    duration_minutes = Column(Integer)
    rating = Column(Float)
    is_free = Column(Boolean, default=True)
    skill_tags = Column(JSON, default=list)  # List of relevant skills
    difficulty_level = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_verified = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<ContentRecommendation(title={self.title}, platform={self.platform})>"