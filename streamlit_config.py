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
    
    # Mock Data Configuration (for development)
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
    
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

# Mock data for development and testing
MOCK_DATA = {
    "user_profile": {
        "user_id": "demo_user",
        "career_goals": [
            "Become a full-stack developer",
            "Learn machine learning",
            "Get AWS certification"
        ],
        "current_skills": {
            "Python": {"level": "Intermediate", "confidence_score": 0.75},
            "JavaScript": {"level": "Beginner", "confidence_score": 0.45},
            "SQL": {"level": "Advanced", "confidence_score": 0.90}
        },
        "learning_preferences": {
            "learning_style": "visual",
            "time_commitment": "10-20",
            "budget_preference": "moderate",
            "preferred_platforms": ["youtube", "coursera", "udemy"],
            "content_types": ["video", "interactive"],
            "difficulty_preference": "mixed"
        },
        "created_at": "2024-01-01T00:00:00Z",
        "last_active": "2024-01-15T12:00:00Z"
    },
    
    "learning_paths": [
        {
            "id": "path_1",
            "title": "Full-Stack Web Development",
            "goal": "Become a full-stack developer",
            "progress": 0.35,
            "milestones": [
                {
                    "id": "m1",
                    "title": "Frontend Fundamentals",
                    "status": "completed",
                    "description": "Learn HTML, CSS, and JavaScript basics"
                },
                {
                    "id": "m2", 
                    "title": "React Development",
                    "status": "in_progress",
                    "description": "Build interactive UIs with React"
                },
                {
                    "id": "m3",
                    "title": "Backend with Node.js",
                    "status": "not_started",
                    "description": "Create APIs and server-side logic"
                }
            ]
        }
    ],
    
    "assessments": [
        {
            "id": "assessment_1",
            "skill_area": "Python Programming",
            "status": "completed",
            "score": 85,
            "level": "Intermediate",
            "date": "2024-01-10"
        },
        {
            "id": "assessment_2",
            "skill_area": "Web Development",
            "status": "completed", 
            "score": 72,
            "level": "Beginner",
            "date": "2024-01-08"
        }
    ],
    
    "recommendations": [
        {
            "title": "Python for Everybody Specialization",
            "type": "course",
            "url": "https://coursera.org/specializations/python",
            "description": "Learn Python programming from basics to advanced topics",
            "rating": 4.8,
            "cost": "Free",
            "tags": ["Python", "Programming", "Beginner"]
        },
        {
            "title": "JavaScript Crash Course",
            "type": "video",
            "url": "https://youtube.com/watch?v=hdI2bqOjy3c",
            "description": "Complete JavaScript tutorial for beginners",
            "rating": 4.6,
            "cost": "Free",
            "tags": ["JavaScript", "Web Development", "Tutorial"]
        }
    ],
    
    "chat_messages": [
        {
            "role": "assistant",
            "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "role": "user", 
            "content": "I want to become a data scientist",
            "timestamp": "2024-01-15T10:01:00Z"
        },
        {
            "role": "assistant",
            "content": "That's a great goal! Data science is an exciting field. Let me help you create a personalized learning path. First, could you tell me about your current background and experience with programming or statistics?",
            "timestamp": "2024-01-15T10:01:30Z"
        }
    ],
    
    "analytics": {
        "skills_assessed": 5,
        "learning_paths": 2,
        "study_hours": 45,
        "completion_rate": 0.68,
        "skills_delta": 2,
        "paths_delta": 1,
        "hours_delta": 12,
        "completion_delta": 0.15
    }
}

# Utility functions
def get_mock_data(data_type: str) -> Any:
    """Get mock data for development"""
    return MOCK_DATA.get(data_type, {})

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return StreamlitConfig.FEATURES.get(feature_name, False)