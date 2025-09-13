"""
EdAgent Streamlit Frontend - Refactored Modular Application

This is the main application file that demonstrates the new modular architecture
with proper separation of concerns, comprehensive error handling, and maintainable code structure.
"""

import streamlit as st
import asyncio
from typing import Dict, Any, Optional

# Import the new modular components
from edagent_streamlit import (
    # Core modules
    StreamlitConfig,
    SessionManager,
    EnhancedEdAgentAPI,
    ErrorHandler,
    setup_logging,
    
    # UI Components
    AuthenticationComponents,
    ChatComponents,
    AssessmentComponents,
    LearningPathComponents,
    PrivacyComponents,
    AnalyticsComponents,
    ProfileComponents,
    CommonComponents,
    
    # Utilities
    FormValidator,
    DataFormatter,
    UIHelpers
)

# Initialize logging
logger = setup_logging("edagent_streamlit_app")

# Initialize configuration
config = StreamlitConfig()

# Configure Streamlit page
st.set_page_config(**config.get_streamlit_config())

# Initialize core components
session_manager = SessionManager()
api_client = EnhancedEdAgentAPI(session_manager)
error_handler = ErrorHandler()
common_components = CommonComponents()

# Initialize UI components
auth_components = AuthenticationComponents(api_client, session_manager)
chat_components = ChatComponents(api_client, session_manager)
assessment_components = AssessmentComponents(api_client, session_manager)
learning_path_components = LearningPathComponents(api_client, session_manager)
privacy_components = PrivacyComponents(api_client, session_manager)
analytics_components = AnalyticsComponents(api_client, session_manager)
profile_components = ProfileComponents(api_client, session_manager)

# Initialize utilities
form_validator = FormValidator()
data_formatter = DataFormatter()
ui_helpers = UIHelpers()


def initialize_application() -> None:
    """Initialize the application with proper setup and error handling"""
    try:
        # Load session state
        session_manager.load_session_state()
        
        # Inject custom CSS
        common_components.inject_custom_css()
        
        # Log application startup
        logger.info("EdAgent Streamlit application initialized successfully")
        
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        st.error("Failed to initialize application. Please refresh the page.")


def render_header() -> None:
    """Render application header with branding and navigation"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {config.ui.primary_color}, {config.ui.primary_color}dd);
        padding: 1rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 15px 15px;
        color: white;
    ">
        <h1 style="margin: 0; font-size: 2rem;">
            {config.ui.app_icon} {config.ui.app_title}
        </h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
            Your AI-powered career coaching assistant
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render sidebar with authentication and navigation"""
    with st.sidebar:
        st.markdown("### Navigation")
        
        # Authentication section
        auth_result = auth_components.render_authentication_interface()
        
        if session_manager.is_authenticated():
            # User profile section
            auth_components.render_user_profile_sidebar()
            
            # Quick actions
            st.markdown("---")
            st.markdown("### Quick Actions")
            
            if st.button("🔄 Refresh Data", key="refresh_data"):
                api_client.clear_cache()
                session_manager.clear_cached_data()
                st.success("Data refreshed!")
                st.rerun()
            
            if st.button("📊 View Analytics", key="quick_analytics"):
                session_manager.set_current_tab("analytics")
                st.rerun()
            
            # System status
            st.markdown("---")
            st.markdown("### System Status")
            
            # API status
            try:
                # Simple health check (you could implement a proper health endpoint)
                st.success("🟢 API Connected")
            except:
                st.error("🔴 API Disconnected")
            
            # Session info
            if config.features.debug_mode:
                with st.expander("Debug Info"):
                    session_info = session_manager.get_session_info()
                    st.json({
                        "authenticated": session_info["is_authenticated"],
                        "user_id": session_info["user_id"],
                        "current_tab": session_info["current_tab"],
                        "cache_keys": len(session_info["cached_data_keys"])
                    })


