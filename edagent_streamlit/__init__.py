"""
EdAgent Streamlit Frontend Package

A comprehensive, modular web interface for the EdAgent career coaching assistant.
This package provides a maintainable, well-structured frontend with proper error handling,
consistent API integration patterns, and comprehensive logging capabilities.
"""

__version__ = "1.0.0"
__author__ = "EdAgent Team"

# Import main components for easy access
from .core.config import StreamlitConfig
from .core.session_manager import SessionManager
from .core.api_client import EnhancedEdAgentAPI
from .core.error_handler import ErrorHandler
from .core.logger import setup_logging

# Import UI components
from .components.auth import AuthenticationComponents
from .components.chat import ChatComponents
from .components.assessment import AssessmentComponents
from .components.learning_path import LearningPathComponents
from .components.privacy import PrivacyComponents
from .components.analytics import AnalyticsComponents
from .components.profile import ProfileComponents

# Import utilities
from .utils.validators import FormValidator
from .utils.formatters import DataFormatter
from .utils.helpers import UIHelpers

__all__ = [
    # Core
    'StreamlitConfig',
    'SessionManager', 
    'EnhancedEdAgentAPI',
    'ErrorHandler',
    'setup_logging',
    
    # Components
    'AuthenticationComponents',
    'ChatComponents',
    'AssessmentComponents', 
    'LearningPathComponents',
    'PrivacyComponents',
    'AnalyticsComponents',
    'ProfileComponents',
    
    # Utilities
    'FormValidator',
    'DataFormatter',
    'UIHelpers'
]