# SessionManager Integration Guide

This guide explains how to integrate the enhanced SessionManager into the existing EdAgent Streamlit application.

## Overview

The enhanced SessionManager provides:

- **Robust Authentication State Management**: Secure token storage, automatic refresh, and session validation
- **Session Persistence**: Data persists across page reloads and browser sessions
- **User Preference Caching**: Efficient storage and retrieval of user preferences
- **Comprehensive Error Handling**: Graceful handling of authentication errors and session expiry
- **Security Features**: Token encryption, session timeout, and cleanup mechanisms

## Key Components

### 1. SessionManager Class

The main class that handles all session-related operations:

```python
from streamlit_session_manager import SessionManager, UserInfo, UserPreferences

# Initialize session manager
session_manager = SessionManager(session_timeout_minutes=480)  # 8 hours
```

### 2. Data Classes

- **UserInfo**: Stores user profile information
- **UserPreferences**: Manages user learning preferences and settings
- **SessionState**: Enum for different session states

## Integration Steps

### Step 1: Replace Basic Session Management

**Before (in streamlit_app.py):**
```python
def initialize_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    # ... more manual initialization
```

**After:**
```python
from streamlit_session_manager import SessionManager, UserInfo, UserPreferences, SessionState

class EdAgentApp:
    def __init__(self):
        self.session_manager = SessionManager(session_timeout_minutes=480)
        self.session_manager.load_session_state()
    
    def run(self):
        session_state = self.session_manager.get_session_state()
        
        if session_state == SessionState.UNAUTHENTICATED:
            self.show_authentication()
        elif session_state == SessionState.TOKEN_EXPIRED:
            self.handle_token_expiry()
        elif session_state == SessionState.TOKEN_REFRESH_NEEDED:
            self.handle_token_refresh()
        else:
            self.show_main_app()
```

### Step 2: Update Authentication Flow

**Enhanced Login Function:**
```python
def handle_login(self, email: str, password: str) -> bool:
    try:
        # Call API for authentication
        auth_result = await self.api_client.login_user(email, password)
        
        if auth_result.success:
            # Create user info object
            user_info = UserInfo(
                user_id=auth_result.user_id,
                email=auth_result.email,
                name=auth_result.name,
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            
            # Store authentication data securely
            self.session_manager.set_auth_data(
                user_info=user_info,
                access_token=auth_result.access_token,
                refresh_token=auth_result.refresh_token,
                expires_at=auth_result.expires_at
            )
            
            return True
        else:
            st.error(f"Login failed: {auth_result.error}")
            return False
            
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False
```

### Step 3: Implement Token Management

**Automatic Token Refresh:**
```python
def handle_token_refresh(self):
    """Handle automatic token refresh"""
    try:
        # Attempt to refresh token
        success = await self.api_client.refresh_token()
        
        if success:
            st.success("Session refreshed successfully!")
            st.rerun()
        else:
            # Refresh failed, require re-authentication
            self.session_manager.handle_auth_error()
            
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        self.session_manager.handle_auth_error()
```

### Step 4: Update API Client Integration

**Enhanced API Client Constructor:**
```python
class EnhancedEdAgentAPI:
    def __init__(self, base_url: str, session_manager: SessionManager):
        self.base_url = base_url
        self.session_manager = session_manager
        # ... rest of initialization
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        headers = {"Content-Type": "application/json"}
        
        if self.session_manager.is_authenticated():
            token = self.session_manager.get_auth_token()
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def _handle_auth_error(self, error: APIError):
        """Handle authentication errors"""
        if error.error_type == APIErrorType.AUTHENTICATION_ERROR:
            self.session_manager.handle_auth_error()
```

### Step 5: Implement User Preferences

**User Preferences Management:**
```python
def setup_user_preferences(self):
    """Setup user preferences interface"""
    preferences = self.session_manager.get_user_preferences()
    
    if not preferences:
        # Initialize default preferences
        preferences = UserPreferences(
            learning_style="visual",
            time_commitment="5-10",
            budget_preference="free",
            theme="light"
        )
        self.session_manager.update_user_preferences(preferences)
    
    # Show preferences form
    with st.form("preferences_form"):
        learning_style = st.selectbox(
            "Learning Style",
            ["visual", "auditory", "kinesthetic", "reading"],
            index=["visual", "auditory", "kinesthetic", "reading"].index(preferences.learning_style)
        )
        
        time_commitment = st.selectbox(
            "Time Commitment",
            ["1-5", "5-10", "10-20", "20+"],
            index=["1-5", "5-10", "10-20", "20+"].index(preferences.time_commitment)
        )
        
        if st.form_submit_button("Save Preferences"):
            preferences.learning_style = learning_style
            preferences.time_commitment = time_commitment
            self.session_manager.update_user_preferences(preferences)
            st.success("Preferences saved!")
```

