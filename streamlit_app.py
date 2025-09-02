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
from streamlit_config import StreamlitConfig, MOCK_DATA, get_mock_data, is_feature_enabled
from streamlit_websocket import initialize_websocket, connect_websocket, send_websocket_message, get_websocket_response
from streamlit_components import (
    render_skill_assessment_widget, render_learning_path_builder, 
    render_progress_dashboard, render_resource_recommendations,
    render_interview_prep_widget, render_resume_analyzer, render_career_roadmap
)

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

# Initialize API client
api = EdAgentAPI(API_BASE_URL)

def initialize_session_state():
    """Initialize session state variables"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "current_assessment" not in st.session_state:
        st.session_state.current_assessment = None
    if "learning_paths" not in st.session_state:
        st.session_state.learning_paths = []
    if "show_registration" not in st.session_state:
        st.session_state.show_registration = False

def authenticate_user():
    """Handle user authentication with email/password"""
    st.sidebar.header("🔐 Authentication")
    
    if st.session_state.user_id is None:
        # Login/Register tabs
        auth_tab = st.sidebar.radio("Choose action:", ["Login", "Register"])
        
        if auth_tab == "Login":
            with st.sidebar.form("login_form"):
                st.subheader("Login")
                email = st.text_input("Email:", placeholder="your.email@example.com")
                password = st.text_input("Password:", type="password")
                
                login_submitted = st.form_submit_button("Login")
                
                if login_submitted:
                    if email and password:
                        login_result = api.login_user(email, password)
                        if login_result:
                            # Store authentication data
                            st.session_state.access_token = login_result.get("access_token")
                            st.session_state.user_id = login_result.get("user_id")
                            st.session_state.user_email = login_result.get("email")
                            
                            # Try to get user profile
                            user_data = api.get_user(st.session_state.user_id)
                            if user_data:
                                st.session_state.user_profile = user_data.get("user")
                            
                            st.sidebar.success("✅ Logged in successfully!")
                            st.rerun()
                    else:
                        st.sidebar.error("Please enter both email and password")
        
        else:  # Register
            with st.sidebar.form("register_form"):
                st.subheader("Register")
                name = st.text_input("Full Name:", placeholder="John Doe")
                email = st.text_input("Email:", placeholder="your.email@example.com")
                password = st.text_input("Password:", type="password", 
                                       help="Must contain uppercase, lowercase, number, and special character")
                
                # Password strength indicator
                if password:
                    strength_score = 0
                    requirements = []
                    
                    if len(password) >= 8:
                        strength_score += 1
                    else:
                        requirements.append("At least 8 characters")
                    
                    if any(c.isupper() for c in password):
                        strength_score += 1
                    else:
                        requirements.append("One uppercase letter")
                    
                    if any(c.islower() for c in password):
                        strength_score += 1
                    else:
                        requirements.append("One lowercase letter")
                    
                    if any(c.isdigit() for c in password):
                        strength_score += 1
                    else:
                        requirements.append("One number")
                    
                    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                        strength_score += 1
                    else:
                        requirements.append("One special character")
                    
                    # Show strength
                    if strength_score < 3:
                        st.error(f"Weak password. Missing: {', '.join(requirements)}")
                    elif strength_score < 5:
                        st.warning(f"Medium password. Missing: {', '.join(requirements)}")
                    else:
                        st.success("Strong password! ✓")
                confirm_password = st.text_input("Confirm Password:", type="password")
                
                register_submitted = st.form_submit_button("Register")
                
                if register_submitted:
                    if name and email and password and confirm_password:
                        if password != confirm_password:
                            st.sidebar.error("Passwords do not match")
                        else:
                            register_result = api.register_user(email, password, name)
                            if register_result:
                                # Store authentication data
                                st.session_state.access_token = register_result.get("access_token")
                                st.session_state.user_id = register_result.get("user_id")
                                st.session_state.user_email = register_result.get("email")
                                st.session_state.user_name = name
                                
                                st.sidebar.success("✅ Registered and logged in successfully!")
                                st.rerun()
                    else:
                        st.sidebar.error("Please fill in all fields")
    
    else:
        # Show logged in user info
        user_display = st.session_state.user_email or st.session_state.user_name or st.session_state.user_id
        st.sidebar.success(f"👤 Logged in as: {user_display}")
        
        # User menu
        with st.sidebar.expander("Account", expanded=False):
            st.write(f"**Email:** {st.session_state.user_email}")
            st.write(f"**Name:** {st.session_state.user_name}")
            st.write(f"**User ID:** {st.session_state.user_id}")
        
        if st.sidebar.button("Logout", key="logout_btn"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def show_profile_setup():
    """Show profile setup form for new users"""
    if st.session_state.get("show_profile_setup", False):
        st.header("📝 Complete Your Profile")
        st.write("Welcome! Let's set up your learning profile to provide personalized recommendations.")
        
        with st.form("profile_setup_form"):
            st.subheader("Career Goals")
            career_goals = st.text_area(
                "What are your career goals? (one per line)",
                placeholder="e.g.,\nBecome a software developer\nLearn data science\nTransition to tech"
            ).split('\n')
            career_goals = [goal.strip() for goal in career_goals if goal.strip()]
            
            st.subheader("Learning Preferences")
            col1, col2 = st.columns(2)
            
            with col1:
                learning_style = st.selectbox(
                    "Preferred Learning Style:",
                    ["visual", "auditory", "kinesthetic", "reading"]
                )
                
                time_commitment = st.selectbox(
                    "Time Commitment (hours per week):",
                    ["1-5", "5-10", "10-20", "20+"]
                )
                
                budget_preference = st.selectbox(
                    "Budget Preference:",
                    ["free", "low_cost", "moderate", "premium"]
                )
            
            with col2:
                preferred_platforms = st.multiselect(
                    "Preferred Learning Platforms:",
                    ["youtube", "coursera", "udemy", "edx", "khan_academy", "codecademy"]
                )
                
                content_types = st.multiselect(
                    "Preferred Content Types:",
                    ["video", "text", "interactive", "project_based", "quiz"]
                )
                
                difficulty_preference = st.selectbox(
                    "Difficulty Preference:",
                    ["beginner", "intermediate", "advanced", "mixed"]
                )
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Save Profile", type="primary")
            with col2:
                skip = st.form_submit_button("Skip for Now")
            
            if submitted or skip:
                if submitted and career_goals:
                    # Update user profile with preferences
                    preferences = {
                        "career_goals": career_goals,
                        "learning_preferences": {
                            "learning_style": learning_style,
                            "time_commitment": time_commitment,
                            "budget_preference": budget_preference,
                            "preferred_platforms": preferred_platforms,
                            "content_types": content_types,
                            "difficulty_preference": difficulty_preference
                        }
                    }
                    
                    # Store preferences in session state
                    st.session_state.user_preferences = preferences
                    st.success("✅ Profile saved successfully!")
                
                st.session_state.show_profile_setup = False
                st.rerun()

def main_dashboard():
    """Main dashboard view"""
    if st.session_state.user_id is None:
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
    
    # Welcome message for authenticated users
    welcome_name = st.session_state.user_name or st.session_state.user_email.split('@')[0] if st.session_state.user_email else "there"
    st.markdown(f'<h1 class="main-header">🎓 Welcome back, {welcome_name}!</h1>', unsafe_allow_html=True)
    
    # Show profile setup prompt for new users
    if not st.session_state.get("user_preferences") and not StreamlitConfig.USE_MOCK_DATA:
        st.info("💡 **Tip:** Complete your profile setup to get personalized recommendations!")
        if st.button("Set Up Profile", key="setup_profile_btn"):
            st.session_state.show_profile_setup = True
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
    """Chat interface with WebSocket support"""
    st.header("💬 Chat with EdAgent")
    
    # Initialize WebSocket if enabled and user is authenticated
    if is_feature_enabled("websocket_chat") and st.session_state.user_id and st.session_state.access_token:
        if "ws_connected" not in st.session_state:
            st.session_state.ws_connected = False
        
        if not st.session_state.ws_connected:
            if connect_websocket(st.session_state.user_id, st.session_state.access_token):
                st.session_state.ws_connected = True
                st.success("🔗 Connected to real-time chat!")
    
    # Load mock messages if using mock data
    if StreamlitConfig.USE_MOCK_DATA and not st.session_state.chat_messages:
        st.session_state.chat_messages = get_mock_data("chat_messages")
    
    # Chat container with custom styling
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat messages
        for i, msg in enumerate(st.session_state.chat_messages):
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=f"user_{i}")
            else:
                message(msg["content"], is_user=False, key=f"bot_{i}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Try WebSocket first, fallback to mock response
        response_sent = False
        
        if is_feature_enabled("websocket_chat") and st.session_state.get("ws_connected", False):
            if send_websocket_message(user_input):
                with st.spinner("EdAgent is thinking..."):
                    # Wait for WebSocket response
                    for _ in range(10):  # Wait up to 5 seconds
                        time.sleep(0.5)
                        ws_response = get_websocket_response()
                        if ws_response:
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": ws_response.get("content", "I received your message!"),
                                "timestamp": datetime.now()
                            })
                            response_sent = True
                            break
        
        # Fallback to mock response
        if not response_sent:
            with st.spinner("EdAgent is thinking..."):
                time.sleep(1)  # Simulate processing time
                
                # Generate intelligent response based on input
                response = generate_mock_response(user_input)
                
                # Add AI response
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now()
                })
        
        st.rerun()
    
    # Quick action buttons
    st.subheader("Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 Start Assessment"):
            add_chat_message("assistant", "Let's start a skill assessment! What area would you like to assess?")
            st.rerun()
    
    with col2:
        if st.button("📚 Create Learning Path"):
            add_chat_message("assistant", "I'll help you create a learning path! What's your career goal?")
            st.rerun()
    
    with col3:
        if st.button("💼 Resume Help"):
            add_chat_message("assistant", "I can help improve your resume! Please share your current resume or describe your experience.")
            st.rerun()
    
    with col4:
        if st.button("🎤 Interview Prep"):
            add_chat_message("assistant", "Let's prepare for your interviews! What type of role are you interviewing for?")
            st.rerun()

def generate_mock_response(user_input: str) -> str:
    """Generate intelligent mock responses based on user input"""
    user_input_lower = user_input.lower()
    
    # Assessment-related responses
    if any(word in user_input_lower for word in ["assessment", "test", "evaluate", "skill"]):
        return "I'd be happy to help you assess your skills! What area would you like to focus on? For example: programming, data science, marketing, or design? I can create a comprehensive assessment that will help identify your current level and areas for improvement."
    
    # Learning path responses
    elif any(word in user_input_lower for word in ["learning path", "roadmap", "plan", "study"]):
        return "Great! I can create a personalized learning path for you. What's your career goal? For example: 'I want to become a web developer' or 'I want to learn data analysis'. I'll break it down into manageable milestones with specific resources and timelines."
    
    # Resume-related responses
    elif any(word in user_input_lower for word in ["resume", "cv", "job application"]):
        return "I can help you improve your resume! Please share your current resume or tell me about your experience, and I'll provide specific feedback and suggestions. I can help with formatting, content optimization, ATS compatibility, and tailoring for specific roles."
    
    # Interview preparation
    elif any(word in user_input_lower for word in ["interview", "job interview", "preparation"]):
        return "Let's prepare for your interviews! What type of role are you interviewing for? I can help you practice common questions, provide industry-specific guidance, and give you tips for both technical and behavioral interviews."
    
    # Career change
    elif any(word in user_input_lower for word in ["career change", "transition", "switch"]):
        return "Career transitions can be exciting! What field are you looking to move into? I can help you identify transferable skills, create a transition plan, and recommend resources to bridge any skill gaps. What's your current background and target role?"
    
    # Programming/technical
    elif any(word in user_input_lower for word in ["programming", "coding", "developer", "software"]):
        return "Programming is a fantastic skill to develop! Are you interested in web development, mobile apps, data science, or something else? I can recommend learning paths for different programming languages and help you build a portfolio of projects."
    
    # Data science
    elif any(word in user_input_lower for word in ["data science", "machine learning", "ai", "analytics"]):
        return "Data science is a rapidly growing field! What's your background with mathematics, statistics, or programming? I can create a customized learning path that covers Python/R, statistics, machine learning, and practical projects to build your portfolio."
    
    # General career advice
    elif any(word in user_input_lower for word in ["career", "job", "work", "professional"]):
        return "I'm here to help with your career development! Whether you're looking to advance in your current field, change careers, or develop new skills, I can provide personalized guidance. What specific career goals or challenges are you facing?"
    
    # Greeting responses
    elif any(word in user_input_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "Hello! I'm EdAgent, your AI career coach. I'm here to help you achieve your career goals through personalized learning paths, skill assessments, and career guidance. What would you like to work on today?"
    
    # Default response
    else:
        return f"Thanks for your message! I'm here to help with your career development. I can assist with skill assessments, creating learning paths, resume improvement, interview preparation, and career planning. What specific area would you like to focus on?"

def add_chat_message(role: str, content: str):
    """Add a message to the chat history"""
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })

def show_assessments():
    """Skill assessments interface"""
    st.header("📊 Skill Assessments")
    
    # Use the enhanced assessment widget
    render_skill_assessment_widget(api, st.session_state.user_id or "demo_user")
    
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Quick Assessment")
        
        skill_area = st.selectbox(
            "Choose skill area:",
            ["Python Programming", "Web Development", "Data Science", 
             "Machine Learning", "Digital Marketing", "Project Management"]
        )
        
        if st.button("Start Quick Assessment", key="quick_assessment"):
            if st.session_state.user_id:
                result = api.start_assessment(st.session_state.user_id, skill_area.lower())
                if result:
                    st.session_state.current_assessment = result
                    st.success(f"✅ Started {skill_area} assessment!")
                else:
                    st.error("Failed to start assessment")
            else:
                st.info("Please login to start an assessment")
    
    with col2:
        st.subheader("Assessment History")
        
        # Use mock data if available
        if StreamlitConfig.USE_MOCK_DATA:
            assessments = get_mock_data("assessments")
            if assessments:
                assessment_data = {
                    "Assessment": [a["skill_area"] for a in assessments],
                    "Date": [a["date"] for a in assessments],
                    "Score": [a["score"] for a in assessments],
                    "Level": [a["level"] for a in assessments]
                }
            else:
                assessment_data = {
                    "Assessment": ["Python Programming", "Web Development", "Data Science"],
                    "Date": ["2024-01-15", "2024-01-10", "2024-01-05"],
                    "Score": [85, 72, 90],
                    "Level": ["Intermediate", "Beginner", "Advanced"]
                }
        else:
            # Try to get real data
            assessment_data = {
                "Assessment": ["Python Programming", "Web Development", "Data Science"],
                "Date": ["2024-01-15", "2024-01-10", "2024-01-05"],
                "Score": [85, 72, 90],
                "Level": ["Intermediate", "Beginner", "Advanced"]
            }
        
        df = pd.DataFrame(assessment_data)
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        fig = px.bar(df, x="Assessment", y="Score", color="Level",
                    title="Assessment Scores", color_discrete_map={
                        "Beginner": "#ff7f0e",
                        "Intermediate": "#2ca02c", 
                        "Advanced": "#1f77b4"
                    })
        st.plotly_chart(fig, use_container_width=True)

def show_learning_paths():
    """Learning paths interface"""
    st.header("🛤️ Learning Paths")
    
    # Use the enhanced learning path builder
    render_learning_path_builder(api, st.session_state.user_id or "demo_user")
    
    st.divider()
    
    # Career roadmap visualization
    render_career_roadmap()
    
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Quick Path Creation")
        
        goal = st.text_area(
            "Describe your learning goal:",
            placeholder="e.g., I want to become a full-stack web developer"
        )
        
        if st.button("Create Learning Path", key="create_path"):
            if goal:
                if st.session_state.user_id:
                    result = api.create_learning_path(st.session_state.user_id, goal)
                    if result:
                        st.success("✅ Learning path created!")
                        # Refresh learning paths
                        paths_data = api.get_user_learning_paths(st.session_state.user_id)
                        if paths_data:
                            st.session_state.learning_paths = paths_data.get("learning_paths", [])
                    else:
                        st.error("Failed to create learning path")
                else:
                    st.info("Please login to create a learning path")
            else:
                st.error("Please describe your learning goal")
    
    with col2:
        st.subheader("Your Learning Paths")
        
        # Load mock data if available
        if StreamlitConfig.USE_MOCK_DATA and not st.session_state.learning_paths:
            st.session_state.learning_paths = get_mock_data("learning_paths")
        
        if not st.session_state.learning_paths:
            st.info("No learning paths yet. Create one to get started!")
        else:
            for i, path in enumerate(st.session_state.learning_paths):
                with st.expander(f"📚 {path.get('title', f'Learning Path {i+1}')}"):
                    st.write(f"**Goal:** {path.get('goal', 'Not specified')}")
                    st.write(f"**Progress:** {path.get('progress', 0):.1%}")
                    
                    # Progress bar
                    progress = path.get('progress', 0)
                    st.progress(progress)
                    
                    # Milestones
                    milestones = path.get('milestones', [])
                    if milestones:
                        st.write("**Milestones:**")
                        for milestone in milestones[:3]:  # Show first 3
                            status_icon = "✅" if milestone.get('status') == 'completed' else "🔄" if milestone.get('status') == 'in_progress' else "⏳"
                            st.write(f"{status_icon} {milestone.get('title', 'Milestone')}")
                            if milestone.get('description'):
                                st.caption(milestone['description'])
                    
                    # Action buttons
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"Continue Path", key=f"continue_{i}"):
                            st.info("Continuing learning path...")
                    with col_b:
                        if st.button(f"View Details", key=f"details_{i}"):
                            st.info("Showing detailed view...")

def show_user_profile():
    """User profile management"""
    st.header("👤 User Profile")
    
    # Load mock profile if using mock data
    if StreamlitConfig.USE_MOCK_DATA and not st.session_state.user_profile:
        st.session_state.user_profile = get_mock_data("user_profile")
    
    if st.session_state.user_profile:
        profile = st.session_state.user_profile
        
        # Progress dashboard
        if StreamlitConfig.USE_MOCK_DATA:
            analytics_data = get_mock_data("analytics")
            render_progress_dashboard(analytics_data)
            st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Information")
            st.write(f"**Name:** {st.session_state.user_name or 'N/A'}")
            st.write(f"**Email:** {st.session_state.user_email or 'N/A'}")
            st.write(f"**User ID:** {profile.get('user_id', st.session_state.user_id)}")
            st.write(f"**Member Since:** {profile.get('created_at', 'N/A')}")
            st.write(f"**Last Active:** {profile.get('last_active', 'N/A')}")
            
            st.subheader("Career Goals")
            goals = profile.get('career_goals', [])
            if goals:
                for i, goal in enumerate(goals):
                    col_goal, col_edit = st.columns([4, 1])
                    with col_goal:
                        st.write(f"🎯 {goal}")
                    with col_edit:
                        if st.button("✏️", key=f"edit_goal_{i}"):
                            st.info("Goal editing would be implemented here")
            else:
                st.info("No career goals set")
            
            # Add new goal
            with st.expander("Add New Goal"):
                new_goal = st.text_input("New career goal:")
                if st.button("Add Goal") and new_goal:
                    if 'career_goals' not in profile:
                        profile['career_goals'] = []
                    profile['career_goals'].append(new_goal)
                    st.success("Goal added!")
                    st.rerun()
        
        with col2:
            st.subheader("Learning Preferences")
            prefs = profile.get('learning_preferences', {})
            if prefs:
                st.write(f"**Learning Style:** {prefs.get('learning_style', 'N/A')}")
                st.write(f"**Time Commitment:** {prefs.get('time_commitment', 'N/A')} hours/week")
                st.write(f"**Budget:** {prefs.get('budget_preference', 'N/A')}")
                
                platforms = prefs.get('preferred_platforms', [])
                if platforms:
                    st.write(f"**Platforms:** {', '.join(platforms)}")
                
                content_types = prefs.get('content_types', [])
                if content_types:
                    st.write(f"**Content Types:** {', '.join(content_types)}")
            else:
                st.info("No preferences set")
            
            # Edit preferences button
            if st.button("Edit Preferences"):
                st.session_state.show_preferences_editor = True
            
            st.subheader("Current Skills")
            skills = profile.get('current_skills', {})
            if skills:
                for skill_name, skill_data in skills.items():
                    level = skill_data.get('level', 'Unknown')
                    confidence = skill_data.get('confidence_score', 0)
                    
                    # Skill progress bar
                    col_skill, col_conf = st.columns([2, 1])
                    with col_skill:
                        st.write(f"**{skill_name}:** {level}")
                    with col_conf:
                        st.progress(confidence)
                        st.caption(f"{confidence:.1%}")
            else:
                st.info("No skills assessed yet")
        
        # Preferences editor
        if st.session_state.get("show_preferences_editor", False):
            st.divider()
            st.subheader("✏️ Edit Learning Preferences")
            
            with st.form("preferences_form"):
                current_prefs = profile.get('learning_preferences', {})
                
                learning_style = st.selectbox(
                    "Learning Style:",
                    ["visual", "auditory", "kinesthetic", "reading"],
                    index=["visual", "auditory", "kinesthetic", "reading"].index(
                        current_prefs.get('learning_style', 'visual')
                    )
                )
                
                time_commitment = st.selectbox(
                    "Time Commitment:",
                    ["1-5", "5-10", "10-20", "20+"],
                    index=["1-5", "5-10", "10-20", "20+"].index(
                        current_prefs.get('time_commitment', '5-10')
                    )
                )
                
                budget_preference = st.selectbox(
                    "Budget Preference:",
                    ["free", "low_cost", "moderate", "premium"],
                    index=["free", "low_cost", "moderate", "premium"].index(
                        current_prefs.get('budget_preference', 'moderate')
                    )
                )
                
                preferred_platforms = st.multiselect(
                    "Preferred Platforms:",
                    ["youtube", "coursera", "udemy", "edx", "khan_academy", "codecademy"],
                    default=current_prefs.get('preferred_platforms', [])
                )
                
                content_types = st.multiselect(
                    "Content Types:",
                    ["video", "text", "interactive", "project_based", "quiz"],
                    default=current_prefs.get('content_types', [])
                )
                
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    if st.form_submit_button("Save Changes"):
                        # Update preferences
                        profile['learning_preferences'] = {
                            'learning_style': learning_style,
                            'time_commitment': time_commitment,
                            'budget_preference': budget_preference,
                            'preferred_platforms': preferred_platforms,
                            'content_types': content_types
                        }
                        st.session_state.show_preferences_editor = False
                        st.success("Preferences updated!")
                        st.rerun()
                
                with col_cancel:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_preferences_editor = False
                        st.rerun()
    
    else:
        st.info("Profile information not available. Please login or register to view your profile.")
        
        if st.button("Create Profile"):
            st.session_state.show_registration = True
            st.rerun()

def show_privacy_controls():
    """Privacy and data management"""
    st.header("🔒 Privacy & Data Management")
    
    tab1, tab2, tab3 = st.tabs(["Settings", "Data Export", "Data Deletion"])
    
    with tab1:
        st.subheader("Privacy Settings")
        
        # Get current settings
        settings_data = api.get_privacy_settings(st.session_state.user_id)
        settings = settings_data.get("settings", {}) if settings_data else {}
        
        with st.form("privacy_settings"):
            allow_analytics = st.checkbox(
                "Allow analytics data collection",
                value=settings.get("allow_analytics", True)
            )
            
            allow_personalization = st.checkbox(
                "Allow personalization features",
                value=settings.get("allow_personalization", True)
            )
            
            allow_marketing = st.checkbox(
                "Allow marketing communications",
                value=settings.get("allow_marketing", False)
            )
            
            auto_delete = st.checkbox(
                "Auto-delete old conversations",
                value=settings.get("auto_delete_conversations", False)
            )
            
            retention_days = st.number_input(
                "Conversation retention (days)",
                min_value=30,
                max_value=3650,
                value=settings.get("conversation_retention_days", 365)
            )
            
            if st.form_submit_button("Update Settings"):
                st.success("✅ Privacy settings updated!")
    
    with tab2:
        st.subheader("Export Your Data")
        st.write("Download all your data in JSON format.")
        
        if st.button("Export Data", key="export_data"):
            with st.spinner("Preparing your data export..."):
                result = api.export_user_data(st.session_state.user_id)
                if result:
                    st.success("✅ Data export ready!")
                    
                    # Convert to JSON string for download
                    json_str = json.dumps(result, indent=2)
                    st.download_button(
                        label="Download Export",
                        data=json_str,
                        file_name=f"edagent_export_{st.session_state.user_id}.json",
                        mime="application/json"
                    )
                else:
                    st.error("Failed to export data")
    
    with tab3:
        st.subheader("Delete Your Data")
        st.warning("⚠️ This action cannot be undone!")
        
        data_types = st.multiselect(
            "Select data types to delete:",
            ["conversations", "assessments", "learning_paths", "profile", "all"]
        )
        
        confirm = st.checkbox("I understand this action cannot be undone")
        
        if st.button("Delete Selected Data", key="delete_data", type="secondary"):
            if confirm and data_types:
                st.error("Data deletion functionality would be implemented here")
            else:
                st.error("Please confirm and select data types to delete")

def show_analytics():
    """Analytics and progress tracking"""
    st.header("📈 Your Learning Analytics")
    
    # Load analytics data
    if StreamlitConfig.USE_MOCK_DATA:
        analytics_data = get_mock_data("analytics")
        user_profile = st.session_state.user_profile or get_mock_data("user_profile")
        
        # Render comprehensive progress dashboard
        render_progress_dashboard(analytics_data)
        
        st.divider()
        
        # Resource recommendations
        recommendations = get_mock_data("recommendations")
        render_resource_recommendations(recommendations)
        
    else:
        # Mock analytics data for non-mock mode
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Assessments", "12", "+3")
        
        with col2:
            st.metric("Learning Paths", "5", "+1")
        
        with col3:
            st.metric("Skills Improved", "8", "+2")
        
        with col4:
            st.metric("Study Hours", "45", "+12")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Progress over time
            dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
            progress_data = pd.DataFrame({
                'Date': dates,
                'Progress': [i + (i % 7) * 2 for i in range(len(dates))]
            })
            
            fig = px.line(progress_data, x='Date', y='Progress', 
                         title='Learning Progress Over Time',
                         color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Skill distribution
            skills_data = {
                'Skill': ['Python', 'Web Dev', 'Data Science', 'ML', 'SQL'],
                'Level': [85, 70, 60, 45, 80]
            }
            
            fig = px.bar(skills_data, x='Skill', y='Level', 
                        title='Current Skill Levels',
                        color='Level',
                        color_continuous_scale='viridis')
            st.plotly_chart(fig, use_container_width=True)
        
        # Activity heatmap
        st.subheader("Activity Heatmap")
        
        # Generate mock activity data
        import numpy as np
        activity_data = np.random.randint(0, 10, size=(7, 24))
        
        fig = go.Figure(data=go.Heatmap(
            z=activity_data,
            x=[f"{i}:00" for i in range(24)],
            y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            colorscale='Blues',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='Weekly Activity Pattern',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Additional analytics sections
    st.divider()
    
    # Learning streaks and achievements
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Learning Streaks")
        
        streak_data = {
            "Current Streak": "7 days",
            "Longest Streak": "23 days", 
            "This Week": "5 days",
            "This Month": "18 days"
        }
        
        for label, value in streak_data.items():
            st.metric(label, value)
    
    with col2:
        st.subheader("🏆 Achievements")
        
        achievements = [
            {"title": "First Assessment", "description": "Completed your first skill assessment", "earned": True},
            {"title": "Learning Path Creator", "description": "Created your first learning path", "earned": True},
            {"title": "Week Warrior", "description": "Studied for 7 consecutive days", "earned": True},
            {"title": "Skill Master", "description": "Reached advanced level in a skill", "earned": False},
            {"title": "Course Completer", "description": "Finished a complete learning path", "earned": False}
        ]
        
        for achievement in achievements:
            icon = "🏆" if achievement["earned"] else "🔒"
            color = "normal" if achievement["earned"] else "secondary"
            st.write(f"{icon} **{achievement['title']}**")
            st.caption(achievement["description"])
            st.divider()

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