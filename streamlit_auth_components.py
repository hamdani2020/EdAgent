"""
Comprehensive Authentication Components for EdAgent Streamlit Application

This module provides enhanced authentication components with:
- Robust error handling and user feedback
- Password strength validation with real-time feedback
- Automatic token refresh and session management
- User-friendly registration and login forms
- Secure logout functionality
- Integration tests for authentication workflows
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import streamlit as st

from streamlit_api_client import EnhancedEdAgentAPI, AuthResult, APIError, APIErrorType
from streamlit_session_manager import SessionManager, UserInfo, UserPreferences


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PasswordStrength(Enum):
    """Password strength levels"""
    VERY_WEAK = 0
    WEAK = 1
    FAIR = 2
    GOOD = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class PasswordValidation:
    """Password validation result"""
    strength: PasswordStrength
    score: int
    missing_requirements: List[str]
    feedback: str
    is_valid: bool


@dataclass
class ValidationResult:
    """Form validation result"""
    is_valid: bool
    errors: Dict[str, str]
    warnings: Dict[str, str]


class AuthenticationComponents:
    """
    Comprehensive authentication components with enhanced error handling and validation
    """
    
    def __init__(self, api_client: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api_client = api_client
        self.session_manager = session_manager
        
        # Password requirements
        self.password_requirements = {
            'min_length': 8,
            'max_length': 128,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
            'special_chars': "!@#$%^&*()_+-=[]{}|;:,.<>?"
        }
        
        logger.info("AuthenticationComponents initialized")
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        if len(email) > 254:
            return False, "Email is too long"
        
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Please enter a valid email address"
        
        return True, ""
    
    def validate_password(self, password: str) -> PasswordValidation:
        """Comprehensive password validation with strength assessment"""
        if not password:
            return PasswordValidation(
                strength=PasswordStrength.VERY_WEAK,
                score=0,
                missing_requirements=["Password is required"],
                feedback="Password is required",
                is_valid=False
            )
        
        score = 0
        missing_requirements = []
        
        # Length check
        if len(password) < self.password_requirements['min_length']:
            missing_requirements.append(f"At least {self.password_requirements['min_length']} characters")
        else:
            score += 1
        
        if len(password) > self.password_requirements['max_length']:
            missing_requirements.append(f"No more than {self.password_requirements['max_length']} characters")
        
        # Character type checks
        if self.password_requirements['require_uppercase'] and not any(c.isupper() for c in password):
            missing_requirements.append("One uppercase letter")
        else:
            score += 1
        
        if self.password_requirements['require_lowercase'] and not any(c.islower() for c in password):
            missing_requirements.append("One lowercase letter")
        else:
            score += 1
        
        if self.password_requirements['require_digit'] and not any(c.isdigit() for c in password):
            missing_requirements.append("One number")
        else:
            score += 1
        
        if self.password_requirements['require_special'] and not any(c in self.password_requirements['special_chars'] for c in password):
            missing_requirements.append("One special character")
        else:
            score += 1
        
        # Additional strength factors
        if len(password) >= 12:
            score += 1
        
        if len(set(password)) >= len(password) * 0.7:  # Character diversity
            score += 1
        
        # Determine strength level
        if score <= 1:
            strength = PasswordStrength.VERY_WEAK
            feedback = "Very weak password"
        elif score == 2:
            strength = PasswordStrength.WEAK
            feedback = "Weak password"
        elif score == 3:
            strength = PasswordStrength.FAIR
            feedback = "Fair password"
        elif score == 4:
            strength = PasswordStrength.GOOD
            feedback = "Good password"
        elif score == 5:
            strength = PasswordStrength.STRONG
            feedback = "Strong password"
        else:
            strength = PasswordStrength.VERY_STRONG
            feedback = "Very strong password"
        
        is_valid = len(missing_requirements) == 0 and len(password) <= self.password_requirements['max_length']
        
        return PasswordValidation(
            strength=strength,
            score=score,
            missing_requirements=missing_requirements,
            feedback=feedback,
            is_valid=is_valid
        )
    
    def validate_name(self, name: str) -> Tuple[bool, str]:
        """Validate name field"""
        if not name or not name.strip():
            return False, "Name is required"
        
        if len(name.strip()) < 2:
            return False, "Name must be at least 2 characters"
        
        if len(name.strip()) > 100:
            return False, "Name is too long"
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", name.strip()):
            return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
        
        return True, ""
    
    def render_password_strength_indicator(self, password: str) -> None:
        """Render real-time password strength indicator"""
        if not password:
            return
        
        validation = self.validate_password(password)
        
        # Color mapping for strength levels
        strength_colors = {
            PasswordStrength.VERY_WEAK: "#dc3545",
            PasswordStrength.WEAK: "#fd7e14",
            PasswordStrength.FAIR: "#ffc107",
            PasswordStrength.GOOD: "#20c997",
            PasswordStrength.STRONG: "#28a745",
            PasswordStrength.VERY_STRONG: "#198754"
        }
        
        color = strength_colors[validation.strength]
        progress = min(validation.score / 5.0, 1.0)
        
        # Progress bar
        st.markdown(f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 0.9em; font-weight: bold;">Password Strength</span>
                <span style="font-size: 0.9em; color: {color}; font-weight: bold;">{validation.feedback}</span>
            </div>
            <div style="background-color: #e9ecef; border-radius: 10px; height: 8px;">
                <div style="background-color: {color}; height: 8px; border-radius: 10px; width: {progress * 100}%; transition: width 0.3s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show missing requirements
        if validation.missing_requirements:
            st.markdown("**Missing requirements:**")
            for req in validation.missing_requirements:
                st.markdown(f"• {req}")
    
    def render_login_form(self) -> Optional[Dict[str, Any]]:
        """Render enhanced login form with validation and error handling"""
        st.subheader("🔐 Login to EdAgent")
        
        with st.form("enhanced_login_form", clear_on_submit=False):
            # Email input
            email = st.text_input(
                "Email Address",
                placeholder="your.email@example.com",
                help="Enter your registered email address"
            )
            
            # Password input
            password = st.text_input(
                "Password",
                type="password",
                help="Enter your password"
            )
            
            # Remember me option
            remember_me = st.checkbox(
                "Keep me logged in",
                help="Stay logged in for 30 days (use only on trusted devices)"
            )
            
            # Submit button
            col1, col2 = st.columns([1, 1])
            with col1:
                login_submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            with col2:
                forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
            
            if login_submitted:
                return self._handle_login_submission(email, password, remember_me)
            
            if forgot_password:
                st.info("🔄 Password reset functionality will be available soon. Please contact support if you need help.")
                return None
        
        return None
    
    def render_registration_form(self) -> Optional[Dict[str, Any]]:
        """Render enhanced registration form with real-time validation"""
        st.subheader("📝 Create Your EdAgent Account")
        st.markdown("Join thousands of learners advancing their careers with AI-powered coaching!")
        
        with st.form("enhanced_registration_form", clear_on_submit=False):
            # Name input
            name = st.text_input(
                "Full Name",
                placeholder="John Doe",
                help="Enter your full name as you'd like it to appear"
            )
            
            # Email input
            email = st.text_input(
                "Email Address",
                placeholder="your.email@example.com",
                help="We'll use this to send you important updates"
            )
            
            # Password input with strength indicator
            password = st.text_input(
                "Password",
                type="password",
                help="Create a strong password to protect your account"
            )
            
            # Show password strength in real-time
            if password:
                self.render_password_strength_indicator(password)
            
            # Confirm password
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                help="Re-enter your password to confirm"
            )
            
            # Terms and privacy
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                accept_terms = st.checkbox("", key="accept_terms")
            with col2:
                st.markdown("""
                I agree to the [Terms of Service](https://edagent.ai/terms) and 
                [Privacy Policy](https://edagent.ai/privacy)
                """)
            
            # Marketing emails opt-in
            marketing_emails = st.checkbox(
                "Send me helpful tips and updates about EdAgent (optional)",
                value=True
            )
            
            # Submit button
            register_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            
            if register_submitted:
                return self._handle_registration_submission(
                    name, email, password, confirm_password, accept_terms, marketing_emails
                )
        
        return None
    
    def _handle_login_submission(self, email: str, password: str, remember_me: bool) -> Optional[Dict[str, Any]]:
        """Handle login form submission with comprehensive validation"""
        # Validate inputs
        validation_errors = {}
        
        # Email validation
        email_valid, email_error = self.validate_email(email)
        if not email_valid:
            validation_errors["email"] = email_error
        
        # Password validation
        if not password:
            validation_errors["password"] = "Password is required"
        
        # Show validation errors
        if validation_errors:
            for field, error in validation_errors.items():
                st.error(f"❌ {error}")
            return None
        
        # Show loading state
        with st.spinner("🔐 Logging you in..."):
            try:
                # Attempt login
                auth_result = asyncio.run(self.api_client.login_user(email, password))
                
                if auth_result.success:
                    # Create user info object
                    user_info = UserInfo(
                        user_id=auth_result.user_id,
                        email=auth_result.email,
                        name=auth_result.name,
                        created_at=datetime.now(),
                        last_active=datetime.now()
                    )
                    
                    # Store authentication data
                    expires_at = auth_result.expires_at or (datetime.now() + timedelta(hours=24))
                    if remember_me:
                        expires_at = datetime.now() + timedelta(days=30)
                    
                    self.session_manager.set_auth_data(
                        user_info=user_info,
                        access_token=auth_result.access_token,
                        expires_at=expires_at
                    )
                    
                    # Success feedback
                    st.success("✅ Login successful! Welcome back!")
                    logger.info(f"User {auth_result.user_id} logged in successfully")
                    
                    # Return success data
                    return {
                        "success": True,
                        "user_id": auth_result.user_id,
                        "email": auth_result.email,
                        "name": auth_result.name
                    }
                
                else:
                    # Handle login failure
                    error_message = auth_result.error or "Login failed. Please check your credentials."
                    st.error(f"❌ {error_message}")
                    logger.warning(f"Login failed for email {email}: {error_message}")
                    return None
            
            except Exception as e:
                st.error("❌ An unexpected error occurred. Please try again.")
                logger.error(f"Login exception for email {email}: {e}")
                return None
    
    def _handle_registration_submission(
        self, 
        name: str, 
        email: str, 
        password: str, 
        confirm_password: str, 
        accept_terms: bool,
        marketing_emails: bool
    ) -> Optional[Dict[str, Any]]:
        """Handle registration form submission with comprehensive validation"""
        # Validate all inputs
        validation_errors = {}
        
        # Name validation
        name_valid, name_error = self.validate_name(name)
        if not name_valid:
            validation_errors["name"] = name_error
        
        # Email validation
        email_valid, email_error = self.validate_email(email)
        if not email_valid:
            validation_errors["email"] = email_error
        
        # Password validation
        password_validation = self.validate_password(password)
        if not password_validation.is_valid:
            validation_errors["password"] = f"Password requirements not met: {', '.join(password_validation.missing_requirements)}"
        
        # Confirm password validation
        if password != confirm_password:
            validation_errors["confirm_password"] = "Passwords do not match"
        
        # Terms acceptance validation
        if not accept_terms:
            validation_errors["terms"] = "You must accept the Terms of Service and Privacy Policy"
        
        # Show validation errors
        if validation_errors:
            st.error("❌ Please fix the following errors:")
            for field, error in validation_errors.items():
                st.error(f"• {error}")
            return None
        
        # Show loading state
        with st.spinner("📝 Creating your account..."):
            try:
                # Attempt registration
                auth_result = asyncio.run(self.api_client.register_user(email, password, name.strip()))
                
                if auth_result.success:
                    # Create user info object
                    user_info = UserInfo(
                        user_id=auth_result.user_id,
                        email=auth_result.email,
                        name=auth_result.name,
                        created_at=datetime.now(),
                        last_active=datetime.now(),
                        preferences=UserPreferences(
                            notifications_enabled=marketing_emails
                        ).to_dict()
                    )
                    
                    # Store authentication data
                    expires_at = auth_result.expires_at or (datetime.now() + timedelta(hours=24))
                    
                    self.session_manager.set_auth_data(
                        user_info=user_info,
                        access_token=auth_result.access_token,
                        expires_at=expires_at
                    )
                    
                    # Success feedback
                    st.success("🎉 Account created successfully! Welcome to EdAgent!")
                    st.balloons()
                    logger.info(f"User {auth_result.user_id} registered successfully")
                    
                    # Show welcome message
                    st.info("💡 **Next Steps:** Complete your profile to get personalized recommendations!")
                    
                    # Return success data
                    return {
                        "success": True,
                        "user_id": auth_result.user_id,
                        "email": auth_result.email,
                        "name": auth_result.name,
                        "is_new_user": True
                    }
                
                else:
                    # Handle registration failure
                    error_message = auth_result.error or "Registration failed. Please try again."
                    st.error(f"❌ {error_message}")
                    logger.warning(f"Registration failed for email {email}: {error_message}")
                    return None
            
            except Exception as e:
                st.error("❌ An unexpected error occurred during registration. Please try again.")
                logger.error(f"Registration exception for email {email}: {e}")
                return None
    
    def render_user_profile_sidebar(self) -> None:
        """Render authenticated user profile in sidebar"""
        if not self.session_manager.is_authenticated():
            return
        
        user_info = self.session_manager.get_current_user()
        if not user_info:
            return
        
        st.sidebar.success(f"👤 Welcome, {user_info.name or user_info.email.split('@')[0]}!")
        
        # User menu
        with st.sidebar.expander("👤 Account", expanded=False):
            st.write(f"**Name:** {user_info.name or 'Not set'}")
            st.write(f"**Email:** {user_info.email}")
            st.write(f"**Member since:** {user_info.created_at.strftime('%B %Y') if user_info.created_at else 'Unknown'}")
            
            # Token expiry info
            expiry_time = self.session_manager.get_time_until_token_expiry()
            if expiry_time:
                if expiry_time.total_seconds() > 0:
                    hours = int(expiry_time.total_seconds() // 3600)
                    minutes = int((expiry_time.total_seconds() % 3600) // 60)
                    st.write(f"**Session expires in:** {hours}h {minutes}m")
                else:
                    st.warning("⚠️ Session expired")
        
        # Quick actions
        with st.sidebar.expander("⚙️ Quick Actions", expanded=False):
            if st.button("🔄 Refresh Session", key="refresh_session"):
                self._handle_token_refresh()
            
            if st.button("📊 View Profile", key="view_profile"):
                st.session_state.current_tab = "profile"
                st.rerun()
            
            if st.button("🔒 Privacy Settings", key="privacy_settings"):
                st.session_state.current_tab = "privacy"
                st.rerun()
        
        # Logout button
        if st.sidebar.button("🚪 Logout", key="logout_btn", type="secondary"):
            self._handle_logout()
    
    def _handle_token_refresh(self) -> None:
        """Handle token refresh"""
        with st.spinner("🔄 Refreshing session..."):
            try:
                success = asyncio.run(self.api_client.refresh_token())
                if success:
                    st.success("✅ Session refreshed successfully!")
                    logger.info("Token refreshed successfully")
                else:
                    st.error("❌ Failed to refresh session. Please log in again.")
                    self.session_manager.handle_auth_error()
            except Exception as e:
                st.error("❌ Error refreshing session. Please log in again.")
                logger.error(f"Token refresh error: {e}")
                self.session_manager.handle_auth_error()
    
    def _handle_logout(self) -> None:
        """Handle user logout with proper cleanup"""
        try:
            # Clear session data
            self.session_manager.clear_session()
            
            # Show success message
            st.success("👋 You have been logged out successfully!")
            logger.info("User logged out successfully")
            
            # Force page refresh to show login form
            st.rerun()
            
        except Exception as e:
            st.error("❌ Error during logout. Clearing session anyway.")
            logger.error(f"Logout error: {e}")
            
            # Force clear session state
            for key in list(st.session_state.keys()):
                if key.startswith("edagent_"):
                    del st.session_state[key]
            
            st.rerun()
    
    def check_and_handle_token_expiry(self) -> bool:
        """Check token expiry and handle automatic refresh"""
        if not self.session_manager.is_authenticated():
            return False
        
        # Check if token needs refresh
        if self.session_manager.needs_token_refresh():
            logger.info("Token needs refresh, attempting automatic refresh")
            
            try:
                success = asyncio.run(self.api_client.refresh_token())
                if success:
                    logger.info("Token refreshed automatically")
                    return True
                else:
                    logger.warning("Automatic token refresh failed")
                    st.warning("⚠️ Your session is about to expire. Please refresh or log in again.")
                    return False
            except Exception as e:
                logger.error(f"Automatic token refresh error: {e}")
                st.error("❌ Session expired. Please log in again.")
                self.session_manager.handle_auth_error()
                return False
        
        return True
    
    def render_authentication_interface(self) -> Optional[Dict[str, Any]]:
        """Render complete authentication interface"""
        # Check token expiry first
        if self.session_manager.is_authenticated():
            if not self.check_and_handle_token_expiry():
                return None
            
            # Render authenticated user interface
            self.render_user_profile_sidebar()
            return {
                "authenticated": True,
                "user": self.session_manager.get_current_user()
            }
        
        # Render authentication forms for unauthenticated users
        st.sidebar.header("🔐 Authentication")
        
        # Authentication tabs
        auth_tab = st.sidebar.radio(
            "Choose an option:",
            ["Login", "Register"],
            help="Login to your existing account or create a new one"
        )
        
        if auth_tab == "Login":
            result = self.render_login_form()
            if result and result.get("success"):
                st.rerun()
            return result
        
        else:  # Register
            result = self.render_registration_form()
            if result and result.get("success"):
                # Set flag to show profile setup for new users
                st.session_state.show_profile_setup = True
                st.rerun()
            return result
    
    def render_error_message(self, error: APIError, context: str) -> None:
        """Render user-friendly error messages"""
        error_icons = {
            APIErrorType.AUTHENTICATION_ERROR: "🔐",
            APIErrorType.AUTHORIZATION_ERROR: "🚫",
            APIErrorType.VALIDATION_ERROR: "⚠️",
            APIErrorType.RATE_LIMIT_ERROR: "⏱️",
            APIErrorType.SERVER_ERROR: "🔧",
            APIErrorType.NETWORK_ERROR: "🌐",
            APIErrorType.TIMEOUT_ERROR: "⏰",
            APIErrorType.UNKNOWN_ERROR: "❌"
        }
        
        icon = error_icons.get(error.error_type, "❌")
        
        # Show main error message
        st.error(f"{icon} {error.message}")
        
        # Show additional context if available
        if error.details:
            with st.expander("Error Details"):
                st.json(error.details)
        
        # Show retry information for retryable errors
        if error.is_retryable:
            if error.retry_after:
                st.info(f"⏳ Please wait {error.retry_after} seconds before trying again.")
            else:
                st.info("🔄 You can try again now.")
        
        # Log error for debugging
        logger.error(f"Error in {context}: {error}")
    
    def render_loading_spinner(self, message: str = "Loading...") -> None:
        """Render loading spinner with message"""
        st.spinner(f"⏳ {message}")
    
    def get_authentication_status(self) -> Dict[str, Any]:
        """Get comprehensive authentication status"""
        return {
            "is_authenticated": self.session_manager.is_authenticated(),
            "session_state": self.session_manager.get_session_state().value,
            "user_info": self.session_manager.get_current_user(),
            "token_expires_at": self.session_manager.get_token_expiry_time(),
            "needs_refresh": self.session_manager.needs_token_refresh(),
            "session_info": self.session_manager.get_session_info()
        }


# Utility functions for integration testing

def create_test_user_data() -> Dict[str, str]:
    """Create test user data for integration testing"""
    import uuid
    test_id = str(uuid.uuid4())[:8]
    
    return {
        "name": f"Test User {test_id}",
        "email": f"test.user.{test_id}@example.com",
        "password": "TestPassword123!"
    }


def run_authentication_integration_test(auth_components: AuthenticationComponents) -> Dict[str, Any]:
    """Run comprehensive authentication integration test"""
    test_results = {
        "registration_test": False,
        "login_test": False,
        "logout_test": False,
        "token_refresh_test": False,
        "errors": []
    }
    
    try:
        # Test user data
        test_data = create_test_user_data()
        
        # Test registration
        logger.info("Testing user registration...")
        reg_result = asyncio.run(
            auth_components.api_client.register_user(
                test_data["email"], 
                test_data["password"], 
                test_data["name"]
            )
        )
        
        if reg_result.success:
            test_results["registration_test"] = True
            logger.info("Registration test passed")
        else:
            test_results["errors"].append(f"Registration failed: {reg_result.error}")
        
        # Test login
        logger.info("Testing user login...")
        login_result = asyncio.run(
            auth_components.api_client.login_user(
                test_data["email"], 
                test_data["password"]
            )
        )
        
        if login_result.success:
            test_results["login_test"] = True
            logger.info("Login test passed")
            
            # Store auth data for further tests
            user_info = UserInfo(
                user_id=login_result.user_id,
                email=login_result.email,
                name=login_result.name
            )
            
            auth_components.session_manager.set_auth_data(
                user_info=user_info,
                access_token=login_result.access_token,
                expires_at=login_result.expires_at
            )
            
            # Test token refresh
            logger.info("Testing token refresh...")
            refresh_result = asyncio.run(auth_components.api_client.refresh_token())
            
            if refresh_result:
                test_results["token_refresh_test"] = True
                logger.info("Token refresh test passed")
            else:
                test_results["errors"].append("Token refresh failed")
            
            # Test logout
            logger.info("Testing logout...")
            auth_components.session_manager.clear_session()
            
            if not auth_components.session_manager.is_authenticated():
                test_results["logout_test"] = True
                logger.info("Logout test passed")
            else:
                test_results["errors"].append("Logout failed - session still active")
        
        else:
            test_results["errors"].append(f"Login failed: {login_result.error}")
    
    except Exception as e:
        test_results["errors"].append(f"Integration test exception: {e}")
        logger.error(f"Authentication integration test error: {e}")
    
    return test_results