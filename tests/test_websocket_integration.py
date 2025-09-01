"""
Integration tests for WebSocket functionality
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from edagent.api.app import create_app
from edagent.api.websocket import ConnectionManager, connection_manager
from edagent.models.conversation import ConversationResponse
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.messages_sent: List[Dict[str, Any]] = []
        self.messages_received: List[Dict[str, Any]] = []
        self.is_closed = False
        self.close_code = None
        self.close_reason = None
    
    async def accept(self):
        """Mock accept method"""
        pass
    
    async def send_json(self, data: Dict[str, Any]):
        """Mock send_json method"""
        if self.is_closed:
            raise RuntimeError("WebSocket is closed")
        self.messages_sent.append(data)
    
    async def receive_json(self) -> Dict[str, Any]:
        """Mock receive_json method"""
        if self.is_closed:
            raise RuntimeError("WebSocket is closed")
        if self.messages_received:
            return self.messages_received.pop(0)
        # Simulate waiting for message
        await asyncio.sleep(0.1)
        return {"message": "test message"}
    
    async def close(self, code: int = 1000, reason: str = ""):
        """Mock close method"""
        self.is_closed = True
        self.close_code = code
        self.close_reason = reason
    
    def add_received_message(self, message: Dict[str, Any]):
        """Add a message to the received queue"""
        self.messages_received.append(message)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing"""
    return MockWebSocket()


@pytest.fixture
def clean_connection_manager():
    """Clean connection manager state before each test"""
    # Clear any existing connections
    connection_manager.active_connections.clear()
    connection_manager.connection_metadata.clear()
    yield connection_manager
    # Clean up after test
    connection_manager.active_connections.clear()
    connection_manager.connection_metadata.clear()


@pytest.fixture
def mock_conversation_manager():
    """Mock conversation manager for testing"""
    mock = AsyncMock()
    mock.handle_message.return_value = ConversationResponse(
        message="Test AI response",
        response_type="text",
        confidence_score=0.9
    )
    return mock


@pytest.fixture
def mock_user_context_manager():
    """Mock user context manager for testing"""
    mock = AsyncMock()
    mock.get_user_context.return_value = UserContext(
        user_id="test-user",
        current_skills={},
        career_goals=[],
        learning_preferences=UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week"
        ),
        conversation_history=[],
        assessment_results=None
    )
    mock.create_user_context.return_value = UserContext(
        user_id="test-user",
        current_skills={},
        career_goals=[],
        learning_preferences=UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week"
        ),
        conversation_history=[],
        assessment_results=None
    )
    return mock


