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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .info-message {
        color: #17a2b8;
        font-weight: bold;
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
    """Main dashboard view"""
    # Check authentication status
    if not session_manager.is_authenticated():
        st.markdown('<h1 class="main-header">🎓 Welcome to EdAgent</h1>', unsafe_allow_html=True)
        st.markdown("""
        ### Your AI-Powered Career Coach
        
        EdAgent helps you:
        - 🎯 Assess your current skills
        - 📚 Create personalized learning paths
        - 💼 Get career coaching advice
        - 🔍 Find the best educational resources
        
        **Please login or register to get started!**
        
        ### New to EdAgent?
        Create an account with your email and password to:
        - Save your progress across sessions
        - Get personalized recommendations
        - Track your learning journey
        - Access all premium features
        """)
        return
    
    # Get current user info
    user_info = session_manager.get_current_user()
    welcome_name = user_info.name or user_info.email.split('@')[0] if user_info else "there"
    st.markdown(f'<h1 class="main-header">🎓 Welcome back, {welcome_name}!</h1>', unsafe_allow_html=True)
    
    # Show profile setup prompt for new users
    user_preferences = session_manager.get_user_preferences()
    if not user_preferences:
        st.info("💡 **Tip:** Complete your profile setup to get personalized recommendations!")
        if st.button("Set Up Profile", key="setup_profile_btn"):
            session_manager.set_ui_state("show_profile_setup", True)
            st.rerun()
    
    st.markdown('<h1 class="main-header">🎓 EdAgent Dashboard</h1>', unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💬 Chat", "📊 Assessments", "🛤️ Learning Paths", 
        "👤 Profile", "🔒 Privacy", "📈 Analytics", "🎤 Interview Prep", "📄 Resume Help"
    ])
    
    with tab1:
        show_chat_interface()
    
    with tab2:
        show_assessments()
    
    with tab3:
        show_learning_paths()
    
    with tab4:
        show_user_profile()
    
    with tab5:
        show_privacy_controls()
    
    with tab6:
        show_analytics()
    
    with tab7:
        render_interview_prep_widget()
    
    with tab8:
        render_resume_analyzer()

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