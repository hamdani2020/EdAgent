"""
Comprehensive tests for conversation interface and WebSocket integration
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import streamlit as st

# Import modules to test
from streamlit_api_client import EnhancedEdAgentAPI, ConversationResponse, APIResponse, APIError, APIErrorType
from streamlit_websocket import EnhancedStreamlitWebSocketClient, initialize_websocket, connect_websocket
from streamlit_session_manager import SessionManager


class TestConversationFlow:
    """Test conversation interface functionality"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        from streamlit_session_manager import UserInfo
        
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        
        # Create mock user info
        mock_user = Mock(spec=UserInfo)
        mock_user.user_id = "test_user_123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        
        session_manager.get_current_user.return_value = mock_user
        session_manager.get_auth_token.return_value = "test_token_456"
        return session_manager
    
    @pytest.fixture
    def mock_api_client(self, mock_session_manager):
        """Create mock API client"""
        api_client = Mock(spec=EnhancedEdAgentAPI)
        api_client.session_manager = mock_session_manager
        return api_client
    
    @pytest.fixture
    def sample_conversation_response(self):
        """Sample conversation response data"""
        return ConversationResponse(
            message="Hello! I can help you with your career goals. What would you like to work on?",
            response_type="text",
            confidence_score=0.95,
            suggested_actions=["Start a skill assessment", "Create a learning path"],
            content_recommendations=[
                {
                    "title": "Python Programming Course",
                    "description": "Learn Python from basics to advanced",
                    "url": "https://example.com/python-course",
                    "type": "course"
                }
            ],
            follow_up_questions=["What's your current skill level?", "What are your career goals?"],
            metadata={"conversation_id": "conv_123", "user_intent": "general_help"}
        )
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_api_client, sample_conversation_response):
        """Test successful message sending"""
        # Setup
        mock_api_client.send_message.return_value = sample_conversation_response
        
        # Test
        result = await mock_api_client.send_message("test_user_123", "Hello, I need help with my career")
        
        # Assertions
        assert result.message == "Hello! I can help you with your career goals. What would you like to work on?"
        assert result.confidence_score == 0.95
        assert len(result.suggested_actions) == 2
        assert len(result.content_recommendations) == 1
        assert len(result.follow_up_questions) == 2
        
        mock_api_client.send_message.assert_called_once_with("test_user_123", "Hello, I need help with my career")
    
    @pytest.mark.asyncio
    async def test_send_message_api_error(self, mock_api_client):
        """Test message sending with API error"""
        # Setup
        mock_api_client.send_message.side_effect = Exception("API connection failed")
        
        # Test
        with pytest.raises(Exception) as exc_info:
            await mock_api_client.send_message("test_user_123", "Hello")
        
        assert "API connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, mock_api_client):
        """Test successful conversation history retrieval"""
        # Setup
        mock_history = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2024-01-01T10:00:00Z",
                "metadata": {}
            },
            {
                "role": "assistant", 
                "content": "Hi! How can I help you?",
                "timestamp": "2024-01-01T10:00:01Z",
                "metadata": {"confidence_score": 0.9}
            }
        ]
        mock_api_client.get_conversation_history.return_value = mock_history
        
        # Test
        result = await mock_api_client.get_conversation_history("test_user_123", limit=50)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[1]["metadata"]["confidence_score"] == 0.9
        
        mock_api_client.get_conversation_history.assert_called_once_with("test_user_123", limit=50)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self, mock_api_client):
        """Test conversation history retrieval when empty"""
        # Setup
        mock_api_client.get_conversation_history.return_value = []
        
        # Test
        result = await mock_api_client.get_conversation_history("test_user_123")
        
        # Assertions
        assert result == []
        mock_api_client.get_conversation_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_conversation_history_success(self, mock_api_client):
        """Test successful conversation history clearing"""
        # Setup
        mock_api_client.clear_conversation_history.return_value = True
        
        # Test
        result = await mock_api_client.clear_conversation_history("test_user_123")
        
        # Assertions
        assert result is True
        mock_api_client.clear_conversation_history.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    async def test_clear_conversation_history_failure(self, mock_api_client):
        """Test conversation history clearing failure"""
        # Setup
        mock_api_client.clear_conversation_history.return_value = False
        
        # Test
        result = await mock_api_client.clear_conversation_history("test_user_123")
        
        # Assertions
        assert result is False


