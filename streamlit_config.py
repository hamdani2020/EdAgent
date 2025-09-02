"""
Configuration settings for EdAgent Streamlit frontend
"""

import os
from typing import Dict, Any

class StreamlitConfig:
    """Configuration class for Streamlit app"""
    
    # API Configuration
    API_BASE_URL = os.getenv("EDAGENT_API_URL", "http://localhost:8000/api/v1")
    WS_URL = os.getenv("EDAGENT_WS_URL", "ws://localhost:8000/api/v1/ws")
    
    # App Configuration
    APP_TITLE = "EdAgent - AI Career Coach"
    APP_ICON = "🎓"
    PAGE_LAYOUT = "wide"
    
    # Theme Configuration
    THEME = {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f8f9fa",
        "textColor": "#262730"
    }
    
    # Feature Flags
    FEATURES = {
        "websocket_chat": True,
        "real_time_updates": True,
        "file_upload": True,
        "data_export": True,
        "analytics_dashboard": True,
        "interview_prep": True,
        "resume_analysis": True
    }
    
    # API Timeouts
    REQUEST_TIMEOUT = 30
    WEBSOCKET_TIMEOUT = 60
    
    # UI Configuration
    CHAT_MESSAGE_LIMIT = 100
    PAGINATION_SIZE = 10
    MAX_FILE_SIZE_MB = 10
    
    # Mock Data Configuration (for development) - DISABLED
    USE_MOCK_DATA = False
    
    @classmethod
    def get_api_headers(cls, auth_token: str = None) -> Dict[str, str]:
        """Get API headers with optional authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EdAgent-Streamlit/1.0"
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        return headers
    
    @classmethod
    def get_websocket_headers(cls, auth_token: str, user_id: str) -> Dict[str, str]:
        """Get WebSocket headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "User-ID": user_id
        }

# Utility functions

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return StreamlitConfig.FEATURES.get(feature_name, False)