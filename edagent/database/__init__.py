"""
Database layer for EdAgent application
"""

from .connection import get_database_connection, DatabaseManager
from .models import Base, User, UserSkill, Conversation

__all__ = [
    "get_database_connection",
    "DatabaseManager",
    "Base",
    "User", 
    "UserSkill",
    "Conversation",
]