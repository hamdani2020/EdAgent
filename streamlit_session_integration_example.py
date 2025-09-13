"""
Integration example showing how to use the enhanced SessionManager 
with the EdAgent Streamlit application.

This example demonstrates:
- Replacing the basic session management with the enhanced SessionManager
- Proper authentication flow with token management
- Session persistence and validation
- User preference management
- Error handling and recovery
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# Import the enhanced session manager
from streamlit_session_manager import SessionManager, UserInfo, UserPreferences, SessionState

# Import existing API client (would need to be updated to work with new SessionManager)
# from streamlit_api_client import EnhancedEdAgentAPI


class StreamlitAppWithEnhancedSession:
    """
    Example Streamlit application using the enhanced SessionManager
    """
    
    def __init__(self):
        # Initialize the enhanced session manager
        self.session_manager = SessionManager(session_timeout_minutes=480)  # 8 hours
        
        # Initialize API client with session manager
        # self.api_client = EnhancedEdAgentAPI(
        #     base_url="http://localhost:8000/api/v1",
        #     session_manager=self.session_manager
        # )
        
        # Load session state on app start
        self.session_manager.load_session_state()
    
    def run(self):
        """Main application entry point"""
        st.set_page_config(
            page_title="EdAgent - Enhanced Session Demo",
            page_icon="🎓",
            layout="wide"
        )
        
        # Check session state and handle accordingly
        session_state = self.session_manager.get_session_state()
        
        if session_state == SessionState.UNAUTHENTICATED:
            self.show_authentication_page()
        elif session_state == SessionState.TOKEN_EXPIRED:
            self.handle_token_expiry()
        elif session_state == SessionState.TOKEN_REFRESH_NEEDED:
            self.handle_token_refresh()
        else:
            self.show_main_application()
    
    def show_authentication_page(self):
        """Show login/registration page"""
        st.title("🔐 EdAgent Authentication")
        
        # Create tabs for login and registration
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            self.show_login_form()
        
        with register_tab:
            self.show_registration_form()
    
    def show_login_form(self):
        """Show login form"""
        st.subheader("Login to EdAgent")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me for 30 days")
            
            submitted = st.form_submit_button("Login", type="primary")
            
            if submitted:
                if email and password:
                    # Show loading state
                    self.session_manager.set_loading_state("login", True)
                    
                    with st.spinner("Logging in..."):
                        # Simulate API call (replace with actual API call)
                        success = self.simulate_login(email, password)
                        
                        if success:
                            # Create user info
                            user_info = UserInfo(
                                user_id="demo_user_123",
                                email=email,
                                name="Demo User",
                                created_at=datetime.now(),
                                last_active=datetime.now()
                            )
                            
                            # Set authentication data
                            expires_at = datetime.now() + timedelta(days=30 if remember_me else 1)
                            self.session_manager.set_auth_data(
                                user_info=user_info,
                                access_token="demo_access_token",
                                refresh_token="demo_refresh_token",
                                expires_at=expires_at
                            )
                            
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials. Please try again.")
                    
                    self.session_manager.set_loading_state("login", False)
                else:
                    st.error("Please enter both email and password.")
    
    def show_registration_form(self):
        """Show registration form"""
        st.subheader("Create EdAgent Account")
        
        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Password strength indicator
            if password:
                strength = self.check_password_strength(password)
                if strength < 3:
                    st.error("Weak password. Please use a stronger password.")
                elif strength < 5:
                    st.warning("Medium password strength.")
                else:
                    st.success("Strong password! ✓")
            
            submitted = st.form_submit_button("Create Account", type="primary")
            
            if submitted:
                if name and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        # Show loading state
                        self.session_manager.set_loading_state("register", True)
                        
                        with st.spinner("Creating account..."):
                            # Simulate API call
                            success = self.simulate_registration(name, email, password)
                            
                            if success:
                                # Create user info
                                user_info = UserInfo(
                                    user_id="demo_user_456",
                                    email=email,
                                    name=name,
                                    created_at=datetime.now(),
                                    last_active=datetime.now()
                                )
                                
                                # Set authentication data
                                self.session_manager.set_auth_data(
                                    user_info=user_info,
                                    access_token="demo_access_token",
                                    refresh_token="demo_refresh_token",
                                    expires_at=datetime.now() + timedelta(hours=24)
                                )
                                
                                st.success("✅ Account created successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Registration failed. Please try again.")
                        
                        self.session_manager.set_loading_state("register", False)
                else:
                    st.error("Please fill in all fields.")
    
    def handle_token_expiry(self):
        """Handle expired token"""
        st.warning("🔐 Your session has expired. Please log in again.")
        
        # Clear expired session
        self.session_manager.clear_session()
        
        # Show login form
        self.show_authentication_page()
    
    def handle_token_refresh(self):
        """Handle token refresh"""
        st.info("🔄 Refreshing your session...")
        
        # Simulate token refresh
        with st.spinner("Refreshing session..."):
            success = self.simulate_token_refresh()
            
            if success:
                # Update token
                new_expires_at = datetime.now() + timedelta(hours=1)
                self.session_manager.update_token(
                    access_token="refreshed_access_token",
                    expires_at=new_expires_at
                )
                st.success("✅ Session refreshed!")
                st.rerun()
            else:
                st.error("❌ Failed to refresh session. Please log in again.")
                self.session_manager.handle_auth_error()
    
    def show_main_application(self):
        """Show main application interface"""
        current_user = self.session_manager.get_current_user()
        
        # Header with user info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title(f"🎓 Welcome back, {current_user.name}!")
        
        with col2:
            # Session info
            time_until_expiry = self.session_manager.get_time_until_token_expiry()
            if time_until_expiry:
                hours = int(time_until_expiry.total_seconds() // 3600)
                minutes = int((time_until_expiry.total_seconds() % 3600) // 60)
                st.info(f"Session expires in: {hours}h {minutes}m")
        
        with col3:
            if st.button("Logout"):
                self.session_manager.clear_session()
                st.success("Logged out successfully!")
                st.rerun()
        
        # Show session debug info in sidebar
        with st.sidebar:
            st.subheader("Session Information")
            session_info = self.session_manager.get_session_info()
            
            st.json({
                "User ID": session_info["user_id"],
                "Session State": session_info["session_state"],
                "Authenticated": session_info["is_authenticated"],
                "Current Tab": session_info["current_tab"],
                "Needs Refresh": session_info["needs_refresh"]
            })
            
            # User preferences
            st.subheader("User Preferences")
            self.show_user_preferences()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Analytics", "⚙️ Settings", "🔒 Privacy"])
        
        with tab1:
            self.session_manager.set_current_tab("chat")
            self.show_chat_interface()
        
        with tab2:
            self.session_manager.set_current_tab("analytics")
            self.show_analytics_interface()
        
        with tab3:
            self.session_manager.set_current_tab("settings")
            self.show_settings_interface()
        
        with tab4:
            self.session_manager.set_current_tab("privacy")
            self.show_privacy_interface()
    
    def show_user_preferences(self):
        """Show and manage user preferences"""
        preferences = self.session_manager.get_user_preferences()
        
        if not preferences:
            if st.button("Set Up Preferences"):
                # Initialize default preferences
                default_prefs = UserPreferences()
                self.session_manager.update_user_preferences(default_prefs)
                st.rerun()
        else:
            # Show current preferences
            st.write(f"**Learning Style:** {preferences.learning_style}")
            st.write(f"**Time Commitment:** {preferences.time_commitment}")
            st.write(f"**Theme:** {preferences.theme}")
            
            # Quick preference updates
            if st.button("Switch Theme"):
                new_theme = "dark" if preferences.theme == "light" else "light"
                self.session_manager.set_preference("theme", new_theme)
                st.success(f"Theme changed to {new_theme}")
                st.rerun()
    
    def show_chat_interface(self):
        """Show chat interface with session-aware features"""
        st.subheader("💬 Chat with EdAgent")
        
        # Load cached chat messages
        chat_messages = self.session_manager.get_cached_data("chat_messages") or []
        
        # Display chat messages
        for message in chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            chat_messages.append({"role": "user", "content": prompt})
            
            # Simulate AI response
            ai_response = f"Thanks for your message: '{prompt}'. This is a demo response from EdAgent!"
            chat_messages.append({"role": "assistant", "content": ai_response})
            
            # Cache updated messages
            self.session_manager.set_cached_data("chat_messages", chat_messages, ttl_hours=24)
            
            st.rerun()
    
    def show_analytics_interface(self):
        """Show analytics interface"""
        st.subheader("📊 Your Learning Analytics")
        
        # Simulate analytics data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sessions This Week", "12", "+3")
        
        with col2:
            st.metric("Learning Hours", "8.5", "+2.1")
        
        with col3:
            st.metric("Skills Assessed", "5", "+1")
        
        # Show cached analytics data
        analytics_data = self.session_manager.get_cached_data("analytics_data")
        if not analytics_data:
            # Generate and cache analytics data
            analytics_data = {
                "last_updated": datetime.now().isoformat(),
                "total_sessions": 45,
                "total_hours": 120.5,
                "skills_progress": {"Python": 85, "JavaScript": 70, "Data Science": 60}
            }
            self.session_manager.set_cached_data("analytics_data", analytics_data, ttl_hours=6)
        
        st.json(analytics_data)
    
    def show_settings_interface(self):
        """Show settings interface"""
        st.subheader("⚙️ Account Settings")
        
        current_user = self.session_manager.get_current_user()
        preferences = self.session_manager.get_user_preferences() or UserPreferences()
        
        # User profile settings
        with st.form("profile_settings"):
            st.write("**Profile Information**")
            name = st.text_input("Name", value=current_user.name or "")
            email = st.text_input("Email", value=current_user.email, disabled=True)
            
            st.write("**Learning Preferences**")
            learning_style = st.selectbox(
                "Learning Style",
                ["visual", "auditory", "kinesthetic", "reading"],
                index=["visual", "auditory", "kinesthetic", "reading"].index(preferences.learning_style)
            )
            
            time_commitment = st.selectbox(
                "Time Commitment (hours/week)",
                ["1-5", "5-10", "10-20", "20+"],
                index=["1-5", "5-10", "10-20", "20+"].index(preferences.time_commitment)
            )
            
            theme = st.selectbox(
                "Theme",
                ["light", "dark"],
                index=["light", "dark"].index(preferences.theme)
            )
            
            if st.form_submit_button("Save Settings"):
                # Update preferences
                preferences.learning_style = learning_style
                preferences.time_commitment = time_commitment
                preferences.theme = theme
                
                self.session_manager.update_user_preferences(preferences)
                st.success("✅ Settings saved!")
                st.rerun()
    
    def show_privacy_interface(self):
        """Show privacy interface"""
        st.subheader("🔒 Privacy & Data Management")
        
        # Session management
        st.write("**Session Management**")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear Cache"):
                self.session_manager.clear_cached_data()
                st.success("Cache cleared!")
        
        with col2:
            if st.button("End All Sessions"):
                self.session_manager.clear_session()
                st.success("All sessions ended!")
                st.rerun()
        
        # Data export
        st.write("**Data Export**")
        if st.button("Export My Data"):
            # Simulate data export
            user_data = {
                "user_info": self.session_manager.get_current_user().to_dict(),
                "preferences": self.session_manager.get_user_preferences().to_dict() if self.session_manager.get_user_preferences() else {},
                "session_info": self.session_manager.get_session_info(),
                "cached_data": self.session_manager.get_cached_data("chat_messages") or []
            }
            
            st.download_button(
                label="Download Data (JSON)",
                data=str(user_data),
                file_name=f"edagent_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Utility methods for simulation
    
    def simulate_login(self, email: str, password: str) -> bool:
        """Simulate login API call"""
        # Simulate network delay
        import time
        time.sleep(1)
        
        # Simple validation for demo
        return email.endswith("@example.com") and len(password) >= 6
    
    def simulate_registration(self, name: str, email: str, password: str) -> bool:
        """Simulate registration API call"""
        import time
        time.sleep(1.5)
        
        # Simple validation for demo
        return len(name) >= 2 and email.endswith("@example.com") and len(password) >= 6
    
    def simulate_token_refresh(self) -> bool:
        """Simulate token refresh API call"""
        import time
        time.sleep(0.5)
        
        # Simulate 90% success rate
        import random
        return random.random() > 0.1
    
    def check_password_strength(self, password: str) -> int:
        """Check password strength (0-5 scale)"""
        score = 0
        if len(password) >= 8:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        return score


# Main application entry point
def main():
    """Main function to run the Streamlit app"""
    app = StreamlitAppWithEnhancedSession()
    app.run()


if __name__ == "__main__":
    main()