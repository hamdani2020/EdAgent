"""
Unit tests for the SessionManager class

Tests cover:
- Authentication state management
- Token management and refresh logic
- Session validation and cleanup
- User preference caching
- Session persistence across page reloads
- Edge cases and error handling
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import base64

# Mock streamlit before importing our modules
import sys
sys.modules['streamlit'] = Mock()

from streamlit_session_manager import (
    SessionManager, 
    UserInfo, 
    UserPreferences, 
    SessionState,
    SessionData
)


class TestSessionManager(unittest.TestCase):
    """Test cases for SessionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock streamlit session state
        self.mock_session_state = {}
        
        # Patch streamlit.session_state
        self.session_state_patcher = patch('streamlit_session_manager.st.session_state', self.mock_session_state)
        self.session_state_patcher.start()
        
        # Create SessionManager instance
        self.session_manager = SessionManager(session_timeout_minutes=60)
        
        # Test user data
        self.test_user = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        self.test_preferences = UserPreferences(
            career_goals=["Software Developer", "Data Scientist"],
            learning_style="visual",
            time_commitment="10-20",
            preferred_platforms=["coursera", "udemy"]
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.session_state_patcher.stop()
    
    def test_initialization(self):
        """Test SessionManager initialization"""
        # Check that session state is properly initialized
        self.assertTrue(self.mock_session_state.get("edagent_session_initialized"))
        self.assertIsNotNone(self.mock_session_state.get("edagent_session_last_activity"))
        self.assertEqual(self.mock_session_state.get("edagent_session_cached_data"), {})
    
    def test_authentication_state_management(self):
        """Test authentication state management"""
        # Initially not authenticated
        self.assertFalse(self.session_manager.is_authenticated())
        self.assertEqual(self.session_manager.get_session_state(), SessionState.UNAUTHENTICATED)
        
        # Set authentication data
        access_token = "test_access_token"
        expires_at = datetime.now() + timedelta(hours=1)
        
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token=access_token,
            expires_at=expires_at
        )
        
        # Should now be authenticated
        self.assertTrue(self.session_manager.is_authenticated())
        self.assertEqual(self.session_manager.get_session_state(), SessionState.AUTHENTICATED)
        
        # Check user info retrieval
        current_user = self.session_manager.get_current_user()
        self.assertIsNotNone(current_user)
        self.assertEqual(current_user.user_id, self.test_user.user_id)
        self.assertEqual(current_user.email, self.test_user.email)
        
        # Check token retrieval
        retrieved_token = self.session_manager.get_auth_token()
        self.assertEqual(retrieved_token, access_token)
    
    def test_token_encryption_decryption(self):
        """Test token encryption and decryption"""
        original_token = "test_access_token_12345"
        
        # Test encryption
        encrypted = self.session_manager._encrypt_token(original_token)
        self.assertNotEqual(encrypted, original_token)
        
        # Test decryption
        decrypted = self.session_manager._decrypt_token(encrypted)
        self.assertEqual(decrypted, original_token)
        
        # Test with empty token
        self.assertEqual(self.session_manager._encrypt_token(""), "")
        self.assertEqual(self.session_manager._decrypt_token(""), "")
    
    def test_token_expiry_management(self):
        """Test token expiry detection and management"""
        # Set up authenticated session with token expiring soon
        access_token = "test_token"
        expires_at = datetime.now() + timedelta(minutes=2)  # Expires in 2 minutes
        
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token=access_token,
            expires_at=expires_at
        )
        
        # Should not be expired yet
        self.assertFalse(self.session_manager.is_token_expired())
        
        # Should need refresh (within 5 minute threshold)
        self.assertTrue(self.session_manager.needs_token_refresh())
        self.assertEqual(self.session_manager.get_session_state(), SessionState.TOKEN_REFRESH_NEEDED)
        
        # Test with expired token
        expired_time = datetime.now() - timedelta(minutes=1)
        self.session_manager.update_token(access_token, expired_time)
        
        self.assertTrue(self.session_manager.is_token_expired())
        self.assertFalse(self.session_manager.is_authenticated())
    
    def test_session_timeout(self):
        """Test session timeout functionality"""
        # Set up authenticated session
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=2)
        )
        
        # Should be authenticated
        self.assertTrue(self.session_manager.is_authenticated())
        
        # Simulate old last activity (beyond timeout)
        old_activity = datetime.now() - timedelta(hours=2)
        self.mock_session_state[self.session_manager._get_session_key("last_activity")] = old_activity
        
        # Should now be expired due to inactivity
        self.assertTrue(self.session_manager.is_session_expired())
        self.assertFalse(self.session_manager.is_authenticated())
    
    def test_session_validation(self):
        """Test session validation logic"""
        # Valid session
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        self.assertTrue(self.session_manager.validate_session())
        
        # Invalid session - user info without token
        self.mock_session_state[self.session_manager._get_session_key("access_token")] = None
        self.assertFalse(self.session_manager.validate_session())
        
        # Invalid session - token without user info
        self.mock_session_state[self.session_manager._get_session_key("user_info")] = None
        self.mock_session_state[self.session_manager._get_session_key("access_token")] = "test_token"
        self.assertFalse(self.session_manager.validate_session())
    
    def test_session_cleanup(self):
        """Test session cleanup functionality"""
        # Set up session with data
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Add some cached data
        self.session_manager.set_cached_data("test_key", "test_value")
        
        # Verify data exists
        self.assertTrue(self.session_manager.is_authenticated())
        self.assertIsNotNone(self.session_manager.get_cached_data("test_key"))
        
        # Clear session
        self.session_manager.clear_session()
        
        # Verify data is cleared
        self.assertFalse(self.session_manager.is_authenticated())
        self.assertIsNone(self.session_manager.get_current_user())
        self.assertIsNone(self.session_manager.get_auth_token())
    
    def test_user_preferences_management(self):
        """Test user preferences caching and management"""
        # Initially no preferences
        self.assertIsNone(self.session_manager.get_user_preferences())
        
        # Set preferences
        self.session_manager.update_user_preferences(self.test_preferences)
        
        # Retrieve preferences
        retrieved_prefs = self.session_manager.get_user_preferences()
        self.assertIsNotNone(retrieved_prefs)
        self.assertEqual(retrieved_prefs.learning_style, "visual")
        self.assertEqual(retrieved_prefs.career_goals, ["Software Developer", "Data Scientist"])
        
        # Test individual preference access
        self.assertEqual(self.session_manager.get_preference("learning_style"), "visual")
        self.assertEqual(self.session_manager.get_preference("nonexistent", "default"), "default")
        
        # Test setting individual preference
        self.session_manager.set_preference("theme", "dark")
        updated_prefs = self.session_manager.get_user_preferences()
        self.assertEqual(updated_prefs.theme, "dark")
    
    def test_cached_data_management(self):
        """Test cached data storage and retrieval with TTL"""
        # Set cached data
        test_data = {"key": "value", "number": 42}
        self.session_manager.set_cached_data("test_cache", test_data, ttl_hours=1)
        
        # Retrieve cached data
        retrieved_data = self.session_manager.get_cached_data("test_cache")
        self.assertEqual(retrieved_data, test_data)
        
        # Test cache miss
        self.assertIsNone(self.session_manager.get_cached_data("nonexistent_key"))
        
        # Test cache expiry simulation
        # Manually set old timestamp
        cached_data = self.mock_session_state[self.session_manager._get_session_key("cached_data")]
        old_timestamp = (datetime.now() - timedelta(hours=2)).isoformat()
        cached_data["test_cache"]["timestamp"] = old_timestamp
        
        # Should return None for expired cache
        self.assertIsNone(self.session_manager.get_cached_data("test_cache"))
        
        # Clear specific cache key
        self.session_manager.set_cached_data("key1", "value1")
        self.session_manager.set_cached_data("key2", "value2")
        
        self.session_manager.clear_cached_data("key1")
        self.assertIsNone(self.session_manager.get_cached_data("key1"))
        self.assertIsNotNone(self.session_manager.get_cached_data("key2"))
        
        # Clear all cached data
        self.session_manager.clear_cached_data()
        self.assertIsNone(self.session_manager.get_cached_data("key2"))
    
    def test_navigation_state_management(self):
        """Test navigation state tracking"""
        # Default tab
        self.assertEqual(self.session_manager.get_current_tab(), "chat")
        self.assertIsNone(self.session_manager.get_previous_tab())
        
        # Set new tab
        self.session_manager.set_current_tab("assessments")
        self.assertEqual(self.session_manager.get_current_tab(), "assessments")
        self.assertEqual(self.session_manager.get_previous_tab(), "chat")
        
        # Set another tab
        self.session_manager.set_current_tab("learning_paths")
        self.assertEqual(self.session_manager.get_current_tab(), "learning_paths")
        self.assertEqual(self.session_manager.get_previous_tab(), "assessments")
    
    def test_ui_state_management(self):
        """Test UI state management"""
        # Test general UI state
        self.session_manager.set_ui_state("show_modal", True)
        self.assertTrue(self.session_manager.get_ui_state("show_modal"))
        self.assertIsNone(self.session_manager.get_ui_state("nonexistent"))
        self.assertEqual(self.session_manager.get_ui_state("nonexistent", "default"), "default")
        
        # Test loading states
        self.assertFalse(self.session_manager.get_loading_state("api_call"))
        
        self.session_manager.set_loading_state("api_call", True)
        self.assertTrue(self.session_manager.get_loading_state("api_call"))
        
        self.session_manager.set_loading_state("api_call", False)
        self.assertFalse(self.session_manager.get_loading_state("api_call"))
    
    def test_token_refresh_logic(self):
        """Test token refresh detection logic"""
        # Set token that expires in 3 minutes (within refresh threshold)
        expires_at = datetime.now() + timedelta(minutes=3)
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=expires_at
        )
        
        # Should need refresh
        self.assertTrue(self.session_manager.needs_token_refresh())
        
        # Update with fresh token (expires in 30 minutes)
        fresh_expires_at = datetime.now() + timedelta(minutes=30)
        self.session_manager.update_token("fresh_token", fresh_expires_at)
        
        # Should not need refresh
        self.assertFalse(self.session_manager.needs_token_refresh())
        
        # Check time until expiry
        time_until_expiry = self.session_manager.get_time_until_token_expiry()
        self.assertIsNotNone(time_until_expiry)
        self.assertGreater(time_until_expiry.total_seconds(), 25 * 60)  # More than 25 minutes
    
    def test_auth_error_handling(self):
        """Test authentication error handling"""
        # Set up authenticated session
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        self.assertTrue(self.session_manager.is_authenticated())
        
        # Mock streamlit error and rerun
        with patch('streamlit_session_manager.st.error') as mock_error, \
             patch('streamlit_session_manager.st.rerun') as mock_rerun:
            
            self.session_manager.handle_auth_error()
            
            # Should clear session and show error
            self.assertFalse(self.session_manager.is_authenticated())
            mock_error.assert_called_once()
            mock_rerun.assert_called_once()
    
    def test_session_persistence_methods(self):
        """Test session persistence methods"""
        # Set up session
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Test save session state
        self.session_manager.save_session_state()
        # Should update last activity
        last_activity = self.mock_session_state.get(self.session_manager._get_session_key("last_activity"))
        self.assertIsNotNone(last_activity)
        
        # Test load session state with valid session
        self.session_manager.load_session_state()
        self.assertTrue(self.session_manager.is_authenticated())
        
        # Test load session state with invalid session
        # Corrupt the session by removing user info
        self.mock_session_state[self.session_manager._get_session_key("user_info")] = None
        
        self.session_manager.load_session_state()
        # Should clear invalid session
        self.assertFalse(self.session_manager.is_authenticated())
    
    def test_cleanup_expired_data(self):
        """Test cleanup of expired cached data"""
        # Add some cached data with different timestamps
        current_time = datetime.now()
        old_time = current_time - timedelta(hours=2)
        
        cached_data = {
            "fresh_data": {
                "value": "fresh",
                "timestamp": current_time.isoformat(),
                "ttl_hours": 1
            },
            "expired_data": {
                "value": "expired",
                "timestamp": old_time.isoformat(),
                "ttl_hours": 1
            }
        }
        
        self.mock_session_state[self.session_manager._get_session_key("cached_data")] = cached_data
        
        # Run cleanup
        self.session_manager.cleanup_expired_data()
        
        # Check that expired data is removed
        remaining_data = self.mock_session_state[self.session_manager._get_session_key("cached_data")]
        self.assertIn("fresh_data", remaining_data)
        self.assertNotIn("expired_data", remaining_data)
    
    def test_session_info_retrieval(self):
        """Test session information retrieval for debugging"""
        # Set up session
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Get session info
        info = self.session_manager.get_session_info()
        
        # Verify info structure
        self.assertIn("is_authenticated", info)
        self.assertIn("session_state", info)
        self.assertIn("user_id", info)
        self.assertIn("token_expires_at", info)
        self.assertIn("current_tab", info)
        
        self.assertTrue(info["is_authenticated"])
        self.assertEqual(info["user_id"], self.test_user.user_id)
        self.assertEqual(info["session_state"], "authenticated")
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Test with None values
        self.session_manager.set_auth_data(
            user_info=self.test_user,
            access_token="test_token"
        )
        
        # Should handle None expires_at gracefully
        self.assertIsNotNone(self.session_manager.get_token_expiry_time())
        
        # Test token decryption with invalid data
        invalid_encrypted = "invalid_base64_data"
        decrypted = self.session_manager._decrypt_token(invalid_encrypted)
        self.assertEqual(decrypted, "")
        
        # Test preferences with None values
        self.session_manager.update_user_preferences(None)
        # Should not crash
        
        # Test cache operations with invalid data
        self.session_manager.set_cached_data("test", None)
        self.assertIsNone(self.session_manager.get_cached_data("test"))


