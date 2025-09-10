"""
EdAgent Streamlit Frontend
A comprehensive web interface for the EdAgent career coaching assistant
"""

import streamlit as st
import requests
import json
import asyncio
import websockets
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_chat import message
import time

# Import custom modules
from streamlit_config import StreamlitConfig, is_feature_enabled
from streamlit_websocket import initialize_websocket, connect_websocket, send_websocket_message, get_websocket_response
from streamlit_components import (
    render_skill_assessment_widget, render_learning_path_builder, 
    render_progress_dashboard, render_resource_recommendations,
    render_interview_prep_widget, render_resume_analyzer, render_career_roadmap
)
from streamlit_api_client import EnhancedEdAgentAPI, safe_parse_datetime
from streamlit_session_manager import SessionManager
from streamlit_auth_components import AuthenticationComponents
from streamlit_privacy_components import PrivacyComponents

# Configuration
API_BASE_URL = StreamlitConfig.API_BASE_URL
WS_URL = StreamlitConfig.WS_URL

# Page configuration
st.set_page_config(
    page_title="EdAgent - AI Career Coach",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import enhanced UI/UX components
from streamlit_responsive_ui import (
    responsive_ui, EnhancedCard, ResponsiveColumns, 
    EnhancedForm, FormValidator
)
from streamlit_enhanced_tables import (
    EnhancedDataTable, ColumnConfig, TableConfig, ColumnType,
    create_user_table, create_assessment_table, create_learning_path_table
)
from streamlit_accessibility import (
    accessibility_framework, make_accessible_button, 
    make_accessible_form, add_skip_links, announce_to_screen_reader
)
from streamlit_enhanced_navigation import (
    navigation_system, create_navigation_item, render_enhanced_tabs,
    render_enhanced_breadcrumb, set_current_navigation_item
)

# Initialize enhanced UI/UX systems
responsive_ui._inject_responsive_css()
accessibility_framework._inject_accessibility_css()

# Add skip links for accessibility
add_skip_links([
    {"target": "main-content", "text": "Skip to main content"},
    {"target": "navigation", "text": "Skip to navigation"},
    {"target": "sidebar", "text": "Skip to sidebar"}
])

# Enhanced CSS with responsive design and accessibility
st.markdown("""
<style>
    /* Main application styles with enhanced responsive design */
    .main-header {
        font-size: clamp(1.5rem, 4vw, 2.5rem);
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        line-height: 1.2;
    }
    
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 1rem;
        background-color: #f8f9fa;
        transition: all 0.3s ease;
    }
    
    .chat-container:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .success-message {
        color: #28a745;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .error-message {
        color: #dc3545;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .info-message {
        color: #17a2b8;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Enhanced button styles */
    .stButton > button {
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        min-height: 44px;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Enhanced form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: border-color 0.2s ease;
        min-height: 44px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #1f77b4;
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .metric-card {
            padding: 1rem;
            margin: 0.25rem 0;
        }
        
        .chat-container {
            height: 300px;
            padding: 0.75rem;
        }
        
        .stButton > button {
            width: 100%;
            padding: 1rem;
        }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .metric-card {
            border: 2px solid #000;
        }
        
        .chat-container {
            border: 2px solid #000;
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
</style>
""", unsafe_allow_html=True)

class EdAgentAPI:
    """API client for EdAgent backend"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if available"""
        headers = {"Content-Type": "application/json"}
        if "access_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        return headers
    
    def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Register a new user with email/password"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json={"email": email, "password": password, "name": name},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("error", {}).get("message", str(e))
            st.error(f"Registration failed: {error_detail}")
            return {}
        except Exception as e:
            st.error(f"Registration failed: {str(e)}")
            return {}
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email/password"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("error", {}).get("message", str(e))
            st.error(f"Login failed: {error_detail}")
            return {}
        except Exception as e:
            st.error(f"Login failed: {str(e)}")
            return {}
    
    def create_session(self, user_id: str) -> Dict[str, Any]:
        """Create a new user session (deprecated - using JWT tokens now)"""
        # This method is kept for backward compatibility but not used
        return {"session_token": st.session_state.get("access_token", "")}
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        try:
            response = self.session.post(
                f"{self.base_url}/users/",
                json=user_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to create user: {str(e)}")
            return {}
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        try:
            response = self.session.get(
                f"{self.base_url}/users/{user_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to get user: {str(e)}")
            return {}
    
    def start_assessment(self, user_id: str, skill_area: str) -> Dict[str, Any]:
        """Start a skill assessment"""
        try:
            response = self.session.post(
                f"{self.base_url}/assessments/start",
                json={"user_id": user_id, "skill_area": skill_area},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to start assessment: {str(e)}")
            return {}
    
    def create_learning_path(self, user_id: str, goal: str) -> Dict[str, Any]:
        """Create a learning path"""
        try:
            response = self.session.post(
                f"{self.base_url}/learning/paths",
                json={"user_id": user_id, "goal": goal},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to create learning path: {str(e)}")
            return {}
    
    def get_user_learning_paths(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning paths"""
        try:
            response = self.session.get(
                f"{self.base_url}/learning/paths/user/{user_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to get learning paths: {str(e)}")
            return {}
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data"""
        try:
            response = self.session.post(
                f"{self.base_url}/privacy/export",
                json={"include_sensitive": False, "format": "json"},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to export data: {str(e)}")
            return {}
    
    def get_privacy_settings(self, user_id: str) -> Dict[str, Any]:
        """Get privacy settings"""
        try:
            response = self.session.get(
                f"{self.base_url}/privacy/settings",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to get privacy settings: {str(e)}")
            return {}
    
    def send_chat_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Send a chat message and get AI response"""
        try:
            response = self.session.post(
                f"{self.base_url}/conversations/message",
                json={"user_id": user_id, "message": message},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to send chat message: {str(e)}")
            return {"message": "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again later."}

# Initialize enhanced components
session_manager = SessionManager()
api = EnhancedEdAgentAPI(API_BASE_URL, session_manager)
auth_components = AuthenticationComponents(api, session_manager)
privacy_components = PrivacyComponents(api, session_manager)

def initialize_session_state():
    """Initialize session state variables"""
    # Load session state from session manager
    session_manager.load_session_state()
    
    # Initialize chat messages if not exists
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "current_assessment" not in st.session_state:
        st.session_state.current_assessment = None
    if "learning_paths" not in st.session_state:
        st.session_state.learning_paths = []
    
    # Initialize user profile and other session variables
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None
    if "conversation_loaded" not in st.session_state:
        st.session_state.conversation_loaded = False
    if "conversation_page" not in st.session_state:
        st.session_state.conversation_page = 0
    if "ws_connection_status" not in st.session_state:
        st.session_state.ws_connection_status = "disconnected"
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False

def authenticate_user():
    """Handle user authentication with enhanced components"""
    return auth_components.render_authentication_interface()

def show_profile_setup():
    """Show enhanced profile setup wizard for new users"""
    if session_manager.get_ui_state("show_profile_setup", False):
        from streamlit_user_profile_components import render_profile_setup_wizard
        render_profile_setup_wizard(api, session_manager)

def main_dashboard():
    """Enhanced main dashboard view with responsive design and accessibility"""
    
    # Add main content anchor for skip links
    st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)
    
    # Check authentication status
    if not session_manager.is_authenticated():
        with EnhancedCard(title="Welcome to EdAgent", icon="🎓", elevated=True):
            st.markdown("""
            ### Your AI-Powered Career Coach
            
            EdAgent helps you:
            - 🎯 Assess your current skills
            - 📚 Create personalized learning paths
            - 💼 Get career coaching advice
            - 🔍 Find the best educational resources
            
            **Please login or register to get started!**
            """)
            
            with ResponsiveColumns(2) as cols:
                with cols[0]:
                    st.markdown("""
                    ### New to EdAgent?
                    Create an account with your email and password to:
                    - Save your progress across sessions
                    - Get personalized recommendations
                    - Track your learning journey
                    - Access all premium features
                    """)
                
                with cols[1]:
                    st.markdown("""
                    ### Returning User?
                    Log in to continue your learning journey and access:
                    - Your conversation history
                    - Saved learning paths
                    - Assessment results
                    - Personal analytics
                    """)
        return
    
    # Get current user info
    user_info = session_manager.get_current_user()
    welcome_name = user_info.name or user_info.email.split('@')[0] if user_info else "there"
    
    # Enhanced welcome header with responsive design
    st.markdown(f'<h1 class="main-header">🎓 Welcome back, {welcome_name}!</h1>', unsafe_allow_html=True)
    
    # Show profile setup prompt for new users
    user_preferences = session_manager.get_user_preferences()
    if not user_preferences:
        with EnhancedCard(title="Complete Your Profile", icon="💡", compact=True):
            st.info("Complete your profile setup to get personalized recommendations!")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if make_accessible_button("Set Up Profile", key="setup_profile_btn"):
                    session_manager.set_ui_state("show_profile_setup", True)
                    announce_to_screen_reader("Profile setup started", "assertive")
                    st.rerun()
    
    # Enhanced navigation with breadcrumbs
    render_enhanced_breadcrumb()
    
    # Create enhanced navigation items
    nav_items = [
        create_navigation_item("chat", "Chat", "💬", description="AI-powered conversations"),
        create_navigation_item("assessments", "Assessments", "📊", description="Skill evaluations"),
        create_navigation_item("learning_paths", "Learning Paths", "🛤️", description="Personalized learning"),
        create_navigation_item("profile", "Profile", "👤", description="User settings"),
        create_navigation_item("privacy", "Privacy", "🔒", description="Data controls"),
        create_navigation_item("analytics", "Analytics", "📈", description="Progress tracking"),
        create_navigation_item("interview_prep", "Interview Prep", "🎤", description="Interview practice"),
        create_navigation_item("resume_help", "Resume Help", "📄", description="Resume optimization")
    ]
    
    # Get current tab from session state or default to chat
    current_tab = st.session_state.get("current_tab", "chat")
    
    # Render enhanced tabs with accessibility
    st.markdown('<div id="navigation"></div>', unsafe_allow_html=True)
    
    # Use Streamlit's native tabs but with enhanced styling
    tab_labels = [f"{item.icon} {item.label}" for item in nav_items]
    tabs = st.tabs(tab_labels)
    
    # Map tabs to functions
    tab_functions = [
        show_enhanced_chat_interface,
        show_enhanced_assessments,
        show_enhanced_learning_paths,
        show_enhanced_user_profile,
        show_enhanced_privacy_controls,
        show_enhanced_analytics,
        show_enhanced_interview_prep,
        show_enhanced_resume_help
    ]
    
    # Render tab content with enhanced components
    for i, (tab, func) in enumerate(zip(tabs, tab_functions)):
        with tab:
            # Set current navigation item
            set_current_navigation_item(nav_items[i].key)
            
            # Add loading animation
            with st.container():
                st.markdown('<div class="nav-content fade-enter-active">', unsafe_allow_html=True)
                func()
                st.markdown('</div>', unsafe_allow_html=True)

def show_enhanced_chat_interface():
    """Enhanced chat interface with responsive design and accessibility"""
    
    with EnhancedCard(title="Chat with EdAgent", icon="💬"):
        # Check authentication
        if not session_manager.is_authenticated():
            st.warning("🔐 Please log in to use the chat feature.")
            return
        
        # Import enhanced error handling components
        from streamlit_error_handler import error_context
        from streamlit_loading_components import show_loading, LoadingStyle
        from streamlit_connectivity_monitor import require_online_connection
        
        # Check connectivity for chat feature
        if not require_online_connection("chat"):
            return
        
        user_info = session_manager.get_current_user()
        
        # Load conversation history with enhanced error handling
        if not st.session_state.conversation_loaded:
            with show_loading("load_conversation", "Loading conversation history...", LoadingStyle.SPINNER):
                try:
                    history = asyncio.run(api.get_conversation_history(user_info.user_id, limit=50))
                    if history:
                        # Convert API history to chat messages format
                        st.session_state.chat_messages = []
                        for msg in history:
                            st.session_state.chat_messages.append({
                                "role": msg.get("role", "assistant"),
                                "content": msg.get("content", ""),
                                "timestamp": safe_parse_datetime(msg.get("timestamp")) or datetime.now(),
                                "metadata": msg.get("metadata", {})
                            })
                        st.success(f"✅ Loaded {len(history)} previous messages")
                        announce_to_screen_reader(f"Loaded {len(history)} previous messages", "polite")
                    else:
                        # Initialize with welcome message if no history
                        st.session_state.chat_messages = [{
                            "role": "assistant",
                            "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
                            "timestamp": datetime.now(),
                            "metadata": {}
                        }]
                    st.session_state.conversation_loaded = True
                except Exception as e:
                    # Enhanced error handling will show user-friendly message
                    # Fallback to empty conversation
                    st.session_state.chat_messages = [{
                        "role": "assistant",
                        "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
                        "timestamp": datetime.now(),
                        "metadata": {}
                    }]
                    st.session_state.conversation_loaded = True
        
        # Enhanced chat controls with responsive design
        with ResponsiveColumns([2, 1, 1]) as cols:
            with cols[0]:
                # Connection status indicator
                status_colors = {
                    "connected": "🟢",
                    "connecting": "🟡", 
                    "disconnected": "🔴",
                    "error": "🔴"
                }
                status_text = {
                    "connected": "Real-time chat active",
                    "connecting": "Connecting...",
                    "disconnected": "Using standard chat",
                    "error": "Connection failed"
                }
                
                st.caption(f"{status_colors.get(st.session_state.ws_connection_status, '🔴')} {status_text.get(st.session_state.ws_connection_status, 'Unknown')}")
            
            with cols[1]:
                if make_accessible_button("🔗 Connect WebSocket", key="connect_ws"):
                    st.session_state.ws_connection_status = "connecting"
                    try:
                        if connect_websocket(user_info.user_id, session_manager.get_auth_token()):
                            st.session_state.ws_connection_status = "connected"
                            st.success("🔗 Connected to real-time chat!")
                            announce_to_screen_reader("Connected to real-time chat", "assertive")
                        else:
                            st.session_state.ws_connection_status = "error"
                            st.error("Failed to connect WebSocket")
                    except Exception as e:
                        st.session_state.ws_connection_status = "error"
                        st.error(f"WebSocket connection error: {str(e)}")
                    st.rerun()
            
            with cols[2]:
                if make_accessible_button("🗑️ Clear History", key="clear_history"):
                    if st.session_state.get("confirm_clear", False):
                        with show_loading("clear_history", "Clearing conversation history...", LoadingStyle.SPINNER):
                            try:
                                success = asyncio.run(api.clear_conversation_history(user_info.user_id))
                                if success:
                                    st.session_state.chat_messages = [{
                                        "role": "assistant",
                                        "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
                                        "timestamp": datetime.now(),
                                        "metadata": {}
                                    }]
                                    st.success("✅ Conversation history cleared")
                                    announce_to_screen_reader("Conversation history cleared", "assertive")
                                else:
                                    st.error("Failed to clear conversation history")
                            except Exception as e:
                                st.error(f"Error clearing history: {str(e)}")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear = True
                        st.warning("⚠️ Click again to confirm clearing all conversation history")
                        st.rerun()
        
        # Enhanced chat display with accessibility
        render_enhanced_chat_messages()
        
        # Enhanced chat input with validation
        render_enhanced_chat_input(user_info)
        
        # Enhanced quick actions with responsive grid
        render_enhanced_quick_actions()

def show_chat_interface():
    """Enhanced chat interface with comprehensive error handling and loading states"""
    st.header("💬 Chat with EdAgent")
    
    # Import enhanced error handling components
    from streamlit_error_handler import error_context
    from streamlit_loading_components import show_loading, LoadingStyle
    from streamlit_connectivity_monitor import require_online_connection
    
    # Check authentication
    if not session_manager.is_authenticated():
        st.warning("🔐 Please log in to use the chat feature.")
        return
    
    # Check connectivity for chat feature
    if not require_online_connection("chat"):
        return
    
    user_info = session_manager.get_current_user()
    
    # Load conversation history with enhanced error handling
    if not st.session_state.conversation_loaded:
        with error_context("load_conversation_history", loading_message="Loading conversation history..."):
            try:
                history = asyncio.run(api.get_conversation_history(user_info.user_id, limit=50))
                if history:
                    # Convert API history to chat messages format
                    st.session_state.chat_messages = []
                    for msg in history:
                        st.session_state.chat_messages.append({
                            "role": msg.get("role", "assistant"),
                            "content": msg.get("content", ""),
                            "timestamp": safe_parse_datetime(msg.get("timestamp")) or datetime.now(),
                            "metadata": msg.get("metadata", {})
                        })
                    st.success(f"✅ Loaded {len(history)} previous messages")
                else:
                    # Initialize with welcome message if no history
                    st.session_state.chat_messages = [{
                        "role": "assistant",
                        "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
                        "timestamp": datetime.now(),
                        "metadata": {}
                    }]
                st.session_state.conversation_loaded = True
            except Exception as e:
                # Enhanced error handling will show user-friendly message
                # Fallback to empty conversation
                st.session_state.chat_messages = [{
                    "role": "assistant",
                    "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
                    "timestamp": datetime.now(),
                    "metadata": {}
                }]
                st.session_state.conversation_loaded = True
    
    # WebSocket connection management
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Connection status indicator
        status_colors = {
            "connected": "🟢",
            "connecting": "🟡", 
            "disconnected": "🔴",
            "error": "🔴"
        }
        status_text = {
            "connected": "Real-time chat active",
            "connecting": "Connecting...",
            "disconnected": "Using standard chat",
            "error": "Connection failed"
        }
        
        st.caption(f"{status_colors.get(st.session_state.ws_connection_status, '🔴')} {status_text.get(st.session_state.ws_connection_status, 'Unknown')}")
    
    with col2:
        if st.button("🔗 Connect WebSocket", key="connect_ws"):
            st.session_state.ws_connection_status = "connecting"
            try:
                if connect_websocket(user_info.user_id, session_manager.get_auth_token()):
                    st.session_state.ws_connection_status = "connected"
                    st.success("🔗 Connected to real-time chat!")
                else:
                    st.session_state.ws_connection_status = "error"
                    st.error("Failed to connect WebSocket")
            except Exception as e:
                st.session_state.ws_connection_status = "error"
                st.error(f"WebSocket connection error: {str(e)}")
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear History", key="clear_history"):
            if st.session_state.get("confirm_clear", False):
                try:
                    success = asyncio.run(api.clear_conversation_history(user_info.user_id))
                    if success:
                        st.session_state.chat_messages = [{
                            "role": "assistant",
                            "content": "Hello! I'm EdAgent, your AI career coach. How can I help you today?",
                            "timestamp": datetime.now(),
                            "metadata": {}
                        }]
                        st.success("✅ Conversation history cleared")
                    else:
                        st.error("Failed to clear conversation history")
                except Exception as e:
                    st.error(f"Error clearing history: {str(e)}")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ Click again to confirm clearing all conversation history")
                st.rerun()
    
    # Chat container with enhanced styling and pagination
    chat_container = st.container()
    
    with chat_container:
        # Pagination controls for large conversation histories
        total_messages = len(st.session_state.chat_messages)
        messages_per_page = 20
        total_pages = max(1, (total_messages + messages_per_page - 1) // messages_per_page)
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.conversation_page == 0):
                    st.session_state.conversation_page = max(0, st.session_state.conversation_page - 1)
                    st.rerun()
            
            with col2:
                st.write(f"Page {st.session_state.conversation_page + 1} of {total_pages}")
            
            with col3:
                if st.button("Next ➡️", disabled=st.session_state.conversation_page >= total_pages - 1):
                    st.session_state.conversation_page = min(total_pages - 1, st.session_state.conversation_page + 1)
                    st.rerun()
        
        # Calculate message range for current page
        start_idx = st.session_state.conversation_page * messages_per_page
        end_idx = min(start_idx + messages_per_page, total_messages)
        
        # Display chat messages with enhanced formatting
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for i in range(start_idx, end_idx):
            msg = st.session_state.chat_messages[i]
            
            # Enhanced message display with metadata
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
                    st.caption(f"🕒 {msg['timestamp'].strftime('%H:%M:%S')}")
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
                    
                    # Display content recommendations if available
                    metadata = msg.get("metadata", {})
                    if metadata.get("content_recommendations"):
                        with st.expander("📚 Recommended Resources"):
                            for rec in metadata["content_recommendations"][:3]:  # Show top 3
                                st.write(f"• **{rec.get('title', 'Resource')}** - {rec.get('description', 'No description')}")
                                if rec.get('url'):
                                    st.markdown(f"  [View Resource]({rec['url']})")
                    
                    # Display follow-up questions if available
                    if metadata.get("follow_up_questions"):
                        st.write("**Suggested follow-up questions:**")
                        for j, question in enumerate(metadata["follow_up_questions"][:3]):
                            if st.button(f"💭 {question}", key=f"followup_{i}_{j}"):
                                # Add follow-up question as user message
                                st.session_state.chat_messages.append({
                                    "role": "user",
                                    "content": question,
                                    "timestamp": datetime.now(),
                                    "metadata": {"type": "follow_up"}
                                })
                                st.rerun()
                    
                    # Display suggested actions if available
                    if metadata.get("suggested_actions"):
                        st.write("**Suggested actions:**")
                        for action in metadata["suggested_actions"][:2]:
                            st.write(f"• {action}")
                    
                    st.caption(f"🕒 {msg['timestamp'].strftime('%H:%M:%S')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced chat input with loading states
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message immediately
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now(),
            "metadata": {}
        }
        st.session_state.chat_messages.append(user_message)
        
        # Enhanced message sending with comprehensive error handling
        with error_context("send_chat_message", loading_message="EdAgent is thinking..."):
            try:
                # Try WebSocket first if connected
                if st.session_state.ws_connection_status == "connected":
                    try:
                        success = send_websocket_message(user_input)
                        if success:
                            # Wait for WebSocket response (simplified)
                            response = get_websocket_response()
                            if response:
                                response_content = response.get("content", "I received your message via WebSocket!")
                                response_metadata = response.get("metadata", {})
                            else:
                                # Fallback to HTTP API with enhanced error handling
                                chat_response = asyncio.run(api.send_message(user_info.user_id, user_input))
                                response_content = chat_response.message
                                response_metadata = {
                                    "content_recommendations": chat_response.content_recommendations,
                                    "follow_up_questions": chat_response.follow_up_questions,
                                    "suggested_actions": chat_response.suggested_actions,
                                    "confidence_score": chat_response.confidence_score
                                }
                        else:
                            raise Exception("WebSocket send failed")
                    except Exception as ws_error:
                        st.warning(f"WebSocket failed, using HTTP API: {str(ws_error)}")
                        st.session_state.ws_connection_status = "error"
                        # Fallback to HTTP API with enhanced error handling
                        chat_response = asyncio.run(api.send_message(user_info.user_id, user_input))
                        response_content = chat_response.message
                        response_metadata = {
                            "content_recommendations": chat_response.content_recommendations,
                            "follow_up_questions": chat_response.follow_up_questions,
                            "suggested_actions": chat_response.suggested_actions,
                            "confidence_score": chat_response.confidence_score
                        }
                else:
                    # Use HTTP API with enhanced error handling
                    chat_response = asyncio.run(api.send_message(user_info.user_id, user_input))
                    response_content = chat_response.message
                    response_metadata = {
                        "content_recommendations": chat_response.content_recommendations,
                        "follow_up_questions": chat_response.follow_up_questions,
                        "suggested_actions": chat_response.suggested_actions,
                        "confidence_score": chat_response.confidence_score
                    }
                
                # Add AI response
                ai_message = {
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.now(),
                    "metadata": response_metadata
                }
                st.session_state.chat_messages.append(ai_message)
                
            except Exception as e:
                # Enhanced error handling will display user-friendly messages
                # Add fallback message to chat
                error_message = {
                    "role": "assistant",
                    "content": "I'm sorry, I'm having trouble connecting right now. Please try again later.",
                    "timestamp": datetime.now(),
                    "metadata": {"error": True}
                }
                st.session_state.chat_messages.append(error_message)
        
        st.rerun()
    
    # Enhanced quick action buttons with context
    st.subheader("Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 Start Assessment", key="quick_assessment_btn"):
            add_enhanced_chat_message("assistant", 
                "Let's start a skill assessment! What area would you like to assess?",
                metadata={
                    "suggested_actions": ["Choose from: Python, JavaScript, Data Science, Machine Learning"],
                    "follow_up_questions": ["What's your current experience level?", "Any specific skills you want to focus on?"]
                })
            st.rerun()
    
    with col2:
        if st.button("📚 Create Learning Path", key="quick_learning_btn"):
            add_enhanced_chat_message("assistant", 
                "I'll help you create a personalized learning path! What's your career goal?",
                metadata={
                    "suggested_actions": ["Be specific about your target role", "Mention your timeline"],
                    "follow_up_questions": ["What's your current skill level?", "How much time can you dedicate per week?"]
                })
            st.rerun()
    
    with col3:
        if st.button("💼 Resume Help", key="quick_resume_btn"):
            add_enhanced_chat_message("assistant", 
                "I can help improve your resume! Please share your current resume or describe your experience.",
                metadata={
                    "suggested_actions": ["Upload your resume file", "Describe your target role"],
                    "follow_up_questions": ["What industry are you targeting?", "Any specific concerns about your resume?"]
                })
            st.rerun()
    
    with col4:
        if st.button("🎤 Interview Prep", key="quick_interview_btn"):
            add_enhanced_chat_message("assistant", 
                "Let's prepare for your interviews! What type of role are you interviewing for?",
                metadata={
                    "suggested_actions": ["Specify the role and company", "Mention interview format (technical, behavioral, etc.)"],
                    "follow_up_questions": ["When is your interview?", "What are you most nervous about?"]
                })
            st.rerun()
    
    # Conversation context management
    st.divider()
    with st.expander("🔧 Conversation Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export Conversation", key="export_conv"):
                try:
                    # Create exportable conversation data
                    export_data = {
                        "user_id": user_info.user_id,
                        "export_date": datetime.now().isoformat(),
                        "messages": st.session_state.chat_messages
                    }
                    
                    # Convert to JSON for download
                    json_str = json.dumps(export_data, indent=2, default=str)
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_str,
                        file_name=f"edagent_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        with col2:
            if st.button("🔄 Refresh History", key="refresh_history"):
                st.session_state.conversation_loaded = False
                st.rerun()


def add_enhanced_chat_message(role: str, content: str, metadata: Dict[str, Any] = None):
    """Add an enhanced message to the chat history with metadata"""
    if metadata is None:
        metadata = {}
    
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "metadata": metadata
    })



def add_chat_message(role: str, content: str):
    """Add a message to the chat history"""
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })

def show_assessments():
    """Comprehensive skill assessments interface with full API integration"""
    from streamlit_assessment_components import render_assessment_dashboard
    
    # Render the complete assessment dashboard
    render_assessment_dashboard(api, session_manager)

def show_learning_paths():
    """Enhanced learning paths interface with comprehensive management system"""
    # Import the new learning path management system
    from streamlit_learning_path_components import render_learning_path_management_system
    
    # Render the complete learning path management system
    render_learning_path_management_system(api, session_manager)

def show_user_profile():
    """Comprehensive user profile management using UserProfileManager"""
    from streamlit_user_profile_components import render_user_profile_dashboard
    render_user_profile_dashboard(api, session_manager)

def show_privacy_controls():
    """Enhanced privacy and data management using PrivacyComponents"""
    privacy_components.render_privacy_dashboard()

def show_analytics():
    """Analytics and progress tracking dashboard"""
    from streamlit_analytics_components import render_analytics_dashboard
    render_analytics_dashboard(api, session_manager)

def main():
    """Main application entry point"""
    initialize_session_state()
    
    # Handle profile setup for new users
    if st.session_state.get("show_profile_setup", False):
        show_profile_setup()
        return
    
    # Sidebar authentication
    authenticate_user()
    
    # Main dashboard
    main_dashboard()

if __name__ == "__main__":
    main()
def render_enhanced_chat_messages():
    """Render chat messages with enhanced accessibility and responsive design"""
    
    # Chat container with enhanced styling and pagination
    total_messages = len(st.session_state.chat_messages)
    messages_per_page = 20
    total_pages = max(1, (total_messages + messages_per_page - 1) // messages_per_page)
    
    if total_pages > 1:
        with ResponsiveColumns([1, 2, 1]) as cols:
            with cols[0]:
                if make_accessible_button("⬅️ Previous", disabled=st.session_state.conversation_page == 0, key="prev_page"):
                    st.session_state.conversation_page = max(0, st.session_state.conversation_page - 1)
                    st.rerun()
            
            with cols[1]:
                st.markdown(f"<div style='text-align: center; padding: 0.5rem;'>Page {st.session_state.conversation_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
            
            with cols[2]:
                if make_accessible_button("Next ➡️", disabled=st.session_state.conversation_page >= total_pages - 1, key="next_page"):
                    st.session_state.conversation_page = min(total_pages - 1, st.session_state.conversation_page + 1)
                    st.rerun()
    
    # Calculate message range for current page
    start_idx = st.session_state.conversation_page * messages_per_page
    end_idx = min(start_idx + messages_per_page, total_messages)
    
    # Display chat messages with enhanced formatting
    st.markdown('<div class="chat-container" role="log" aria-label="Chat conversation">', unsafe_allow_html=True)
    
    for i in range(start_idx, end_idx):
        msg = st.session_state.chat_messages[i]
        
        # Enhanced message display with metadata
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
                st.caption(f"🕒 {msg['timestamp'].strftime('%H:%M:%S')}")
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])
                
                # Display content recommendations if available
                metadata = msg.get("metadata", {})
                if metadata.get("content_recommendations"):
                    with st.expander("📚 Recommended Resources"):
                        for rec in metadata["content_recommendations"][:3]:  # Show top 3
                            with EnhancedCard(compact=True):
                                st.write(f"**{rec.get('title', 'Resource')}**")
                                st.write(rec.get('description', 'No description'))
                                if rec.get('url'):
                                    st.markdown(f"[View Resource]({rec['url']})")
                
                # Display follow-up questions if available
                if metadata.get("follow_up_questions"):
                    st.write("**Suggested follow-up questions:**")
                    for j, question in enumerate(metadata["follow_up_questions"][:3]):
                        if make_accessible_button(f"💭 {question}", key=f"followup_{i}_{j}"):
                            # Add follow-up question as user message
                            st.session_state.chat_messages.append({
                                "role": "user",
                                "content": question,
                                "timestamp": datetime.now(),
                                "metadata": {"type": "follow_up"}
                            })
                            announce_to_screen_reader(f"Selected follow-up question: {question}", "polite")
                            st.rerun()
                
                # Display suggested actions if available
                if metadata.get("suggested_actions"):
                    st.write("**Suggested actions:**")
                    for action in metadata["suggested_actions"][:2]:
                        st.write(f"• {action}")
                
                st.caption(f"🕒 {msg['timestamp'].strftime('%H:%M:%S')}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_enhanced_chat_input(user_info):
    """Render enhanced chat input with validation and accessibility"""
    
    # Enhanced chat input with loading states
    user_input = st.chat_input("Type your message here...", key="chat_input")
    
    if user_input:
        # Validate input
        if len(user_input.strip()) == 0:
            st.error("Please enter a message")
            return
        
        if len(user_input) > 2000:
            st.error("Message is too long. Please keep it under 2000 characters.")
            return
        
        # Add user message immediately
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now(),
            "metadata": {}
        }
        st.session_state.chat_messages.append(user_message)
        
        # Enhanced message sending with comprehensive error handling
        from streamlit_loading_components import show_loading, LoadingStyle
        
        with show_loading("send_message", "EdAgent is thinking...", LoadingStyle.SPINNER):
            try:
                # Try WebSocket first if connected
                if st.session_state.ws_connection_status == "connected":
                    try:
                        success = send_websocket_message(user_input)
                        if success:
                            # Wait for WebSocket response (simplified)
                            response = get_websocket_response()
                            if response:
                                response_content = response.get("content", "I received your message via WebSocket!")
                                response_metadata = response.get("metadata", {})
                            else:
                                # Fallback to HTTP API
                                chat_response = asyncio.run(api.send_message(user_info.user_id, user_input))
                                response_content = chat_response.message
                                response_metadata = {
                                    "content_recommendations": chat_response.content_recommendations,
                                    "follow_up_questions": chat_response.follow_up_questions,
                                    "suggested_actions": chat_response.suggested_actions,
                                    "confidence_score": chat_response.confidence_score
                                }
                        else:
                            raise Exception("WebSocket send failed")
                    except Exception as ws_error:
                        st.warning(f"WebSocket failed, using HTTP API")
                        st.session_state.ws_connection_status = "error"
                        # Fallback to HTTP API
                        chat_response = asyncio.run(api.send_message(user_info.user_id, user_input))
                        response_content = chat_response.message
                        response_metadata = {
                            "content_recommendations": chat_response.content_recommendations,
                            "follow_up_questions": chat_response.follow_up_questions,
                            "suggested_actions": chat_response.suggested_actions,
                            "confidence_score": chat_response.confidence_score
                        }
                else:
                    # Use HTTP API
                    chat_response = asyncio.run(api.send_message(user_info.user_id, user_input))
                    response_content = chat_response.message
                    response_metadata = {
                        "content_recommendations": chat_response.content_recommendations,
                        "follow_up_questions": chat_response.follow_up_questions,
                        "suggested_actions": chat_response.suggested_actions,
                        "confidence_score": chat_response.confidence_score
                    }
                
                # Add AI response
                ai_message = {
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.now(),
                    "metadata": response_metadata
                }
                st.session_state.chat_messages.append(ai_message)
                announce_to_screen_reader("EdAgent has responded", "polite")
                
            except Exception as e:
                # Add fallback message to chat
                error_message = {
                    "role": "assistant",
                    "content": "I'm sorry, I'm having trouble connecting right now. Please try again later.",
                    "timestamp": datetime.now(),
                    "metadata": {"error": True}
                }
                st.session_state.chat_messages.append(error_message)
                announce_to_screen_reader("Error occurred while sending message", "assertive")
        
        st.rerun()


def render_enhanced_quick_actions():
    """Render enhanced quick action buttons with responsive grid"""
    
    st.subheader("Quick Actions")
    
    with ResponsiveColumns(4) as cols:
        with cols[0]:
            if make_accessible_button("🎯 Start Assessment", key="quick_assessment_btn"):
                add_enhanced_chat_message("assistant", 
                    "Let's start a skill assessment! What area would you like to assess?",
                    metadata={
                        "suggested_actions": ["Choose from: Python, JavaScript, Data Science, Machine Learning"],
                        "follow_up_questions": ["What's your current experience level?", "Any specific skills you want to focus on?"]
                    })
                announce_to_screen_reader("Started skill assessment conversation", "polite")
                st.rerun()
        
        with cols[1]:
            if make_accessible_button("📚 Create Learning Path", key="quick_learning_btn"):
                add_enhanced_chat_message("assistant", 
                    "I'll help you create a personalized learning path! What's your career goal?",
                    metadata={
                        "suggested_actions": ["Be specific about your target role", "Mention your timeline"],
                        "follow_up_questions": ["What's your current skill level?", "How much time can you dedicate per week?"]
                    })
                announce_to_screen_reader("Started learning path creation", "polite")
                st.rerun()
        
        with cols[2]:
            if make_accessible_button("💼 Resume Help", key="quick_resume_btn"):
                add_enhanced_chat_message("assistant", 
                    "I can help improve your resume! Please share your current resume or describe your experience.",
                    metadata={
                        "suggested_actions": ["Upload your resume file", "Describe your target role"],
                        "follow_up_questions": ["What industry are you targeting?", "Any specific concerns about your resume?"]
                    })
                announce_to_screen_reader("Started resume help conversation", "polite")
                st.rerun()
        
        with cols[3]:
            if make_accessible_button("🎤 Interview Prep", key="quick_interview_btn"):
                add_enhanced_chat_message("assistant", 
                    "Let's prepare for your interviews! What type of role are you interviewing for?",
                    metadata={
                        "suggested_actions": ["Specify the role and company", "Mention interview format (technical, behavioral, etc.)"],
                        "follow_up_questions": ["When is your interview?", "What are you most nervous about?"]
                    })
                announce_to_screen_reader("Started interview preparation", "polite")
                st.rerun()


def add_enhanced_chat_message(role: str, content: str, metadata: dict = None):
    """Add a message to the chat with enhanced metadata"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "metadata": metadata or {}
    }
    st.session_state.chat_messages.append(message)


def show_enhanced_assessments():
    """Enhanced assessments interface with interactive tables and responsive design"""
    
    with EnhancedCard(title="Skill Assessments", icon="📊"):
        st.markdown("Track your skill development with comprehensive assessments.")
        
        # Mock assessment data for demonstration
        assessment_data = pd.DataFrame({
            'id': ['assess_1', 'assess_2', 'assess_3', 'assess_4'],
            'skill_area': ['Python Programming', 'Data Science', 'Web Development', 'Machine Learning'],
            'score': [0.85, 0.92, 0.78, 0.88],
            'status': ['completed', 'completed', 'in_progress', 'completed'],
            'completed_at': pd.date_range('2024-01-01', periods=4, freq='7D'),
            'duration': ['25 min', '35 min', '20 min', '40 min']
        })
        
        # Create enhanced assessment table
        assessment_table = create_assessment_table(assessment_data, "assessments_table")
        
        # Render the table
        table_result = assessment_table.render()
        
        # Show selected assessments
        if table_result["selected_rows"]:
            selected_data = assessment_table.get_selected_data()
            
            with EnhancedCard(title="Selected Assessments", compact=True):
                st.write(f"**{len(selected_data)} assessments selected**")
                
                with ResponsiveColumns(3) as cols:
                    with cols[0]:
                        if make_accessible_button("📊 View Details", key="view_assessment_details"):
                            st.info("Assessment details would be displayed here")
                    
                    with cols[1]:
                        if make_accessible_button("🔄 Retake Assessment", key="retake_assessment"):
                            st.info("Assessment retake would be initiated here")
                    
                    with cols[2]:
                        if make_accessible_button("📈 Compare Results", key="compare_assessments"):
                            st.info("Assessment comparison would be shown here")
        
        # Assessment creation section
        st.divider()
        
        with EnhancedCard(title="Start New Assessment", icon="🎯"):
            with EnhancedForm(title="Assessment Setup") as form:
                skill_area = form.text_input(
                    "Skill Area",
                    "skill_area",
                    placeholder="e.g., Python, JavaScript, Data Science",
                    required=True,
                    help_text="Enter the skill you want to assess"
                )
                
                difficulty = st.selectbox(
                    "Difficulty Level",
                    ["Beginner", "Intermediate", "Advanced"],
                    key="assessment_difficulty"
                )
                
                time_limit = st.slider(
                    "Time Limit (minutes)",
                    min_value=10,
                    max_value=60,
                    value=30,
                    key="assessment_time_limit"
                )
                
                if form.submit_button("Start Assessment"):
                    if form.is_valid():
                        with show_loading("create_assessment", "Creating your assessment...", LoadingStyle.PROGRESS_BAR):
                            # Simulate assessment creation
                            time.sleep(2)
                            st.success(f"✅ Assessment for {skill_area} created successfully!")
                            announce_to_screen_reader(f"Assessment for {skill_area} started", "assertive")
                    else:
                        st.error("Please fix the errors above")


def show_enhanced_learning_paths():
    """Enhanced learning paths interface with interactive management"""
    
    with EnhancedCard(title="Learning Paths", icon="🛤️"):
        st.markdown("Create and manage your personalized learning journeys.")
        
        # Mock learning path data
        learning_path_data = pd.DataFrame({
            'id': ['path_1', 'path_2', 'path_3'],
            'title': ['Python Mastery', 'Data Science Fundamentals', 'Web Development Bootcamp'],
            'progress': [0.75, 0.45, 0.20],
            'difficulty': ['Intermediate', 'Beginner', 'Advanced'],
            'estimated_hours': [40, 60, 80],
            'created_at': pd.date_range('2024-01-01', periods=3, freq='10D'),
            'status': ['active', 'active', 'paused']
        })
        
        # Create enhanced learning path table
        learning_path_table = create_learning_path_table(learning_path_data, "learning_paths_table")
        
        # Render the table
        table_result = learning_path_table.render()
        
        # Learning path management actions
        if table_result["selected_rows"]:
            selected_data = learning_path_table.get_selected_data()
            
            with EnhancedCard(title="Path Management", compact=True):
                with ResponsiveColumns(4) as cols:
                    with cols[0]:
                        if make_accessible_button("▶️ Continue", key="continue_path"):
                            st.success("Continuing selected learning path...")
                    
                    with cols[1]:
                        if make_accessible_button("⏸️ Pause", key="pause_path"):
                            st.info("Learning path paused")
                    
                    with cols[2]:
                        if make_accessible_button("📊 Progress", key="view_progress"):
                            st.info("Progress details would be shown here")
                    
                    with cols[3]:
                        if make_accessible_button("🗑️ Delete", key="delete_path"):
                            st.warning("Path deletion would be confirmed here")


def show_enhanced_user_profile():
    """Enhanced user profile interface with comprehensive form validation"""
    
    with EnhancedCard(title="User Profile", icon="👤"):
        user_info = session_manager.get_current_user()
        
        if not user_info:
            st.error("User information not available")
            return
        
        # Profile information display
        with ResponsiveColumns([1, 2]) as cols:
            with cols[0]:
                st.markdown("### Profile Picture")
                st.image("https://via.placeholder.com/150", width=150)
                
                if make_accessible_button("📷 Change Photo", key="change_photo"):
                    st.info("Photo upload would be implemented here")
            
            with cols[1]:
                with EnhancedForm(title="Profile Information") as form:
                    name = form.text_input(
                        "Full Name",
                        "profile_name",
                        value=user_info.name or "",
                        required=True,
                        help_text="Your display name"
                    )
                    
                    email = form.email_input(
                        "Email Address",
                        "profile_email",
                        value=user_info.email or "",
                        required=True
                    )
                    
                    bio = st.text_area(
                        "Bio",
                        value="",
                        placeholder="Tell us about yourself...",
                        key="profile_bio",
                        help="Optional professional bio"
                    )
                    
                    if form.submit_button("Update Profile"):
                        if form.is_valid():
                            with show_loading("update_profile", "Updating profile...", LoadingStyle.SPINNER):
                                time.sleep(1)
                                st.success("✅ Profile updated successfully!")
                                announce_to_screen_reader("Profile updated successfully", "assertive")


def show_enhanced_privacy_controls():
    """Enhanced privacy controls with comprehensive data management"""
    
    with EnhancedCard(title="Privacy & Data Controls", icon="🔒"):
        st.markdown("Manage your data privacy and control how your information is used.")
        
        # Privacy settings
        with EnhancedCard(title="Privacy Settings", compact=True):
            with ResponsiveColumns(2) as cols:
                with cols[0]:
                    data_sharing = st.checkbox(
                        "Allow data sharing for research",
                        value=False,
                        key="privacy_data_sharing",
                        help="Help improve EdAgent by sharing anonymized usage data"
                    )
                    
                    marketing_emails = st.checkbox(
                        "Receive marketing emails",
                        value=True,
                        key="privacy_marketing",
                        help="Get updates about new features and tips"
                    )
                
                with cols[1]:
                    analytics_tracking = st.checkbox(
                        "Enable analytics tracking",
                        value=True,
                        key="privacy_analytics",
                        help="Track usage to improve your experience"
                    )
                    
                    third_party_integrations = st.checkbox(
                        "Allow third-party integrations",
                        value=False,
                        key="privacy_integrations",
                        help="Enable connections with external services"
                    )
        
        # Data management actions
        with EnhancedCard(title="Data Management", compact=True):
            with ResponsiveColumns(3) as cols:
                with cols[0]:
                    if make_accessible_button("📥 Export Data", key="export_data"):
                        with show_loading("export_data", "Preparing data export...", LoadingStyle.PROGRESS_BAR):
                            time.sleep(2)
                            st.success("✅ Data export ready for download")
                
                with cols[1]:
                    if make_accessible_button("🗑️ Delete Account", key="delete_account"):
                        st.error("⚠️ This action cannot be undone!")
                
                with cols[2]:
                    if make_accessible_button("🔄 Reset Preferences", key="reset_preferences"):
                        st.info("Preferences would be reset to defaults")


def show_enhanced_analytics():
    """Enhanced analytics dashboard with interactive visualizations"""
    
    with EnhancedCard(title="Learning Analytics", icon="📈"):
        st.markdown("Track your progress and analyze your learning journey.")
        
        # Mock analytics data
        progress_data = {
            "skills_assessed": 12,
            "learning_paths": 3,
            "study_hours": 45.5,
            "completion_rate": 0.78
        }
        
        # Key metrics with enhanced cards
        with ResponsiveColumns(4) as cols:
            with cols[0]:
                with EnhancedCard(compact=True):
                    st.metric("Skills Assessed", progress_data["skills_assessed"], delta=2)
            
            with cols[1]:
                with EnhancedCard(compact=True):
                    st.metric("Learning Paths", progress_data["learning_paths"], delta=1)
            
            with cols[2]:
                with EnhancedCard(compact=True):
                    st.metric("Study Hours", f"{progress_data['study_hours']:.1f}", delta=5.2)
            
            with cols[3]:
                with EnhancedCard(compact=True):
                    st.metric("Completion Rate", f"{progress_data['completion_rate']:.1%}", delta="8%")
        
        # Progress visualization
        with ResponsiveColumns(2) as cols:
            with cols[0]:
                with EnhancedCard(title="Skill Progress", compact=True):
                    # Mock skill data for radar chart
                    skills_data = pd.DataFrame({
                        'skill': ['Python', 'JavaScript', 'Data Science', 'Machine Learning', 'Web Dev'],
                        'level': [85, 70, 90, 65, 75]
                    })
                    
                    st.bar_chart(skills_data.set_index('skill'))
            
            with cols[1]:
                with EnhancedCard(title="Learning Timeline", compact=True):
                    # Mock timeline data
                    timeline_data = pd.DataFrame({
                        'date': pd.date_range('2024-01-01', periods=30, freq='D'),
                        'hours': [1 + (i % 7) * 0.5 for i in range(30)]
                    })
                    
                    st.line_chart(timeline_data.set_index('date'))


def show_enhanced_interview_prep():
    """Enhanced interview preparation with interactive practice"""
    
    with EnhancedCard(title="Interview Preparation", icon="🎤"):
        render_interview_prep_widget()


def show_enhanced_resume_help():
    """Enhanced resume help with AI-powered analysis"""
    
    with EnhancedCard(title="Resume Optimization", icon="📄"):
        render_resume_analyzer()