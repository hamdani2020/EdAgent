"""
Enhanced Session Management System for EdAgent Streamlit Application

This module provides comprehensive session management including:
- Authentication state management
- Secure token storage and automatic refresh
- Session persistence across page reloads
- User preference caching
- Session validation and cleanup
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import base64

import streamlit as st


def safe_parse_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """
    Safely parse datetime strings, handling various formats including ISO with 'Z' suffix.
    Returns timezone-naive datetime for consistency.
    
    Args:
        datetime_str: The datetime string to parse
        
    Returns:
        Parsed datetime object (timezone-naive) or None if parsing fails
    """
    if not datetime_str:
        return None
    
    try:
        # Handle 'Z' suffix by replacing it with '+00:00'
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str[:-1] + '+00:00'
        
        # Try parsing with timezone info first
        try:
            dt = datetime.fromisoformat(datetime_str)
            # Convert to naive datetime (assume UTC if timezone-aware)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            # Fallback: try without timezone info
            if '+' in datetime_str or datetime_str.endswith('Z'):
                datetime_str = datetime_str.split('+')[0].split('Z')[0]
            return datetime.fromisoformat(datetime_str)
    except (ValueError, AttributeError) as e:
        logging.warning(f"Failed to parse datetime string '{datetime_str}': {e}")
        return None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state enumeration"""
    UNAUTHENTICATED = "unauthenticated"
    AUTHENTICATED = "authenticated"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_REFRESH_NEEDED = "token_refresh_needed"
    INVALID = "invalid"


@dataclass
class UserInfo:
    """User information data class"""
    user_id: str
    email: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.last_active:
            data['last_active'] = self.last_active.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInfo':
        """Create UserInfo from dictionary"""
        # Convert ISO strings back to datetime objects
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = safe_parse_datetime(data['created_at'])
        if data.get('last_active') and isinstance(data['last_active'], str):
            data['last_active'] = safe_parse_datetime(data['last_active'])
        return cls(**data)