class TestUserInfo(unittest.TestCase):
    """Test cases for UserInfo data class"""
    
    def test_user_info_serialization(self):
        """Test UserInfo to_dict and from_dict methods"""
        user = UserInfo(
            user_id="test_123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Test to_dict
        user_dict = user.to_dict()
        self.assertIn("user_id", user_dict)
        self.assertIn("email", user_dict)
        self.assertIn("created_at", user_dict)
        self.assertIsInstance(user_dict["created_at"], str)  # Should be ISO string
        
        # Test from_dict
        restored_user = UserInfo.from_dict(user_dict)
        self.assertEqual(restored_user.user_id, user.user_id)
        self.assertEqual(restored_user.email, user.email)
        self.assertIsInstance(restored_user.created_at, datetime)


class TestUserPreferences(unittest.TestCase):
    """Test cases for UserPreferences data class"""
    
    def test_user_preferences_defaults(self):
        """Test UserPreferences default values"""
        prefs = UserPreferences()
        
        self.assertEqual(prefs.career_goals, [])
        self.assertEqual(prefs.learning_style, "visual")
        self.assertEqual(prefs.preferred_platforms, [])
        self.assertTrue(prefs.notifications_enabled)
    
    def test_user_preferences_serialization(self):
        """Test UserPreferences serialization"""
        prefs = UserPreferences(
            career_goals=["Developer", "Manager"],
            learning_style="auditory",
            preferred_platforms=["coursera", "udemy"]
        )
        
        # Test to_dict
        prefs_dict = prefs.to_dict()
        self.assertEqual(prefs_dict["career_goals"], ["Developer", "Manager"])
        self.assertEqual(prefs_dict["learning_style"], "auditory")
        
        # Test from_dict
        restored_prefs = UserPreferences.from_dict(prefs_dict)
        self.assertEqual(restored_prefs.career_goals, prefs.career_goals)
        self.assertEqual(restored_prefs.learning_style, prefs.learning_style)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)