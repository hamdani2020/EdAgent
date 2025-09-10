"""
Core modules for EdAgent Streamlit application

This package contains the fundamental components that provide the foundation
for the entire application including configuration, session management,
API communication, error handling, and logging.
"""

from .config import StreamlitConfig, DeploymentConfig
from .session_manager import SessionManager, UserInfo, UserPreferences
from .api_client import EnhancedEdAgentAPI, APIResponse, APIError
from .error_handler import ErrorHandler, ErrorCategory, UserFriendlyError
from .logger import setup_logging, get_logger

__all__ = [
    'StreamlitConfig',
    'DeploymentConfig', 
    'SessionManager',
    'UserInfo',
    'UserPreferences',
    'EnhancedEdAgentAPI',
    'APIResponse',
    'APIError',
    'ErrorHandler',
    'ErrorCategory',
    'UserFriendlyError',
    'setup_logging',
    'get_logger'
]