class TestConnectionManager:
    """Test ConnectionManager functionality"""
    
    @pytest.mark.asyncio
    async def test_connect_user(self, mock_websocket, clean_connection_manager):
        """Test connecting a user via WebSocket"""
        user_id = "test-user-123"
        
        await clean_connection_manager.connect(mock_websocket, user_id)
        
        # Verify connection is established
        assert user_id in clean_connection_manager.active_connections
        assert clean_connection_manager.is_connected(user_id)
        
        # Verify welcome message was sent
        assert len(mock_websocket.messages_sent) == 1
        welcome_msg = mock_websocket.messages_sent[0]
        assert welcome_msg["type"] == "connection_established"
        assert "Connected to EdAgent" in welcome_msg["message"]
        
        # Verify metadata is tracked
        conn_info = clean_connection_manager.get_connection_info(user_id)
        assert conn_info is not None
        assert "connected_at" in conn_info
        assert conn_info["message_count"] == 1  # Welcome message counts
    
    @pytest.mark.asyncio
    async def test_disconnect_user(self, mock_websocket, clean_connection_manager):
        """Test disconnecting a user"""
        user_id = "test-user-123"
        
        # Connect first
        await clean_connection_manager.connect(mock_websocket, user_id)
        assert clean_connection_manager.is_connected(user_id)
        
        # Disconnect
        await clean_connection_manager.disconnect(user_id, "test_disconnect")
        
        # Verify disconnection
        assert not clean_connection_manager.is_connected(user_id)
        assert user_id not in clean_connection_manager.active_connections
        assert user_id not in clean_connection_manager.connection_metadata
        
        # Verify disconnect message was sent
        disconnect_messages = [msg for msg in mock_websocket.messages_sent if msg.get("type") == "disconnection"]
        assert len(disconnect_messages) == 1
        assert disconnect_messages[0]["reason"] == "test_disconnect"
    
    @pytest.mark.asyncio
    async def test_send_message(self, mock_websocket, clean_connection_manager):
        """Test sending messages to connected users"""
        user_id = "test-user-123"
        
        # Connect user
        await clean_connection_manager.connect(mock_websocket, user_id)
        initial_message_count = len(mock_websocket.messages_sent)
        
        # Send test message
        test_message = {"type": "test", "content": "Hello World"}
        success = await clean_connection_manager.send_message(user_id, test_message)
        
        # Verify message was sent
        assert success is True
        assert len(mock_websocket.messages_sent) == initial_message_count + 1
        assert mock_websocket.messages_sent[-1] == test_message
        
        # Verify metadata was updated
        conn_info = clean_connection_manager.get_connection_info(user_id)
        assert conn_info["message_count"] == 2  # Welcome message + test message
    
    @pytest.mark.asyncio
    async def test_send_message_to_disconnected_user(self, clean_connection_manager):
        """Test sending message to disconnected user returns False"""
        user_id = "disconnected-user"
        
        test_message = {"type": "test", "content": "Hello"}
        success = await clean_connection_manager.send_message(user_id, test_message)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_typing_indicator(self, mock_websocket, clean_connection_manager):
        """Test sending typing indicators"""
        user_id = "test-user-123"
        
        # Connect user
        await clean_connection_manager.connect(mock_websocket, user_id)
        initial_count = len(mock_websocket.messages_sent)
        
        # Send typing indicator
        success = await clean_connection_manager.send_typing_indicator(user_id, True)
        
        assert success is True
        assert len(mock_websocket.messages_sent) == initial_count + 1
        
        typing_msg = mock_websocket.messages_sent[-1]
        assert typing_msg["type"] == "typing_indicator"
        assert typing_msg["is_typing"] is True
    
    @pytest.mark.asyncio
    async def test_send_error(self, mock_websocket, clean_connection_manager):
        """Test sending error messages"""
        user_id = "test-user-123"
        
        # Connect user
        await clean_connection_manager.connect(mock_websocket, user_id)
        initial_count = len(mock_websocket.messages_sent)
        
        # Send error
        success = await clean_connection_manager.send_error(user_id, "Test error", "test_code")
        
        assert success is True
        assert len(mock_websocket.messages_sent) == initial_count + 1
        
        error_msg = mock_websocket.messages_sent[-1]
        assert error_msg["type"] == "error"
        assert error_msg["message"] == "Test error"
        assert error_msg["error_code"] == "test_code"
    
    @pytest.mark.asyncio
    async def test_reconnection_closes_existing(self, clean_connection_manager):
        """Test that reconnecting closes existing connection"""
        user_id = "test-user-123"
        
        # Connect first WebSocket
        first_ws = MockWebSocket()
        await clean_connection_manager.connect(first_ws, user_id)
        
        # Connect second WebSocket (should close first)
        second_ws = MockWebSocket()
        await clean_connection_manager.connect(second_ws, user_id)
        
        # Verify only second connection is active
        assert clean_connection_manager.is_connected(user_id)
        assert clean_connection_manager.active_connections[user_id] == second_ws
        
        # Verify first WebSocket was closed
        assert first_ws.is_closed
    
    def test_get_active_users(self, clean_connection_manager):
        """Test getting list of active users"""
        # Initially empty
        assert clean_connection_manager.get_active_users() == []
        
        # Add some mock connections
        clean_connection_manager.active_connections["user1"] = MockWebSocket()
        clean_connection_manager.active_connections["user2"] = MockWebSocket()
        
        active_users = clean_connection_manager.get_active_users()
        assert len(active_users) == 2
        assert "user1" in active_users
        assert "user2" in active_users


