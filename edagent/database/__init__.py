"""
Database layer for EdAgent application
"""

from .connection import get_database_connection, DatabaseManager, init_database, close_database
from .models import Base, User, UserSkill, Conversation, LearningPath, Milestone, ContentRecommendation
from .utils import DatabaseUtils

__all__ = [
    "get_database_connection",
    "DatabaseManager",
    "init_database",
    "close_database",
    "DatabaseUtils",
    "Base",
    "User", 
    "UserSkill",
    "Conversation",
    "LearningPath",
    "Milestone",
    "ContentRecommendation",
]