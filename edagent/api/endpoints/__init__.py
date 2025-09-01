"""
API endpoints for EdAgent
"""

from .conversation import router as conversation_router
from .user import router as user_router
from .assessment import router as assessment_router
from .learning import router as learning_router

__all__ = [
    "conversation_router",
    "user_router", 
    "assessment_router",
    "learning_router"
]