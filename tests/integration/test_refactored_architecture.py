"""
Integration Tests for Refactored EdAgent Streamlit Architecture

This module tests the complete user workflows and system interactions
to ensure the refactored architecture works correctly end-to-end.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the refactored components
from edagent_streamlit.core.config import StreamlitConfig, Environment
from edagent_streamlit.core.session_manager import SessionManager, UserInfo, UserPreferences
from edagent_streamlit.core.api_client import EnhancedEdAgentAPI, AuthResult
from edagent_streamlit.core.error_handler import ErrorHandler, ErrorCategory
from edagent_streamlit.core.logger import setup_logging
from edagent_streamlit.components.auth import AuthenticationComponents
from edagent_streamlit.utils.validators import FormValidator, validate_registration_form


class TestRefactoredArchitecture:
    """Test suite for the refactored architecture"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return StreamlitConfig(Environment.TESTING)
    
    @pytest.fixture
    def session_manager(self):
        """Create test session manager"""
        return SessionManager()
    
    @pytest.fixture
    def api_client(self, session_manager):
        """Create test API client"""
        return EnhancedEdAgentAPI(session_manager)
    
    @pytest.fixture
    def error_handler(self):
        """Create test error handler"""
        return ErrorHandler()
    
    @pytest.fixture
    def auth_components(self, api_client, session_manager):
        """Create test authentication components"""
        return AuthenticationComponents(api_client, session_manager)
    
    def test_configuration_management(self, config):
        """Test configuration management system"""
        # Test environment-specific configuration
        assert config.environment == Environment.TESTING
        assert config.features.mock_data == True
        assert config.api.timeout == 5  # Testing override
        
        # Test feature flags
        assert config.is_feature_enabled("websocket_chat") == True
        assert config.is_feature_enabled("voice_chat") == False
        
        # Test API headers
        headers = config.get_api_headers("test_token")
        assert "Authorization" in headers
        assert headers["User-Agent"].startswith("EdAgent-Streamlit")
    
    def test_session_manager_lifecycle(self, session_manager):
        """Test complete session manager lifecycle"""
        # Test initial state
        assert not session_manager.is_authenticated()
        assert session_manager.get_current_user() is None
        
        # Test authentication
        user_info = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        session_manager.set_auth_data(
            user_info=user_info,
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Test authenticated state
        assert session_manager.is_authenticated()
        assert session_manager.get_current_user().user_id == "test_user_123"
        assert session_manager.get_auth_token() is not None
        
        # Test preferences
        preferences = UserPreferences(
            career_goals=["Software Engineer", "Tech Lead"],
            learning_style="hands-on"
        )
        session_manager.update_user_preferences(preferences)
        
        retrieved_prefs = session_manager.get_user_preferences()
        assert retrieved_prefs.career_goals == ["Software Engineer", "Tech Lead"]
        
        # Test session cleanup
        session_manager.clear_session()
        assert not session_manager.is_authenticated()
    
    @pytest.mark.asyncio
    async def test_api_client_integration(self, api_client, session_manager):
        """Test API client with comprehensive error handling"""
        # Mock HTTP responses
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful registration
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new_access_token",
                "user_id": "new_user_123",
                "email": "newuser@example.com",
                "name": "New User",
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            }
            mock_response.headers = {}
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            # Test registration
            result = await api_client.register_user(
                email="newuser@example.com",
                password="SecurePass123!",
                name="New User"
            )
            
            assert result.success == True
            assert result.user_id == "new_user_123"
            assert result.email == "newuser@example.com"
    
    @pytest.mark.asyncio
    async def test_error_handling_system(self, error_handler):
        """Test comprehensive error handling"""
        from edagent_streamlit.core.error_handler import ErrorContext, UserFriendlyError
        
        # Test error categorization
        test_error = Exception("Connection timeout")
        category = error_handler.categorize_error(test_error)
        assert category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT, ErrorCategory.UNKNOWN]
        
        # Test user-friendly error creation
        context = ErrorContext(
            operation="test_operation",
            user_id="test_user",
            additional_data={"test": "data"}
        )
        
        user_error = error_handler.create_user_friendly_error(test_error, context)
        assert isinstance(user_error, UserFriendlyError)
        assert user_error.message is not None
        assert user_error.category is not None
    
    def test_form_validation_system(self):
        """Test comprehensive form validation"""
        validator = FormValidator()
        
        # Test registration form validation
        valid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        
        errors = validate_registration_form(valid_data)
        assert len(errors) == 0
        
        # Test invalid data
        invalid_data = {
            "name": "",
            "email": "invalid-email",
            "password": "weak",
            "confirm_password": "different"
        }
        
        errors = validate_registration_form(invalid_data)
        assert len(errors) > 0
        assert "name" in errors
        assert "email" in errors
        assert "password" in errors
        assert "confirm_password" in errors
    
    def test_component_error_boundaries(self, auth_components):
        """Test component error boundaries"""
        # Test that components handle errors gracefully
        with patch.object(auth_components.api_client, 'register_user') as mock_register:
            mock_register.side_effect = Exception("API Error")
            
            # This should not raise an exception due to error boundaries
            try:
                result = asyncio.run(auth_components.api_client.register_user(
                    "test@example.com", "password", "Test User"
                ))
                # Should return error result, not raise exception
                assert result.success == False
            except Exception:
                pytest.fail("Component should handle errors gracefully")
    
    def test_logging_system(self):
        """Test logging system functionality"""
        logger = setup_logging("test_logger")
        
        # Test basic logging
        logger.info("Test info message", test_data="test_value")
        logger.error("Test error message", error_code="TEST_001")
        
        # Test performance logging
        logger.log_performance_metric("test_operation", 150.5, "ms")
        
        # Test user session logging
        logger.log_user_session("test_user", "login", ip_address="127.0.0.1")
    
    def test_caching_system(self, api_client):
        """Test API response caching"""
        # Test cache key generation
        cache_key = api_client._create_cache_key("GET", "/users/123", {"param": "value"})
        assert cache_key is not None
        assert "GET" in cache_key
        
        # Test cacheable endpoint detection
        assert api_client._is_cacheable("GET", "/users/123") == True
        assert api_client._is_cacheable("POST", "/users/") == False
        
        # Test cache operations
        api_client.cache.set("test_key", {"data": "test"}, ttl=60)
        cached_data = api_client.cache.get("test_key")
        assert cached_data == {"data": "test"}
        
        # Test cache cleanup
        api_client.cache.clear()
        assert api_client.cache.get("test_key") is None
    
    def test_security_features(self, session_manager):
        """Test security features"""
        # Test session fingerprinting
        session_manager._generate_session_fingerprint()
        security_state = session_manager.get_ui_state("security_state", {})
        assert "session_fingerprint" in security_state
        
        # Test failed login attempt tracking
        session_manager.record_failed_login_attempt()
        session_manager.record_failed_login_attempt()
        
        security_state = session_manager.get_ui_state("security_state", {})
        assert security_state.get("login_attempts", 0) == 2
        
        # Test account lockout
        for _ in range(5):  # Exceed max attempts
            session_manager.record_failed_login_attempt()
        
        assert session_manager._is_account_locked() == True
        
        remaining_time = session_manager.get_remaining_lockout_time()
        assert remaining_time is not None
        assert remaining_time.total_seconds() > 0
    
    def test_navigation_state_management(self, session_manager):
        """Test navigation state management"""
        # Test tab navigation
        session_manager.set_current_tab("chat")
        assert session_manager.get_current_tab() == "chat"
        
        session_manager.set_current_tab("assessments")
        assert session_manager.get_current_tab() == "assessments"
        
        # Test breadcrumb tracking
        breadcrumb = session_manager.get_navigation_breadcrumb()
        assert "chat" in breadcrumb
        assert "assessments" in breadcrumb
    
    def test_ui_state_management(self, session_manager):
        """Test UI state management"""
        # Test loading states
        session_manager.set_loading_state("api_call", True)
        assert session_manager.get_loading_state("api_call") == True
        
        session_manager.set_loading_state("api_call", False)
        assert session_manager.get_loading_state("api_call") == False
        
        # Test notifications
        session_manager.add_notification("Test message", "success", 5)
        notifications = session_manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0]["message"] == "Test message"
        
        session_manager.clear_notifications()
        assert len(session_manager.get_notifications()) == 0
    
    def test_data_caching_with_ttl(self, session_manager):
        """Test data caching with TTL"""
        # Test cache set and get
        session_manager.set_cached_data("test_key", {"data": "value"}, ttl_hours=1)
        cached_data = session_manager.get_cached_data("test_key")
        assert cached_data == {"data": "value"}
        
        # Test cache expiry (simulate by setting past timestamp)
        import json
        cached_data_dict = session_manager.get_ui_state("cached_data", {})
        if "test_key" in cached_data_dict:
            cached_data_dict["test_key"]["timestamp"] = "2020-01-01T00:00:00"
            session_manager.set_ui_state("cached_data", cached_data_dict)
        
        # Should return None for expired cache
        expired_data = session_manager.get_cached_data("test_key")
        assert expired_data is None
    
    def test_session_persistence(self, session_manager):
        """Test session persistence and recovery"""
        # Test session info generation
        session_info = session_manager.get_session_info()
        assert "is_authenticated" in session_info
        assert "session_state" in session_info
        assert "cached_data_keys" in session_info
        
        # Test session validation
        assert session_manager._validate_session_integrity() == True
        
        # Test session cleanup
        session_manager.cleanup_expired_data()
        # Should not raise any exceptions
    
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, auth_components, session_manager):
        """Test complete user workflow from registration to authenticated usage"""
        # Mock API responses for complete workflow
        with patch.object(auth_components.api_client, 'register_user') as mock_register, \
             patch.object(auth_components.api_client, 'login_user') as mock_login:
            
            # Mock successful registration
            mock_register.return_value = AuthResult(
                success=True,
                access_token="test_token",
                user_id="workflow_user",
                email="workflow@example.com",
                name="Workflow User",
                expires_at=datetime.now() + timedelta(hours=1)
            )
            
            # Mock successful login
            mock_login.return_value = AuthResult(
                success=True,
                access_token="login_token",
                user_id="workflow_user",
                email="workflow@example.com",
                name="Workflow User",
                expires_at=datetime.now() + timedelta(hours=1)
            )
            
            # Test registration workflow
            registration_result = await auth_components.api_client.register_user(
                "workflow@example.com",
                "SecurePass123!",
                "Workflow User"
            )
            
            assert registration_result.success == True
            
            # Test login workflow
            login_result = await auth_components.api_client.login_user(
                "workflow@example.com",
                "SecurePass123!"
            )
            
            assert login_result.success == True
            
            # Test session establishment
            user_info = UserInfo(
                user_id=login_result.user_id,
                email=login_result.email,
                name=login_result.name
            )
            
            session_manager.set_auth_data(
                user_info=user_info,
                access_token=login_result.access_token,
                expires_at=login_result.expires_at
            )
            
            # Verify authenticated state
            assert session_manager.is_authenticated() == True
            assert session_manager.get_current_user().user_id == "workflow_user"


class TestPerformanceAndScalability:
    """Test performance and scalability aspects"""
    
    def test_memory_usage(self, session_manager):
        """Test memory usage with large datasets"""
        # Test with large cached data
        large_data = {"data": ["item"] * 1000}
        session_manager.set_cached_data("large_dataset", large_data)
        
        retrieved_data = session_manager.get_cached_data("large_dataset")
        assert len(retrieved_data["data"]) == 1000
        
        # Test cleanup
        session_manager.clear_cached_data("large_dataset")
        assert session_manager.get_cached_data("large_dataset") is None
    
    def test_concurrent_operations(self, api_client):
        """Test concurrent API operations"""
        import threading
        import time
        
        results = []
        
        def make_request():
            # Simulate concurrent cache operations
            api_client.cache.set(f"concurrent_{threading.current_thread().ident}", {"data": "test"})
            time.sleep(0.1)
            result = api_client.cache.get(f"concurrent_{threading.current_thread().ident}")
            results.append(result is not None)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])