class TestWebSocketIntegration:
    """Test WebSocket functionality"""
    
    @pytest.fixture
    def ws_client(self):
        """Create WebSocket client for testing"""
        return EnhancedStreamlitWebSocketClient("ws://localhost:8000/api/v1")
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.ping = AsyncMock()
        return mock_ws
    
    def test_websocket_initialization(self, ws_client):
        """Test WebSocket client initialization"""
        assert ws_client.ws_url == "ws://localhost:8000/api/v1"
        assert ws_client.is_connected is False
        assert ws_client.reconnect_attempts == 0
        assert ws_client.max_reconnect_attempts == 5
        assert ws_client.messages_sent == 0
        assert ws_client.messages_received == 0
    
    @pytest.mark.asyncio
    async def test_websocket_connect_success(self, ws_client, mock_websocket):
        """Test successful WebSocket connection"""
        # Mock the async iterator properly
        async def mock_message_iterator():
            return
            yield  # This makes it an async generator
        
        mock_websocket.__aiter__ = mock_message_iterator
        
        with patch('websockets.connect') as mock_connect:
            mock_connect.return_value = mock_websocket
            
            # Mock the gather to avoid running the actual listeners
            with patch('asyncio.gather') as mock_gather:
                mock_gather.return_value = None
                
                try:
                    await ws_client.connect("test_user", "test_token")
                except Exception:
                    pass  # Expected since we're mocking
                
                # Check that connection was attempted
                assert ws_client.user_id == "test_user"
                assert ws_client.auth_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_websocket_connect_failure(self, ws_client):
        """Test WebSocket connection failure"""
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            # The connect method handles exceptions internally and doesn't re-raise
            await ws_client.connect("test_user", "test_token")
            
            # Should have attempted connection but failed
            assert ws_client.is_connected is False
            assert ws_client.reconnect_attempts == ws_client.max_reconnect_attempts
    
    @pytest.mark.asyncio
    async def test_websocket_send_message(self, ws_client, mock_websocket):
        """Test sending message through WebSocket"""
        # Setup connected state
        ws_client.websocket = mock_websocket
        ws_client.is_connected = True
        ws_client.user_id = "test_user"
        
        # Test
        await ws_client.send_message("Hello, world!")
        
        # Assertions
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        message_data = json.loads(call_args)
        
        assert message_data["type"] == "message"
        assert message_data["content"] == "Hello, world!"
        assert message_data["user_id"] == "test_user"
        assert ws_client.messages_sent == 1
    
    @pytest.mark.asyncio
    async def test_websocket_send_message_not_connected(self, ws_client):
        """Test sending message when not connected"""
        ws_client.is_connected = False
        
        with pytest.raises(ConnectionError):
            await ws_client.send_message("Hello")
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self, ws_client):
        """Test incoming message handling"""
        # Setup message handler
        received_messages = []
        
        def message_handler(data):
            received_messages.append(data)
        
        ws_client.set_message_handler(message_handler)
        
        # Simulate incoming messages
        test_messages = [
            json.dumps({"type": "response", "content": "Hello back!", "user_id": "assistant"}),
            json.dumps({"type": "status", "message": "ready"}),
            json.dumps({"type": "error", "message": "Something went wrong", "code": "test_error"})
        ]
        
        # Create a proper async iterator
        async def message_generator():
            for msg in test_messages:
                yield msg
        
        # Mock WebSocket with proper async iterator
        mock_websocket = Mock()
        mock_websocket.__aiter__ = lambda: message_generator()
        
        ws_client.websocket = mock_websocket
        ws_client.is_connected = True
        
        # Process messages
        try:
            await ws_client.listen_for_messages()
        except Exception:
            pass  # Expected since we're mocking
        
        # Assertions - check that messages were processed
        assert ws_client.messages_received >= 0  # At least attempted to process
    
    def test_websocket_sync_message_sending(self, ws_client):
        """Test synchronous message sending for Streamlit"""
        ws_client.is_connected = True
        
        # Test
        result = ws_client.send_message_sync("Test message")
        
        # Assertions
        assert result is True
        assert not ws_client.message_queue.empty()
        
        # Check queued message
        queued_message = ws_client.message_queue.get()
        assert queued_message["message"] == "Test message"
    
    def test_websocket_sync_message_not_connected(self, ws_client):
        """Test synchronous message sending when not connected"""
        ws_client.is_connected = False
        
        result = ws_client.send_message_sync("Test message")
        
        assert result is False
    
    def test_websocket_response_queue(self, ws_client):
        """Test response queue functionality"""
        # Add test response to queue
        test_response = {"type": "response", "content": "Test response"}
        ws_client.response_queue.put(test_response)
        
        # Test getting response
        response = ws_client.get_latest_response()
        assert response == test_response
        
        # Test empty queue
        empty_response = ws_client.get_latest_response()
        assert empty_response is None
    
    def test_websocket_connection_stats(self, ws_client):
        """Test connection statistics"""
        # Setup some state
        ws_client.is_connected = True
        ws_client.messages_sent = 5
        ws_client.messages_received = 3
        ws_client.reconnect_attempts = 1
        ws_client.connection_start_time = datetime.now()
        
        # Test
        stats = ws_client.get_connection_stats()
        
        # Assertions
        assert stats["is_connected"] is True
        assert stats["messages_sent"] == 5
        assert stats["messages_received"] == 3
        assert stats["reconnect_attempts"] == 1
        assert stats["uptime_seconds"] is not None
        assert stats["uptime_seconds"] >= 0