class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self, mock_conversation_manager, mock_user_context_manager):
        """Test complete WebSocket message handling flow"""
        from edagent.api.websocket import websocket_endpoint
        
        user_id = "test-user-123"
        mock_websocket = MockWebSocket()
        
        # Add a test message to be received
        mock_websocket.add_received_message({"message": "Hello EdAgent"})
        
        # Mock the conversation manager response
        mock_response = ConversationResponse(
            message="Hello! How can I help you today?",
            response_type="text",
            confidence_score=0.95,
            suggested_actions=["Ask about skills", "Create learning path"],
            follow_up_questions=["What are your career goals?"]
        )
        mock_conversation_manager.handle_message.return_value = mock_response
        
        # Create a task to run the WebSocket endpoint
        async def run_websocket():
            try:
                await websocket_endpoint(
                    mock_websocket,
                    user_id,
                    mock_conversation_manager,
                    mock_user_context_manager
                )
            except Exception:
                # Expected when mock WebSocket runs out of messages
                pass
        
        # Run the WebSocket endpoint briefly
        task = asyncio.create_task(run_websocket())
        await asyncio.sleep(0.2)  # Let it process the message
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify user context was checked/created
        mock_user_context_manager.get_user_context.assert_called_with(user_id)
        
        # Verify conversation manager was called (may be called with either message)
        assert mock_conversation_manager.handle_message.called
        call_args = mock_conversation_manager.handle_message.call_args
        assert call_args[0][0] == user_id  # First arg should be user_id
        assert call_args[0][1] in ["Hello EdAgent", "test message"]  # Second arg should be one of these messages
        
        # Verify messages were sent (welcome + typing indicators + response)
        assert len(mock_websocket.messages_sent) >= 3
        
        # Check for welcome message
        welcome_messages = [msg for msg in mock_websocket.messages_sent if msg.get("type") == "connection_established"]
        assert len(welcome_messages) == 1
        
        # Check for AI response (may have multiple due to mock behavior)
        ai_responses = [msg for msg in mock_websocket.messages_sent if msg.get("type") == "ai_response"]
        assert len(ai_responses) >= 1
        
        ai_response = ai_responses[0]
        assert ai_response["message"] == "Hello! How can I help you today?"
        assert ai_response["response_type"] == "text"
        assert ai_response["confidence_score"] == 0.95
        assert "suggested_actions" in ai_response
        assert "follow_up_questions" in ai_response
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, mock_user_context_manager):
        """Test WebSocket error handling"""
        from edagent.api.websocket import websocket_endpoint
        
        user_id = "test-user-123"
        mock_websocket = MockWebSocket()
        
        # Mock conversation manager that raises an error
        mock_conversation_manager = AsyncMock()
        mock_conversation_manager.handle_message.side_effect = Exception("Test error")
        
        # Add a test message
        mock_websocket.add_received_message({"message": "Test message"})
        
        # Run WebSocket endpoint
        async def run_websocket():
            try:
                await websocket_endpoint(
                    mock_websocket,
                    user_id,
                    mock_conversation_manager,
                    mock_user_context_manager
                )
            except Exception:
                pass
        
        task = asyncio.create_task(run_websocket())
        await asyncio.sleep(0.2)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify error message was sent
        error_messages = [msg for msg in mock_websocket.messages_sent if msg.get("type") == "error"]
        assert len(error_messages) >= 1
        
        error_msg = error_messages[0]
        assert "technical difficulties" in error_msg["message"]
        assert error_msg["error_code"] == "internal_error"
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_message_format(self, mock_conversation_manager, mock_user_context_manager):
        """Test handling of invalid message formats"""
        from edagent.api.websocket import websocket_endpoint
        
        user_id = "test-user-123"
        mock_websocket = MockWebSocket()
        
        # Add invalid message format
        mock_websocket.add_received_message({"invalid": "format"})
        
        async def run_websocket():
            try:
                await websocket_endpoint(
                    mock_websocket,
                    user_id,
                    mock_conversation_manager,
                    mock_user_context_manager
                )
            except Exception:
                pass
        
        task = asyncio.create_task(run_websocket())
        await asyncio.sleep(0.2)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify error message was sent for invalid format
        error_messages = [msg for msg in mock_websocket.messages_sent if msg.get("type") == "error"]
        assert len(error_messages) >= 1
        
        error_msg = error_messages[0]
        assert "Invalid message format" in error_msg["message"]
        assert error_msg["error_code"] == "invalid_format"