@dataclass
class UserPreferences:
    """User preferences data class"""
    career_goals: List[str] = None
    learning_style: str = "visual"
    time_commitment: str = "5-10"
    budget_preference: str = "free"
    preferred_platforms: List[str] = None
    content_types: List[str] = None
    difficulty_preference: str = "intermediate"
    theme: str = "light"
    notifications_enabled: bool = True
    privacy_level: str = "standard"
    
    def __post_init__(self):
        if self.career_goals is None:
            self.career_goals = []
        if self.preferred_platforms is None:
            self.preferred_platforms = []
        if self.content_types is None:
            self.content_types = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create UserPreferences from dictionary"""
        return cls(**data)


@dataclass
class SessionData:
    """Complete session data structure"""
    user_info: Optional[UserInfo] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    session_created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    preferences: Optional[UserPreferences] = None
    cached_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cached_data is None:
            self.cached_data = {}
        if self.session_created_at is None:
            self.session_created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()


class SessionManager:
    """
    Comprehensive session management system for EdAgent Streamlit application
    
    Features:
    - Secure authentication state management
    - Automatic token refresh
    - Session persistence across page reloads
    - User preference caching
    - Session validation and cleanup
    """
    
    def __init__(self, session_timeout_minutes: int = 480):  # 8 hours default
        self.session_key_prefix = "edagent_session_"
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.token_refresh_threshold = timedelta(minutes=5)  # Refresh token 5 minutes before expiry
        
        # Initialize session state if not exists
        self._initialize_session_state()
        
        logger.info("SessionManager initialized")
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state with default values"""
        default_keys = {
            f"{self.session_key_prefix}initialized": False,
            f"{self.session_key_prefix}user_info": None,
            f"{self.session_key_prefix}access_token": None,
            f"{self.session_key_prefix}refresh_token": None,
            f"{self.session_key_prefix}token_expires_at": None,
            f"{self.session_key_prefix}session_created_at": None,
            f"{self.session_key_prefix}last_activity": None,
            f"{self.session_key_prefix}preferences": None,
            f"{self.session_key_prefix}cached_data": {},
            f"{self.session_key_prefix}navigation_state": {"current_tab": "chat", "previous_tab": None},
            f"{self.session_key_prefix}ui_state": {
                "show_profile_setup": False,
                "show_error_details": False,
                "loading_states": {},
                "error_messages": []
            }
        }
        
        for key, default_value in default_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Mark as initialized
        st.session_state[f"{self.session_key_prefix}initialized"] = True
        
        # Update last activity
        self._update_last_activity()
    
    def _get_session_key(self, key: str) -> str:
        """Get prefixed session key"""
        return f"{self.session_key_prefix}{key}"
    
    def _update_last_activity(self) -> None:
        """Update last activity timestamp"""
        st.session_state[self._get_session_key("last_activity")] = datetime.now()
    
    def _encrypt_token(self, token: str) -> str:
        """Simple token encryption for storage (basic obfuscation)"""
        if not token:
            return token
        
        # Simple base64 encoding for basic obfuscation
        # In production, use proper encryption
        encoded = base64.b64encode(token.encode()).decode()
        return encoded
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt stored token"""
        if not encrypted_token:
            return encrypted_token
        
        try:
            decoded = base64.b64decode(encrypted_token.encode()).decode()
            return decoded
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            return ""
    
    # Authentication State Management
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        user_info = st.session_state.get(self._get_session_key("user_info"))
        access_token = st.session_state.get(self._get_session_key("access_token"))
        
        if not user_info or not access_token:
            return False
        
        # Check if session is expired
        if self.is_session_expired():
            logger.info("Session expired")
            return False
        
        # Check if token is expired
        if self.is_token_expired():
            logger.info("Token expired")
            return False
        
        self._update_last_activity()
        return True
    
    def get_session_state(self) -> SessionState:
        """Get current session state"""
        user_info = st.session_state.get(self._get_session_key("user_info"))
        access_token = st.session_state.get(self._get_session_key("access_token"))
        
        # If no user info or token, return unauthenticated
        if not user_info or not access_token:
            return SessionState.UNAUTHENTICATED
        
        # Check token expiry
        if self.is_token_expired():
            return SessionState.TOKEN_EXPIRED
        
        # Check session expiry
        if self.is_session_expired():
            return SessionState.TOKEN_EXPIRED
        
        # Check if token needs refresh
        if self.needs_token_refresh():
            return SessionState.TOKEN_REFRESH_NEEDED
        
        return SessionState.AUTHENTICATED
    
    def get_current_user(self) -> Optional[UserInfo]:
        """Get current user information"""
        user_data = st.session_state.get(self._get_session_key("user_info"))
        if user_data:
            if isinstance(user_data, dict):
                return UserInfo.from_dict(user_data)
            return user_data
        return None
    
    def get_auth_token(self) -> Optional[str]:
        """Get current authentication token"""
        encrypted_token = st.session_state.get(self._get_session_key("access_token"))
        if encrypted_token:
            return self._decrypt_token(encrypted_token)
        return None
    
    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token"""
        encrypted_token = st.session_state.get(self._get_session_key("refresh_token"))
        if encrypted_token:
            return self._decrypt_token(encrypted_token)
        return None
    
    def set_auth_data(
        self, 
        user_info: UserInfo, 
        access_token: str, 
        refresh_token: str = None,
        expires_at: datetime = None
    ) -> None:
        """Store authentication data in session"""
        try:
            # Store user info
            if isinstance(user_info, UserInfo):
                st.session_state[self._get_session_key("user_info")] = user_info.to_dict()
                # Also store user_id directly for easy access
                st.session_state.user_id = user_info.user_id
                st.session_state.user_email = user_info.email
                st.session_state.user_name = user_info.name
            else:
                st.session_state[self._get_session_key("user_info")] = user_info
                # Also store user_id directly for easy access
                if isinstance(user_info, dict):
                    st.session_state.user_id = user_info.get('user_id')
                    st.session_state.user_email = user_info.get('email')
                    st.session_state.user_name = user_info.get('name')
            
            # Store encrypted tokens
            st.session_state[self._get_session_key("access_token")] = self._encrypt_token(access_token)
            if refresh_token:
                st.session_state[self._get_session_key("refresh_token")] = self._encrypt_token(refresh_token)
            
            # Store token expiry
            if expires_at:
                st.session_state[self._get_session_key("token_expires_at")] = expires_at
            else:
                # Default to 1 hour if not specified
                st.session_state[self._get_session_key("token_expires_at")] = datetime.now() + timedelta(hours=1)
            
            # Update session timestamps
            st.session_state[self._get_session_key("session_created_at")] = datetime.now()
            self._update_last_activity()
            
            logger.info(f"Authentication data stored for user {user_info.user_id if hasattr(user_info, 'user_id') else 'unknown'}")
            
        except Exception as e:
            logger.error(f"Failed to store authentication data: {e}")
            raise
    
    def clear_session(self) -> None:
        """Clear all session data"""
        try:
            # Get all session keys to remove
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith(self.session_key_prefix)]
            
            # Remove all session keys
            for key in keys_to_remove:
                del st.session_state[key]
            
            # Also clear direct user info keys
            for key in ['user_id', 'user_email', 'user_name']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Reinitialize session state
            self._initialize_session_state()
            
            logger.info("Session data cleared and reinitialized")
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
    
    # Token Management
    
    def is_token_expired(self) -> bool:
        """Check if authentication token is expired"""
        expires_at = st.session_state.get(self._get_session_key("token_expires_at"))
        if not expires_at:
            return True
        
        # Ensure timezone-naive comparison
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        
        # Add small buffer to account for network delays
        buffer = timedelta(seconds=30)
        return datetime.now() >= (expires_at - buffer)
    
    def needs_token_refresh(self) -> bool:
        """Check if token needs refresh soon"""
        expires_at = st.session_state.get(self._get_session_key("token_expires_at"))
        if not expires_at:
            return True
        
        # Ensure timezone-naive comparison
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        
        return datetime.now() >= (expires_at - self.token_refresh_threshold)
    
    def get_token_expiry_time(self) -> Optional[datetime]:
        """Get token expiry time"""
        return st.session_state.get(self._get_session_key("token_expires_at"))
    
    def get_time_until_token_expiry(self) -> Optional[timedelta]:
        """Get time remaining until token expires"""
        expires_at = self.get_token_expiry_time()
        if expires_at:
            # Ensure timezone-naive comparison
            if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
                expires_at = expires_at.replace(tzinfo=None)
            return expires_at - datetime.now()
        return None
    
    def update_token(self, access_token: str, expires_at: datetime = None, refresh_token: str = None) -> None:
        """Update authentication token"""
        try:
            st.session_state[self._get_session_key("access_token")] = self._encrypt_token(access_token)
            
            if expires_at:
                st.session_state[self._get_session_key("token_expires_at")] = expires_at
            
            if refresh_token:
                st.session_state[self._get_session_key("refresh_token")] = self._encrypt_token(refresh_token)
            
            self._update_last_activity()
            logger.info("Authentication token updated")
            
        except Exception as e:
            logger.error(f"Failed to update token: {e}")
            raise
    
    # Session Validation and Cleanup
    
    def is_session_expired(self) -> bool:
        """Check if session has expired due to inactivity"""
        last_activity = st.session_state.get(self._get_session_key("last_activity"))
        if not last_activity:
            return True
        
        # Ensure timezone-naive comparison
        if hasattr(last_activity, 'tzinfo') and last_activity.tzinfo is not None:
            last_activity = last_activity.replace(tzinfo=None)
        
        return datetime.now() - last_activity > self.session_timeout
    
    def validate_session(self) -> bool:
        """Validate current session integrity"""
        try:
            # Check if session is initialized
            if not st.session_state.get(self._get_session_key("initialized")):
                logger.warning("Session not properly initialized")
                return False
            
            # Check for required session data consistency
            user_info = st.session_state.get(self._get_session_key("user_info"))
            access_token = st.session_state.get(self._get_session_key("access_token"))
            
            if user_info and not access_token:
                logger.warning("User info exists but no access token")
                return False
            
            if access_token and not user_info:
                logger.warning("Access token exists but no user info")
                return False
            
            # Check session expiry
            if self.is_session_expired():
                logger.info("Session expired due to inactivity")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False
    
    def cleanup_expired_data(self) -> None:
        """Clean up expired session data"""
        try:
            # Clear cached data older than 1 hour
            cached_data = st.session_state.get(self._get_session_key("cached_data"), {})
            current_time = datetime.now()
            
            expired_keys = []
            for key, data in cached_data.items():
                if isinstance(data, dict) and 'timestamp' in data:
                    cache_time = safe_parse_datetime(data['timestamp'])
                    if current_time - cache_time > timedelta(hours=1):
                        expired_keys.append(key)
            
            for key in expired_keys:
                del cached_data[key]
            
            st.session_state[self._get_session_key("cached_data")] = cached_data
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
    
    def handle_auth_error(self) -> None:
        """Handle authentication errors"""
        logger.warning("Authentication error occurred, clearing session")
        self.clear_session()
        
        # Show user-friendly message
        st.error("🔐 Your session has expired. Please log in again.")
        
        # Force page refresh to show login form
        st.rerun()
    
    # User Preferences Management
    
    def get_user_preferences(self) -> Optional[UserPreferences]:
        """Get user preferences"""
        prefs_data = st.session_state.get(self._get_session_key("preferences"))
        if prefs_data:
            if isinstance(prefs_data, dict):
                return UserPreferences.from_dict(prefs_data)
            return prefs_data
        return None
    
    def update_user_preferences(self, preferences: UserPreferences) -> None:
        """Update user preferences"""
        try:
            if isinstance(preferences, UserPreferences):
                st.session_state[self._get_session_key("preferences")] = preferences.to_dict()
            else:
                st.session_state[self._get_session_key("preferences")] = preferences
            
            self._update_last_activity()
            logger.info("User preferences updated")
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            raise
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get specific preference value"""
        preferences = self.get_user_preferences()
        if preferences:
            return getattr(preferences, key, default)
        return default
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set specific preference value"""
        preferences = self.get_user_preferences() or UserPreferences()
        setattr(preferences, key, value)
        self.update_user_preferences(preferences)
    
    # Session Data Persistence
    
    def save_session_state(self) -> None:
        """Save current session state (for persistence across page reloads)"""
        try:
            # Session state is automatically persisted by Streamlit
            # This method can be extended for additional persistence mechanisms
            self._update_last_activity()
            logger.debug("Session state saved")
            
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
    
    def load_session_state(self) -> None:
        """Load session state (for restoration after page reload)"""
        try:
            # Validate and cleanup session on load
            if not self.validate_session():
                logger.info("Invalid session detected, clearing")
                self.clear_session()
                return
            
            # Cleanup expired data
            self.cleanup_expired_data()
            
            # Update last activity
            self._update_last_activity()
            
            logger.debug("Session state loaded and validated")
            
        except Exception as e:
            logger.error(f"Failed to load session state: {e}")
            self.clear_session()
    
    def clear_cached_data(self, cache_key: str = None) -> None:
        """Clear cached data"""
        try:
            cached_data = st.session_state.get(self._get_session_key("cached_data"), {})
            
            if cache_key:
                if cache_key in cached_data:
                    del cached_data[cache_key]
                    logger.info(f"Cleared cache key: {cache_key}")
            else:
                cached_data.clear()
                logger.info("Cleared all cached data")
            
            st.session_state[self._get_session_key("cached_data")] = cached_data
            
        except Exception as e:
            logger.error(f"Failed to clear cached data: {e}")
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            cached_data = st.session_state.get(self._get_session_key("cached_data"), {})
            data = cached_data.get(cache_key)
            
            if data and isinstance(data, dict) and 'timestamp' in data:
                # Check if cache is still valid (1 hour TTL)
                cache_time = safe_parse_datetime(data['timestamp'])
                if cache_time:
                    # Ensure timezone-naive comparison
                    if hasattr(cache_time, 'tzinfo') and cache_time.tzinfo is not None:
                        cache_time = cache_time.replace(tzinfo=None)
                    
                    if datetime.now() - cache_time > timedelta(hours=1):
                        del cached_data[cache_key]
                        st.session_state[self._get_session_key("cached_data")] = cached_data
                        return None
                
                return data.get('value')
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get cached data: {e}")
            return None
    
    def set_cached_data(self, cache_key: str, value: Any, ttl_hours: int = 1) -> None:
        """Set cached data with TTL"""
        try:
            cached_data = st.session_state.get(self._get_session_key("cached_data"), {})
            
            cached_data[cache_key] = {
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'ttl_hours': ttl_hours
            }
            
            st.session_state[self._get_session_key("cached_data")] = cached_data
            logger.debug(f"Cached data set for key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to set cached data: {e}")
    
    # Navigation State Management
    
    def get_current_tab(self) -> str:
        """Get current navigation tab"""
        nav_state = st.session_state.get(self._get_session_key("navigation_state"), {})
        return nav_state.get("current_tab", "chat")
    
    def set_current_tab(self, tab: str) -> None:
        """Set current navigation tab"""
        nav_state = st.session_state.get(self._get_session_key("navigation_state"), {})
        nav_state["previous_tab"] = nav_state.get("current_tab")
        nav_state["current_tab"] = tab
        st.session_state[self._get_session_key("navigation_state")] = nav_state
    
    def get_previous_tab(self) -> Optional[str]:
        """Get previous navigation tab"""
        nav_state = st.session_state.get(self._get_session_key("navigation_state"), {})
        return nav_state.get("previous_tab")
    
    # UI State Management
    
    def get_ui_state(self, key: str, default: Any = None) -> Any:
        """Get UI state value"""
        ui_state = st.session_state.get(self._get_session_key("ui_state"), {})
        return ui_state.get(key, default)
    
    def set_ui_state(self, key: str, value: Any) -> None:
        """Set UI state value"""
        ui_state = st.session_state.get(self._get_session_key("ui_state"), {})
        ui_state[key] = value
        st.session_state[self._get_session_key("ui_state")] = ui_state
    
    def get_loading_state(self, operation: str) -> bool:
        """Get loading state for specific operation"""
        loading_states = self.get_ui_state("loading_states", {})
        return loading_states.get(operation, False)
    
    def set_loading_state(self, operation: str, is_loading: bool) -> None:
        """Set loading state for specific operation"""
        loading_states = self.get_ui_state("loading_states", {})
        loading_states[operation] = is_loading
        self.set_ui_state("loading_states", loading_states)
    
    # Utility Methods
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get comprehensive session information for debugging"""
        return {
            "is_authenticated": self.is_authenticated(),
            "session_state": self.get_session_state().value,
            "user_id": self.get_current_user().user_id if self.get_current_user() else None,
            "token_expires_at": self.get_token_expiry_time(),
            "time_until_expiry": str(self.get_time_until_token_expiry()) if self.get_time_until_token_expiry() else None,
            "needs_refresh": self.needs_token_refresh(),
            "session_created_at": st.session_state.get(self._get_session_key("session_created_at")),
            "last_activity": st.session_state.get(self._get_session_key("last_activity")),
            "current_tab": self.get_current_tab(),
            "cached_data_keys": list(st.session_state.get(self._get_session_key("cached_data"), {}).keys())
        }
    
    def __str__(self) -> str:
        """String representation of session manager"""
        info = self.get_session_info()
        return f"SessionManager(authenticated={info['is_authenticated']}, state={info['session_state']}, user_id={info['user_id']})"