### Step 6: Add Caching for Performance

**Efficient Data Caching:**
```python
def get_user_learning_paths(self, user_id: str):
    """Get learning paths with caching"""
    cache_key = f"learning_paths_{user_id}"
    
    # Try to get from cache first
    cached_paths = self.session_manager.get_cached_data(cache_key)
    if cached_paths:
        return cached_paths
    
    # Fetch from API if not cached
    try:
        paths = await self.api_client.get_user_learning_paths(user_id)
        
        # Cache for 30 minutes
        self.session_manager.set_cached_data(cache_key, paths, ttl_hours=0.5)
        
        return paths
    except Exception as e:
        st.error(f"Failed to load learning paths: {e}")
        return []
```

### Step 7: Implement Session Monitoring

**Session Status Display:**
```python
def show_session_status(self):
    """Show session status in sidebar"""
    with st.sidebar:
        st.subheader("Session Status")
        
        if self.session_manager.is_authenticated():
            current_user = self.session_manager.get_current_user()
            st.success(f"✅ Logged in as {current_user.name}")
            
            # Show time until token expiry
            time_until_expiry = self.session_manager.get_time_until_token_expiry()
            if time_until_expiry:
                hours = int(time_until_expiry.total_seconds() // 3600)
                minutes = int((time_until_expiry.total_seconds() % 3600) // 60)
                st.info(f"Session expires in: {hours}h {minutes}m")
            
            # Show refresh warning if needed
            if self.session_manager.needs_token_refresh():
                st.warning("⚠️ Session will expire soon")
        else:
            st.error("❌ Not authenticated")
```

## Error Handling Best Practices

### 1. Authentication Errors
```python
def handle_api_error(self, error: APIError, context: str):
    """Handle API errors with user-friendly messages"""
    if error.error_type == APIErrorType.AUTHENTICATION_ERROR:
        st.error("🔐 Your session has expired. Please log in again.")
        self.session_manager.handle_auth_error()
    elif error.error_type == APIErrorType.RATE_LIMIT_ERROR:
        retry_after = error.retry_after or 60
        st.warning(f"⏱️ Rate limit reached. Please wait {retry_after} seconds.")
    else:
        st.error(f"❌ {error.message}")
```

### 2. Session Validation
```python
def validate_session_before_api_call(self):
    """Validate session before making API calls"""
    if not self.session_manager.validate_session():
        st.error("Invalid session detected. Please log in again.")
        self.session_manager.clear_session()
        st.rerun()
        return False
    
    if self.session_manager.needs_token_refresh():
        # Attempt automatic refresh
        self.handle_token_refresh()
        return False
    
    return True
```

## Security Considerations

### 1. Token Storage
- Tokens are automatically encrypted using base64 encoding
- For production, implement proper encryption using cryptography libraries
- Tokens are cleared on logout and session expiry

### 2. Session Timeout
- Configurable session timeout (default 8 hours)
- Automatic cleanup of expired data
- Session validation on each request

### 3. Data Protection
- User preferences are stored securely in session state
- Cached data has TTL to prevent stale data
- Sensitive data is cleared on authentication errors

## Testing

The SessionManager includes comprehensive unit tests covering:

- Authentication state management
- Token expiry and refresh logic
- Session validation and cleanup
- User preference management
- Caching mechanisms
- Error handling scenarios

Run tests with:
```bash
python -m pytest test_session_manager.py -v
```

## Migration Checklist

- [ ] Replace manual session state initialization with SessionManager
- [ ] Update authentication flow to use UserInfo and secure token storage
- [ ] Implement automatic token refresh logic
- [ ] Add user preferences management
- [ ] Update API client to use SessionManager for authentication
- [ ] Add session status monitoring in UI
- [ ] Implement proper error handling for authentication errors
- [ ] Add caching for frequently accessed data
- [ ] Test session persistence across page reloads
- [ ] Verify security measures are in place

## Example Usage

See `streamlit_session_integration_example.py` for a complete working example of how to integrate the SessionManager into a Streamlit application.

## Performance Benefits

- **Reduced API Calls**: Intelligent caching reduces redundant API requests
- **Faster Page Loads**: Session data persists across page reloads
- **Better User Experience**: Automatic token refresh prevents unexpected logouts
- **Memory Efficiency**: Automatic cleanup of expired data

## Troubleshooting

### Common Issues

1. **Session not persisting**: Ensure `load_session_state()` is called on app initialization
2. **Token refresh failing**: Check API client token refresh implementation
3. **Preferences not saving**: Verify UserPreferences serialization
4. **Cache not working**: Check TTL settings and cache key naming

### Debug Information

Use `session_manager.get_session_info()` to get comprehensive session debugging information:

```python
debug_info = session_manager.get_session_info()
st.json(debug_info)
```

This provides information about authentication status, token expiry, cached data, and more.