class TestWebSocketAPI:
    """Test WebSocket API endpoints"""
    
    def test_websocket_status_endpoint(self, clean_connection_manager):
        """Test WebSocket status endpoint"""
        app = create_app()
        
        with TestClient(app) as client:
            # Test with no active connections
            response = client.get("/api/v1/ws/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["active_connections"] == 0
            assert data["active_users"] == []
            assert data["connection_details"] == {}
            
            # Add mock connections
            clean_connection_manager.active_connections["user1"] = MockWebSocket()
            clean_connection_manager.connection_metadata["user1"] = {
                "connected_at": datetime.now(),
                "message_count": 5,
                "last_activity": datetime.now()
            }
            
            # Test with active connections
            response = client.get("/api/v1/ws/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["active_connections"] == 1
            assert "user1" in data["active_users"]
            assert "user1" in data["connection_details"]
            assert data["connection_details"]["user1"]["message_count"] == 5
    
    def test_broadcast_endpoint(self, clean_connection_manager):
        """Test broadcast message endpoint"""
        app = create_app()
        
        with TestClient(app) as client:
            # Test broadcast to all users
            broadcast_data = {
                "message": "System maintenance in 10 minutes",
                "user_ids": None
            }
            
            response = client.post("/api/v1/ws/broadcast", json=broadcast_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == "Broadcast sent"
            assert data["sent_to"] == 0  # No active connections
            assert data["total_requested"] == 0
            
            # Add mock connection
            mock_ws = MockWebSocket()
            clean_connection_manager.active_connections["user1"] = mock_ws
            
            # Test broadcast to specific users
            broadcast_data = {
                "message": "Hello user1!",
                "user_ids": ["user1", "user2"]  # user2 not connected
            }
            
            response = client.post("/api/v1/ws/broadcast", json=broadcast_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["sent_to"] == 1  # Only user1 is connected
            assert data["total_requested"] == 2


@pytest.mark.asyncio
async def test_websocket_connection_cleanup():
    """Test that WebSocket connections are properly cleaned up"""
    manager = ConnectionManager()
    mock_ws = MockWebSocket()
    user_id = "cleanup-test-user"
    
    # Connect user
    await manager.connect(mock_ws, user_id)
    assert manager.is_connected(user_id)
    
    # Simulate connection error during send
    mock_ws.is_closed = True
    
    # Try to send message (should trigger cleanup)
    success = await manager.send_message(user_id, {"test": "message"})
    
    # Verify connection was cleaned up
    assert success is False
    assert not manager.is_connected(user_id)
    assert user_id not in manager.active_connections
    assert user_id not in manager.connection_metadata


@pytest.mark.asyncio
async def test_websocket_concurrent_connections():
    """Test handling multiple concurrent WebSocket connections"""
    manager = ConnectionManager()
    
    # Create multiple mock connections
    connections = {}
    for i in range(5):
        user_id = f"user-{i}"
        mock_ws = MockWebSocket()
        connections[user_id] = mock_ws
        await manager.connect(mock_ws, user_id)
    
    # Verify all connections are active
    assert len(manager.get_active_users()) == 5
    
    # Send message to all users
    test_message = {"type": "test", "content": "Broadcast test"}
    
    for user_id in connections:
        success = await manager.send_message(user_id, test_message)
        assert success is True
    
    # Verify all users received the message
    for user_id, mock_ws in connections.items():
        # Should have welcome message + test message
        assert len(mock_ws.messages_sent) >= 2
        assert any(msg.get("content") == "Broadcast test" for msg in mock_ws.messages_sent)
    
    # Disconnect all users
    for user_id in list(connections.keys()):
        await manager.disconnect(user_id)
    
    # Verify all connections are cleaned up
    assert len(manager.get_active_users()) == 0