"""
WebSocket client for real-time chat functionality in Streamlit
"""

import asyncio
import websockets
import json
import threading
import queue
import logging
from typing import Dict, Any, Callable, Optional
import streamlit as st

logger = logging.getLogger(__name__)

class StreamlitWebSocketClient:
    """WebSocket client for Streamlit integration"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.is_connected = False
        self.connection_thread = None
        self.message_handler = None
        
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Set the message handler function"""
        self.message_handler = handler
    
    async def connect(self, user_id: str, auth_token: str):
        """Connect to WebSocket server"""
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "User-ID": user_id
            }
            
            self.websocket = await websockets.connect(
                f"{self.ws_url}/chat/{user_id}",
                extra_headers=headers
            )
            
            self.is_connected = True
            logger.info(f"Connected to WebSocket for user {user_id}")
            
            # Start listening for messages
            await self.listen_for_messages()
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            self.is_connected = False
            raise
    
    async def listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle different message types
                    if data.get("type") == "response":
                        self.response_queue.put(data)
                        
                        # Call message handler if set
                        if self.message_handler:
                            self.message_handler(data)
                    
                    elif data.get("type") == "error":
                        logger.error(f"WebSocket error: {data.get('message')}")
                    
                    elif data.get("type") == "status":
                        logger.info(f"WebSocket status: {data.get('message')}")
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error listening for messages: {str(e)}")
            self.is_connected = False
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None):
        """Send a message through WebSocket"""
        if not self.is_connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        try:
            data = {
                "type": "message",
                "content": message,
                "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
            }
            
            if conversation_id:
                data["conversation_id"] = conversation_id
            
            await self.websocket.send(json.dumps(data))
            logger.info(f"Sent message: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")
    
    def start_connection_thread(self, user_id: str, auth_token: str):
        """Start WebSocket connection in a separate thread"""
        def run_connection():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.connect(user_id, auth_token))
            except Exception as e:
                logger.error(f"Connection thread error: {str(e)}")
            finally:
                loop.close()
        
        self.connection_thread = threading.Thread(target=run_connection, daemon=True)
        self.connection_thread.start()
    
    def send_message_sync(self, message: str, conversation_id: Optional[str] = None):
        """Send message synchronously (for Streamlit)"""
        if not self.is_connected:
            return False
        
        try:
            # Put message in queue for async sending
            self.message_queue.put({
                "message": message,
                "conversation_id": conversation_id
            })
            return True
        except Exception as e:
            logger.error(f"Failed to queue message: {str(e)}")
            return False
    
    def get_latest_response(self) -> Optional[Dict[str, Any]]:
        """Get the latest response from the queue"""
        try:
            return self.response_queue.get_nowait()
        except queue.Empty:
            return None

# Streamlit integration functions
def initialize_websocket():
    """Initialize WebSocket client in Streamlit session state"""
    if "ws_client" not in st.session_state:
        ws_url = "ws://localhost:8000/api/v1"
        st.session_state.ws_client = StreamlitWebSocketClient(ws_url)
    
    return st.session_state.ws_client

def connect_websocket(user_id: str, auth_token: str):
    """Connect WebSocket for the current user"""
    ws_client = initialize_websocket()
    
    if not ws_client.is_connected:
        try:
            ws_client.start_connection_thread(user_id, auth_token)
            return True
        except Exception as e:
            st.error(f"Failed to connect WebSocket: {str(e)}")
            return False
    
    return True

def send_websocket_message(message: str, conversation_id: Optional[str] = None):
    """Send message through WebSocket"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        return ws_client.send_message_sync(message, conversation_id)
    return False

def get_websocket_response():
    """Get latest WebSocket response"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        return ws_client.get_latest_response()
    return None

def disconnect_websocket():
    """Disconnect WebSocket"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        if ws_client.is_connected:
            # Note: This is a simplified disconnect for Streamlit
            # In a full implementation, you'd properly close the connection
            ws_client.is_connected = False
            del st.session_state.ws_client