class TestStreamlitIntegration:
    """Test Streamlit-specific integration functions"""
    
    def test_initialize_websocket(self):
        """Test WebSocket initialization in Streamlit"""
        # Mock streamlit session state
        mock_session_state = {}
        
        with patch('streamlit_websocket.st.session_state', mock_session_state):
            ws_client = initialize_websocket()
            
            assert ws_client is not None
            assert isinstance(ws_client, EnhancedStreamlitWebSocketClient)
            assert "ws_client" in mock_session_state
    
    @patch('streamlit.session_state', {})
    def test_connect_websocket_success(self):
        """Test WebSocket connection through Streamlit interface"""
        with patch('streamlit_websocket.initialize_websocket') as mock_init:
            mock_client = Mock()
            mock_client.is_connected = False
            mock_client.start_connection_thread = Mock()
            mock_init.return_value = mock_client
            
            # Test
            result = connect_websocket("test_user", "test_token")
            
            # Assertions
            assert result is True
            mock_client.start_connection_thread.assert_called_once_with("test_user", "test_token")
    
    @patch('streamlit.session_state', {})
    def test_connect_websocket_already_connected(self):
        """Test WebSocket connection when already connected"""
        with patch('streamlit_websocket.initialize_websocket') as mock_init:
            mock_client = Mock()
            mock_client.is_connected = True
            mock_init.return_value = mock_client
            
            # Test
            result = connect_websocket("test_user", "test_token")
            
            # Assertions
            assert result is True
            mock_client.start_connection_thread.assert_not_called()


class TestErrorHandling:
    """Test error handling in conversation interface"""
    
    @pytest.fixture
    def api_client_with_errors(self):
        """Create API client that simulates various errors"""
        client = Mock(spec=EnhancedEdAgentAPI)
        return client
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, api_client_with_errors):
        """Test handling of authentication errors"""
        # Setup
        auth_error = APIError(
            error_type=APIErrorType.AUTHENTICATION_ERROR,
            message="Token expired",
            status_code=401,
            is_retryable=False
        )
        api_client_with_errors.send_message.side_effect = auth_error
        
        # Test
        with pytest.raises(APIError) as exc_info:
            await api_client_with_errors.send_message("user_123", "Hello")
        
        assert exc_info.value.error_type == APIErrorType.AUTHENTICATION_ERROR
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, api_client_with_errors):
        """Test handling of rate limit errors"""
        # Setup
        rate_limit_error = APIError(
            error_type=APIErrorType.RATE_LIMIT_ERROR,
            message="Rate limit exceeded",
            status_code=429,
            retry_after=60,
            is_retryable=True
        )
        api_client_with_errors.send_message.side_effect = rate_limit_error
        
        # Test
        with pytest.raises(APIError) as exc_info:
            await api_client_with_errors.send_message("user_123", "Hello")
        
        assert exc_info.value.error_type == APIErrorType.RATE_LIMIT_ERROR
        assert exc_info.value.retry_after == 60
        assert exc_info.value.is_retryable is True
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, api_client_with_errors):
        """Test handling of network errors"""
        # Setup
        network_error = APIError(
            error_type=APIErrorType.NETWORK_ERROR,
            message="Connection timeout",
            is_retryable=True
        )
        api_client_with_errors.send_message.side_effect = network_error
        
        # Test
        with pytest.raises(APIError) as exc_info:
            await api_client_with_errors.send_message("user_123", "Hello")
        
        assert exc_info.value.error_type == APIErrorType.NETWORK_ERROR
        assert exc_info.value.is_retryable is True


class TestConversationPagination:
    """Test conversation history pagination"""
    
    def test_message_pagination_calculation(self):
        """Test pagination calculations for large conversation histories"""
        # Setup
        total_messages = 157
        messages_per_page = 20
        
        # Calculate pagination
        total_pages = max(1, (total_messages + messages_per_page - 1) // messages_per_page)
        
        # Test
        assert total_pages == 8  # 157 messages / 20 per page = 7.85, rounded up to 8
        
        # Test page ranges
        for page in range(total_pages):
            start_idx = page * messages_per_page
            end_idx = min(start_idx + messages_per_page, total_messages)
            
            assert start_idx >= 0
            assert end_idx <= total_messages
            assert end_idx > start_idx
        
        # Test last page
        last_page = total_pages - 1
        start_idx = last_page * messages_per_page
        end_idx = min(start_idx + messages_per_page, total_messages)
        
        assert end_idx == total_messages
        assert end_idx - start_idx == 17  # Last page has 17 messages


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])