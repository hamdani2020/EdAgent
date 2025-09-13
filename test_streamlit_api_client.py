"""
Unit tests for Enhanced EdAgent API Client
Tests error handling, retry logic, and response processing
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import httpx

from streamlit_api_client import (
    EnhancedEdAgentAPI,
    SessionManager,
    APIError,
    APIErrorType,
    APIResponse,
    AuthResult,
    ConversationResponse,
    AssessmentSession,
    LearningPath,
    create_api_client,
    handle_async_api_call
)


class TestSessionManager:
    """Test SessionManager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.session_manager = SessionManager()
        # Mock streamlit session state
        self.mock_session_state = {}
        
    @patch('streamlit_api_client.st.session_state', new_callable=dict)
    def test_authentication_state(self, mock_session_state):
        """Test authentication state management"""
        # Initially not authenticated
        assert not self.session_manager.is_authenticated()
        
        # Set authentication data
        auth_result = AuthResult(
            success=True,
            access_token="test_token",
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        self.session_manager.set_auth_data(auth_result)
        
        # Should be authenticated now
        assert self.session_manager.is_authenticated()
        assert self.session_manager.get_current_user_id() == "test_user"
        assert self.session_manager.get_auth_token() == "test_token"
        assert self.session_manager.get_user_email() == "test@example.com"
    
    @patch('streamlit_api_client.st.session_state', new_callable=dict)
    def test_token_expiry(self, mock_session_state):
        """Test token expiry detection"""
        # Set expired token
        auth_result = AuthResult(
            success=True,
            access_token="expired_token",
            user_id="test_user",
            email="test@example.com",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        self.session_manager.set_auth_data(auth_result)
        
        # Should detect expired token
        assert self.session_manager.is_token_expired()
        assert not self.session_manager.is_authenticated()
    
    @patch('streamlit_api_client.st.session_state', new_callable=dict)
    def test_clear_session(self, mock_session_state):
        """Test session clearing"""
        # Set some session data
        auth_result = AuthResult(
            success=True,
            access_token="test_token",
            user_id="test_user",
            email="test@example.com"
        )
        
        self.session_manager.set_auth_data(auth_result)
        assert self.session_manager.get_current_user_id() == "test_user"
        
        # Clear session
        self.session_manager.clear_session()
        assert not self.session_manager.is_authenticated()
        assert self.session_manager.get_current_user_id() is None


class TestEnhancedEdAgentAPI:
    """Test EnhancedEdAgentAPI functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.session_manager = Mock(spec=SessionManager)
        self.api = EnhancedEdAgentAPI("http://test-api", self.session_manager)
    
    def test_initialization(self):
        """Test API client initialization"""
        assert self.api.base_url == "http://test-api"
        assert self.api.session_manager == self.session_manager
        assert self.api.failure_count == 0
        assert self.api.circuit_breaker_threshold == 5
    
    def test_get_headers_unauthenticated(self):
        """Test header generation without authentication"""
        self.session_manager.is_authenticated.return_value = False
        
        headers = self.api._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "EdAgent-Streamlit/1.0"
        assert "Authorization" not in headers
    
    def test_get_headers_authenticated(self):
        """Test header generation with authentication"""
        self.session_manager.is_authenticated.return_value = True
        self.session_manager.get_auth_token.return_value = "test_token"
        
        headers = self.api._get_headers()
        
        assert headers["Authorization"] == "Bearer test_token"
    
    def test_categorize_error_timeout(self):
        """Test error categorization for timeout"""
        exception = httpx.TimeoutException("Request timeout")
        error_type = self.api._categorize_error(None, exception)
        assert error_type == APIErrorType.TIMEOUT_ERROR
    
    def test_categorize_error_network(self):
        """Test error categorization for network error"""
        exception = httpx.NetworkError("Network error")
        error_type = self.api._categorize_error(None, exception)
        assert error_type == APIErrorType.NETWORK_ERROR
    
    def test_categorize_error_http_status(self):
        """Test error categorization for HTTP status codes"""
        # Mock response objects
        responses = [
            (401, APIErrorType.AUTHENTICATION_ERROR),
            (403, APIErrorType.AUTHORIZATION_ERROR),
            (422, APIErrorType.VALIDATION_ERROR),
            (429, APIErrorType.RATE_LIMIT_ERROR),
            (500, APIErrorType.SERVER_ERROR),
            (404, APIErrorType.UNKNOWN_ERROR)
        ]
        
        for status_code, expected_type in responses:
            mock_response = Mock()
            mock_response.status_code = status_code
            error_type = self.api._categorize_error(mock_response)
            assert error_type == expected_type
    
    def test_create_api_error_from_exception(self):
        """Test API error creation from exception"""
        exception = httpx.TimeoutException("Request timeout")
        api_error = self.api._create_api_error(exception=exception)
        
        assert api_error.error_type == APIErrorType.TIMEOUT_ERROR
        assert api_error.message == "Request timeout"
        assert api_error.is_retryable is True
    
    def test_create_api_error_from_response(self):
        """Test API error creation from HTTP response"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60"}
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit exceeded",
                "details": {"limit": 100}
            }
        }
        mock_response.text = "Rate limit exceeded"
        
        api_error = self.api._create_api_error(response=mock_response)
        
        assert api_error.error_type == APIErrorType.RATE_LIMIT_ERROR
        assert api_error.message == "Rate limit exceeded"
        assert api_error.status_code == 429
        assert api_error.retry_after == 60
        assert api_error.is_retryable is True
    
    def test_should_retry_logic(self):
        """Test retry logic"""
        # Retryable error with low failure count
        retryable_error = APIError(
            error_type=APIErrorType.NETWORK_ERROR,
            message="Network error",
            is_retryable=True
        )
        assert self.api._should_retry(retryable_error) is True
        
        # Non-retryable error
        non_retryable_error = APIError(
            error_type=APIErrorType.AUTHENTICATION_ERROR,
            message="Auth error",
            is_retryable=False
        )
        assert self.api._should_retry(non_retryable_error) is False
        
        # Retryable error with high failure count
        self.api.failure_count = 10
        assert self.api._should_retry(retryable_error) is False
    
    def test_circuit_breaker_open(self):
        """Test circuit breaker functionality"""
        self.api.failure_count = 5
        self.api.circuit_breaker_last_failure = time.time()
        
        with pytest.raises(APIError) as exc_info:
            self.api._handle_circuit_breaker()
        
        assert exc_info.value.error_type == APIErrorType.SERVER_ERROR
        assert "Circuit breaker open" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"message": "success"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            result = await self.api._make_request("GET", "/test")
            
            assert result.success is True
            assert result.data == {"message": "success"}
            assert result.status_code == 200
            assert self.api.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self):
        """Test API request with HTTP error"""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "error": {"message": "Bad request"}
        }
        mock_response.text = "Bad request"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            result = await self.api._make_request("GET", "/test")
            
            assert result.success is False
            assert result.error is not None
            assert result.status_code == 400
            assert self.api.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_make_request_network_exception(self):
        """Test API request with network exception"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.NetworkError("Network error")
            )
            
            result = await self.api._make_request("GET", "/test")
            
            assert result.success is False
            assert result.error.error_type == APIErrorType.NETWORK_ERROR
            assert self.api.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration"""
        mock_response_data = {
            "access_token": "test_token",
            "user_id": "test_user",
            "email": "test@example.com",
            "name": "Test User",
            "expires_at": "2024-12-31T23:59:59"
        }
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await self.api.register_user("test@example.com", "password", "Test User")
            
            assert result.success is True
            assert result.access_token == "test_token"
            assert result.user_id == "test_user"
            assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_register_user_failure(self):
        """Test failed user registration"""
        api_error = APIError(
            error_type=APIErrorType.VALIDATION_ERROR,
            message="Invalid email"
        )
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=False,
                data=None,
                error=api_error
            )
            
            with patch.object(self.api, '_handle_api_error') as mock_handle_error:
                result = await self.api.register_user("invalid-email", "password", "Test User")
                
                assert result.success is False
                assert result.error == "Invalid email"
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_user_success(self):
        """Test successful user login"""
        mock_response_data = {
            "access_token": "login_token",
            "user_id": "login_user",
            "email": "login@example.com",
            "name": "Login User",
            "expires_at": "2024-12-31T23:59:59"
        }
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await self.api.login_user("login@example.com", "password")
            
            assert result.success is True
            assert result.access_token == "login_token"
            assert result.user_id == "login_user"
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending"""
        mock_response_data = {
            "message": "AI response",
            "response_type": "text",
            "confidence_score": 0.95,
            "suggested_actions": ["action1", "action2"],
            "content_recommendations": [{"title": "Resource 1"}],
            "follow_up_questions": ["Question 1?"],
            "metadata": {"key": "value"}
        }
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await self.api.send_message("user123", "Hello")
            
            assert result.message == "AI response"
            assert result.response_type == "text"
            assert result.confidence_score == 0.95
            assert len(result.suggested_actions) == 2
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Test failed message sending"""
        api_error = APIError(
            error_type=APIErrorType.SERVER_ERROR,
            message="Server error"
        )
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=False,
                data=None,
                error=api_error
            )
            
            with patch.object(self.api, '_handle_api_error') as mock_handle_error:
                result = await self.api.send_message("user123", "Hello")
                
                assert "trouble connecting" in result.message
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_assessment_success(self):
        """Test successful assessment start"""
        mock_response_data = {
            "id": "assessment123",
            "user_id": "user123",
            "skill_area": "python",
            "questions": [{"question": "What is Python?"}],
            "current_question_index": 0,
            "status": "active",
            "started_at": "2024-01-01T00:00:00",
            "progress": 0.0
        }
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await self.api.start_assessment("user123", "python")
            
            assert result is not None
            assert result.id == "assessment123"
            assert result.skill_area == "python"
            assert result.status == "active"
    
    @pytest.mark.asyncio
    async def test_create_learning_path_success(self):
        """Test successful learning path creation"""
        mock_response_data = {
            "id": "path123",
            "title": "Python Learning Path",
            "description": "Learn Python programming",
            "goal": "Become a Python developer",
            "milestones": [{"title": "Basics"}],
            "estimated_duration": 3600,
            "difficulty_level": "intermediate",
            "prerequisites": ["basic programming"],
            "target_skills": ["python", "programming"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "progress": 0.0
        }
        
        with patch.object(self.api, '_make_request') as mock_request:
            mock_request.return_value = APIResponse(
                success=True,
                data=mock_response_data
            )
            
            result = await self.api.create_learning_path("user123", "Become a Python developer")
            
            assert result is not None
            assert result.id == "path123"
            assert result.title == "Python Learning Path"
            assert result.goal == "Become a Python developer"
    
    def test_get_connection_status(self):
        """Test connection status reporting"""
        self.session_manager.is_authenticated.return_value = True
        self.session_manager.get_current_user_id.return_value = "user123"
        self.session_manager.get_token_expiry_time.return_value = datetime.now() + timedelta(hours=1)
        
        status = self.api.get_connection_status()
        
        assert status["base_url"] == "http://test-api"
        assert status["authenticated"] is True
        assert status["user_id"] == "user123"
        assert status["failure_count"] == 0
        assert status["circuit_breaker_open"] is False
    
    def test_reset_circuit_breaker(self):
        """Test circuit breaker reset"""
        self.api.failure_count = 5
        self.api.circuit_breaker_last_failure = time.time()
        
        self.api.reset_circuit_breaker()
        
        assert self.api.failure_count == 0
        assert self.api.circuit_breaker_last_failure == 0


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_api_client_default(self):
        """Test API client creation with default URL"""
        with patch.dict('os.environ', {}, clear=True):
            client = create_api_client()
            assert client.base_url == "http://localhost:8000/api/v1"
    
    def test_create_api_client_custom_url(self):
        """Test API client creation with custom URL"""
        client = create_api_client("http://custom-api:8080/api/v1")
        assert client.base_url == "http://custom-api:8080/api/v1"
    
    def test_create_api_client_env_var(self):
        """Test API client creation with environment variable"""
        with patch.dict('os.environ', {'EDAGENT_API_URL': 'http://env-api:9000/api/v1'}):
            client = create_api_client()
            assert client.base_url == "http://env-api:9000/api/v1"
    
    @pytest.mark.asyncio
    async def test_handle_async_api_call(self):
        """Test async API call handling"""
        async def test_coro():
            return "test_result"
        
        result = handle_async_api_call(test_coro())
        assert result == "test_result"


class TestErrorHandling:
    """Test comprehensive error handling scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.session_manager = Mock(spec=SessionManager)
        self.api = EnhancedEdAgentAPI("http://test-api", self.session_manager)
    
    @patch('streamlit_api_client.st.error')
    @patch('streamlit_api_client.st.rerun')
    def test_handle_authentication_error(self, mock_rerun, mock_error):
        """Test authentication error handling"""
        api_error = APIError(
            error_type=APIErrorType.AUTHENTICATION_ERROR,
            message="Token expired"
        )
        
        self.api._handle_api_error(api_error, "test context")
        
        mock_error.assert_called_once()
        self.session_manager.clear_session.assert_called_once()
        mock_rerun.assert_called_once()
    
    @patch('streamlit_api_client.st.error')
    def test_handle_rate_limit_error(self, mock_error):
        """Test rate limit error handling"""
        api_error = APIError(
            error_type=APIErrorType.RATE_LIMIT_ERROR,
            message="Rate limit exceeded",
            retry_after=120
        )
        
        self.api._handle_api_error(api_error, "test context")
        
        mock_error.assert_called_once()
        error_call_args = mock_error.call_args[0][0]
        assert "120 seconds" in error_call_args
    
    @patch('streamlit_api_client.st.error')
    def test_handle_network_error(self, mock_error):
        """Test network error handling"""
        api_error = APIError(
            error_type=APIErrorType.NETWORK_ERROR,
            message="Connection failed"
        )
        
        self.api._handle_api_error(api_error, "test context")
        
        mock_error.assert_called_once()
        error_call_args = mock_error.call_args[0][0]
        assert "internet connection" in error_call_args.lower()


class TestRetryLogic:
    """Test retry logic and resilience"""
    
    def setup_method(self):
        """Setup test environment"""
        self.session_manager = Mock(spec=SessionManager)
        self.api = EnhancedEdAgentAPI("http://test-api", self.session_manager)
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry behavior on timeout"""
        call_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.json.return_value = {"success": True}
            return mock_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = mock_request
            
            result = await self.api._make_request("GET", "/test")
            
            assert result.success is True
            assert call_count == 3  # Should retry twice then succeed
    
    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """Test no retry on authentication error"""
        call_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            mock_response.is_success = False
            mock_response.status_code = 401
            mock_response.headers = {}
            mock_response.json.return_value = {"error": {"message": "Unauthorized"}}
            mock_response.text = "Unauthorized"
            return mock_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = mock_request
            
            result = await self.api._make_request("GET", "/test")
            
            assert result.success is False
            assert call_count == 1  # Should not retry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])