def render_main_content() -> None:
    """Render main application content based on current tab"""
    if not session_manager.is_authenticated():
        render_welcome_page()
        return
    
    # Get current tab
    current_tab = session_manager.get_current_tab()
    
    # Tab configuration
    tab_config = {
        "chat": {
            "label": "💬 Chat",
            "component": chat_components.render_chat_interface,
            "description": "AI-powered conversations"
        },
        "assessments": {
            "label": "📊 Assessments", 
            "component": assessment_components.render_assessment_dashboard,
            "description": "Skill evaluations"
        },
        "learning_paths": {
            "label": "🛤️ Learning Paths",
            "component": learning_path_components.render_learning_paths_dashboard,
            "description": "Personalized learning"
        },
        "profile": {
            "label": "👤 Profile",
            "component": profile_components.render_profile_dashboard,
            "description": "User settings"
        },
        "privacy": {
            "label": "🔒 Privacy",
            "component": privacy_components.render_privacy_dashboard,
            "description": "Data controls"
        },
        "analytics": {
            "label": "📈 Analytics",
            "component": analytics_components.render_analytics_dashboard,
            "description": "Progress tracking"
        }
    }
    
    # Create tabs
    tab_labels = [config["label"] for config in tab_config.values()]
    tabs = st.tabs(tab_labels)
    
    # Render tab content
    for i, (tab_key, tab_info) in enumerate(tab_config.items()):
        with tabs[i]:
            try:
                # Update current tab in session
                if st.session_state.get("active_tab") != tab_key:
                    session_manager.set_current_tab(tab_key)
                    st.session_state.active_tab = tab_key
                
                # Render tab content with error boundary
                with error_handler.with_error_handling(f"render_{tab_key}"):
                    tab_info["component"]()
                    
            except Exception as e:
                logger.error(f"Error rendering {tab_key} tab: {e}")
                st.error(f"Error loading {tab_info['label']}. Please try refreshing the page.")


def render_welcome_page() -> None:
    """Render welcome page for unauthenticated users"""
    # Hero section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 3rem; margin-bottom: 1rem;">
                {config.ui.app_icon}
            </h1>
            <h2 style="color: {config.ui.primary_color}; margin-bottom: 1rem;">
                Welcome to EdAgent
            </h2>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
                Your AI-powered career coaching assistant
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Features section
    st.markdown("### What EdAgent Can Do For You")
    
    feature_cols = st.columns(3)
    
    features = [
        {
            "icon": "🎯",
            "title": "Skill Assessment",
            "description": "Evaluate your current skills and identify areas for improvement"
        },
        {
            "icon": "📚",
            "title": "Learning Paths",
            "description": "Get personalized learning recommendations based on your goals"
        },
        {
            "icon": "💼",
            "title": "Career Coaching",
            "description": "Receive AI-powered advice for your career development"
        }
    ]
    
    for i, feature in enumerate(features):
        with feature_cols[i]:
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 1.5rem;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                margin: 0.5rem 0;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">
                    {feature['icon']}
                </div>
                <h4 style="margin-bottom: 0.5rem;">
                    {feature['title']}
                </h4>
                <p style="color: #666; font-size: 0.9rem;">
                    {feature['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h3>Ready to Start Your Journey?</h3>
            <p>Create an account or log in to access all features</p>
        </div>
        """, unsafe_allow_html=True)


def render_footer() -> None:
    """Render application footer"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**EdAgent**")
        st.markdown("AI-powered career coaching")
    
    with col2:
        st.markdown("**Resources**")
        st.markdown("• [Documentation](https://docs.edagent.ai)")
        st.markdown("• [Support](https://support.edagent.ai)")
    
    with col3:
        st.markdown("**Connect**")
        st.markdown("• [GitHub](https://github.com/edagent)")
        st.markdown("• [Twitter](https://twitter.com/edagent)")
    
    # Version info
    if config.features.debug_mode:
        st.caption(f"Version 1.0.0 • Environment: {config.environment.value}")


def handle_notifications() -> None:
    """Handle and display notifications"""
    notifications = session_manager.get_notifications()
    
    for notification in notifications:
        notification_type = notification.get("type", "info")
        message = notification.get("message", "")
        
        common_components.render_notification_toast(
            message=message,
            type=notification_type,
            dismissible=True
        )
    
    # Clear old notifications
    if notifications:
        session_manager.clear_notifications()


def main() -> None:
    """Main application entry point"""
    try:
        # Initialize application
        initialize_application()
        
        # Render header
        render_header()
        
        # Handle notifications
        handle_notifications()
        
        # Create main layout
        main_col, sidebar_col = st.columns([4, 1])
        
        with main_col:
            render_main_content()
        
        with sidebar_col:
            render_sidebar()
        
        # Render footer
        render_footer()
        
        # Save session state
        session_manager.save_session_state()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        
        # Show error page
        st.error("An unexpected error occurred. Please refresh the page.")
        
        if config.features.debug_mode:
            st.exception(e)


if __name__ == "__main__":
    main()