"""
WebSocket endpoints and connection management for real-time chat
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.routing import APIRouter

from ..services.conversation_manager import ConversationManager
from ..services.user_context_manager import UserContextManager
from ..models.conversation import ConversationResponse, MessageType
from .dependencies import get_conversation_manager, get_user_context_manager
from .exceptions import ConversationError, UserNotFoundError
from .schemas import (
    WebSocketConnectionStatus, BroadcastRequest, BroadcastResponse,
    WebSocketMessageType, WebSocketIncomingMessage
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Connection metadata: user_id -> connection info
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Close existing connection if user reconnects
        if user_id in self.active_connections:
            await self.disconnect(user_id, reason="reconnection")
        
        self.active_connections[user_id] = websocket
        self.connection_metadata[user_id] = {
            "connected_at": datetime.now(),
            "message_count": 0,
            "last_activity": datetime.now()
        }
        
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Send welcome message
        await self.send_message(user_id, {
            "type": WebSocketMessageType.CONNECTION_ESTABLISHED,
            "message": "Connected to EdAgent! How can I help you today?",
            "timestamp": datetime.now().isoformat()
        })
    
    async def disconnect(self, user_id: str, reason: str = "client_disconnect") -> None:
        """Disconnect a WebSocket connection"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            
            try:
                # Send disconnect message if connection is still open
                if reason != "connection_error":
                    await websocket.send_json({
                        "type": WebSocketMessageType.DISCONNECTION,
                        "message": "Connection closed",
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Error sending disconnect message to {user_id}: {e}")
            
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket for {user_id}: {e}")
            
            # Clean up connection data
            del self.active_connections[user_id]
            if user_id in self.connection_metadata:
                del self.connection_metadata[user_id]
            
            logger.info(f"WebSocket connection closed for user {user_id}, reason: {reason}")
    
    async def send_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to send message to disconnected user {user_id}")
            return False
        
        websocket = self.active_connections[user_id]
        
        try:
            await websocket.send_json(message)
            
            # Update connection metadata
            if user_id in self.connection_metadata:
                self.connection_metadata[user_id]["message_count"] += 1
                self.connection_metadata[user_id]["last_activity"] = datetime.now()
            
            return True
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            # Connection is likely broken, clean it up
            await self.disconnect(user_id, reason="connection_error")
            return False
    
    async def send_typing_indicator(self, user_id: str, is_typing: bool = True) -> bool:
        """Send typing indicator to user"""
        return await self.send_message(user_id, {
            "type": WebSocketMessageType.TYPING_INDICATOR,
            "is_typing": is_typing,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_error(self, user_id: str, error_message: str, error_code: str = "general_error") -> bool:
        """Send error message to user"""
        return await self.send_message(user_id, {
            "type": WebSocketMessageType.ERROR,
            "message": error_message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_active_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get connection metadata for a user"""
        return self.connection_metadata.get(user_id)
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.active_connections


# Global connection manager instance
connection_manager = ConnectionManager()

# WebSocket router
websocket_router = APIRouter()


@websocket_router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    WebSocket endpoint for real-time chat with EdAgent
    
    Args:
        websocket: WebSocket connection
        user_id: Unique identifier for the user
        conversation_manager: Injected conversation manager service
        user_context_manager: Injected user context manager service
    """
    try:
        # Verify user exists or create new user context
        try:
            user_context = await user_context_manager.get_user_context(user_id)
            if not user_context:
                # Create new user context for new users
                user_context = await user_context_manager.create_user_context(user_id)
                logger.info(f"Created new user context for WebSocket user {user_id}")
        except Exception as e:
            logger.error(f"Error verifying/creating user context for {user_id}: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User verification failed")
            return
        
        # Establish WebSocket connection
        await connection_manager.connect(websocket, user_id)
        
        try:
            while True:
                # Wait for message from client
                data = await websocket.receive_json()
                
                # Validate message format
                if not isinstance(data, dict) or "message" not in data:
                    await connection_manager.send_error(
                        user_id, 
                        "Invalid message format. Expected JSON with 'message' field.",
                        "invalid_format"
                    )
                    continue
                
                message_content = data["message"].strip()
                
                # Skip empty messages
                if not message_content:
                    continue
                
                # Send typing indicator to show AI is processing
                await connection_manager.send_typing_indicator(user_id, True)
                
                try:
                    # Process message through conversation manager
                    response = await conversation_manager.handle_message(user_id, message_content)
                    
                    # Stop typing indicator
                    await connection_manager.send_typing_indicator(user_id, False)
                    
                    # Format and send response
                    response_data = {
                        "type": WebSocketMessageType.AI_RESPONSE,
                        "message": response.message,
                        "response_type": response.response_type,
                        "confidence_score": response.confidence_score,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": response.metadata or {}
                    }
                    
                    # Add optional fields if present
                    if response.suggested_actions:
                        response_data["suggested_actions"] = response.suggested_actions
                    
                    if response.content_recommendations:
                        response_data["content_recommendations"] = [
                            rec if isinstance(rec, dict) else rec.to_dict() 
                            for rec in response.content_recommendations
                        ]
                    
                    if response.follow_up_questions:
                        response_data["follow_up_questions"] = response.follow_up_questions
                    
                    await connection_manager.send_message(user_id, response_data)
                    
                except ConversationError as e:
                    await connection_manager.send_typing_indicator(user_id, False)
                    await connection_manager.send_error(
                        user_id,
                        f"I'm having trouble processing your message: {e.message}",
                        "conversation_error"
                    )
                    logger.error(f"Conversation error for user {user_id}: {e}")
                
                except Exception as e:
                    await connection_manager.send_typing_indicator(user_id, False)
                    await connection_manager.send_error(
                        user_id,
                        "I'm experiencing technical difficulties. Please try again.",
                        "internal_error"
                    )
                    logger.error(f"Unexpected error processing message for user {user_id}: {e}")
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {user_id} disconnected normally")
        
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket connection for user {user_id}: {e}")
        
        finally:
            # Clean up connection
            await connection_manager.disconnect(user_id, reason="session_ended")
    
    except Exception as e:
        logger.error(f"Fatal error in WebSocket endpoint for user {user_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@websocket_router.get("/ws/status", response_model=WebSocketConnectionStatus)
async def websocket_status():
    """Get WebSocket connection status and statistics"""
    active_users = connection_manager.get_active_users()
    
    connection_details = {}
    
    # Add connection details for each user
    for user_id in active_users:
        conn_info = connection_manager.get_connection_info(user_id)
        if conn_info:
            connection_details[user_id] = {
                "connected_at": conn_info["connected_at"].isoformat(),
                "message_count": conn_info["message_count"],
                "last_activity": conn_info["last_activity"].isoformat()
            }
    
    return WebSocketConnectionStatus(
        active_connections=len(active_users),
        active_users=active_users,
        connection_details=connection_details
    )


@websocket_router.post("/ws/broadcast", response_model=BroadcastResponse)
async def broadcast_message(request: BroadcastRequest):
    """
    Broadcast a message to connected users (admin endpoint)
    
    Args:
        request: Broadcast request with message and optional user IDs
    """
    user_ids = request.user_ids
    if user_ids is None:
        user_ids = connection_manager.get_active_users()
    
    broadcast_data = {
        "type": WebSocketMessageType.BROADCAST,
        "message": request.message,
        "timestamp": datetime.now().isoformat()
    }
    
    sent_count = 0
    for user_id in user_ids:
        if connection_manager.is_connected(user_id):
            success = await connection_manager.send_message(user_id, broadcast_data)
            if success:
                sent_count += 1
    
    return BroadcastResponse(
        message="Broadcast sent",
        sent_to=sent_count,
        total_requested=len(user_ids)
    )


def get_connection_manager() -> ConnectionManager:
    """Dependency to get the connection manager instance"""
    return connection_manager