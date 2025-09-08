"""
Enhanced WebSocket client for real-time chat functionality in Streamlit
"""

import asyncio
import websockets
import json
import threading
import queue
import logging
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
import streamlit as st

logger = logging.getLogger(__name__)

class EnhancedStreamlitWebSocketClient:
    """Enhanced WebSocket client with connection management and reconnection logic"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.is_connected = False
        self.connection_thread = None
        self.message_handler = None
        
        # Connection management
        self.user_id = None
        self.auth_token = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 30
        self.last_ping = None
        self.ping_interval = 30  # Ping every 30 seconds
        
        # Message handling
        self.message_handlers = {}
        self.connection_status_callback = None
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_start_time = None
        
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Set the message handler function"""
        self.message_handler = handler
    
    def set_connection_status_callback(self, callback: Callable[[str], None]):
        """Set callback for connection status changes"""
        self.connection_status_callback = callback
    
    def _update_connection_status(self, status: str):
        """Update connection status and notify callback"""
        if self.connection_status_callback:
            self.connection_status_callback(status)
    
    async def connect(self, user_id: str, auth_token: str):
        """Connect to WebSocket server with retry logic"""
        self.user_id = user_id
        self.auth_token = auth_token
        
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self._update_connection_status("connecting")
                
                headers = {
                    "Authorization": f"Bearer {auth_token}",
                    "User-ID": user_id
                }
                
                # Connect with timeout
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        f"{self.ws_url}/chat/{user_id}",
                        extra_headers=headers,
                        ping_interval=self.ping_interval,
                        ping_timeout=10
                    ),
                    timeout=10
                )
                
                self.is_connected = True
                self.reconnect_attempts = 0
                self.reconnect_delay = 1
                self.connection_start_time = datetime.now()
                self.last_ping = datetime.now()
                
                logger.info(f"Connected to WebSocket for user {user_id}")
                self._update_connection_status("connected")
                
                # Start message processing tasks
                await asyncio.gather(
                    self.listen_for_messages(),
                    self.process_message_queue(),
                    self.heartbeat_monitor()
                )
                
            except asyncio.TimeoutError:
                logger.error("WebSocket connection timeout")
                self._update_connection_status("timeout")
                await self._handle_reconnection()
                
            except websockets.exceptions.InvalidStatusCode as e:
                logger.error(f"WebSocket connection failed with status {e.status_code}")
                if e.status_code == 401:
                    self._update_connection_status("auth_error")
                    break  # Don't retry on auth errors
                else:
                    self._update_connection_status("error")
                    await self._handle_reconnection()
                    
            except Exception as e:
                logger.error(f"WebSocket connection failed: {str(e)}")
                self._update_connection_status("error")
                await self._handle_reconnection()
    
    async def _handle_reconnection(self):
        """Handle reconnection logic with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self._update_connection_status("failed")
            return
        
        self.reconnect_attempts += 1
        delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), self.max_reconnect_delay)
        
        logger.info(f"Reconnecting in {delay} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        self._update_connection_status("reconnecting")
        
        await asyncio.sleep(delay)
    
    async def heartbeat_monitor(self):
        """Monitor connection health with heartbeat"""
        while self.is_connected:
            try:
                current_time = datetime.now()
                
                # Send ping if needed
                if self.last_ping and (current_time - self.last_ping).seconds > self.ping_interval:
                    await self.websocket.ping()
                    self.last_ping = current_time
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed during heartbeat")
                self.is_connected = False
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
                self.is_connected = False
                break
    
    async def listen_for_messages(self):
        """Listen for incoming messages with enhanced error handling"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.messages_received += 1
                    
                    # Handle different message types
                    message_type = data.get("type", "unknown")
                    
                    if message_type == "response":
                        self.response_queue.put(data)
                        
                        # Call message handler if set
                        if self.message_handler:
                            self.message_handler(data)
                    
                    elif message_type == "error":
                        logger.error(f"WebSocket error: {data.get('message')}")
                        self._handle_server_error(data)
                    
                    elif message_type == "status":
                        logger.info(f"WebSocket status: {data.get('message')}")
                        self._handle_status_message(data)
                    
                    elif message_type == "ping":
                        # Respond to server ping
                        await self.websocket.send(json.dumps({"type": "pong"}))
                    
                    elif message_type == "typing":
                        # Handle typing indicators
                        self._handle_typing_indicator(data)
                    
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
            self._update_connection_status("disconnected")
        except Exception as e:
            logger.error(f"Error listening for messages: {str(e)}")
            self.is_connected = False
            self._update_connection_status("error")
    
    async def process_message_queue(self):
        """Process outgoing message queue"""
        while self.is_connected:
            try:
                # Check for queued messages
                if not self.message_queue.empty():
                    message_data = self.message_queue.get_nowait()
                    await self._send_message_internal(
                        message_data["message"], 
                        message_data.get("conversation_id")
                    )
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing message queue: {str(e)}")
                await asyncio.sleep(1)
    
    def _handle_server_error(self, error_data: Dict[str, Any]):
        """Handle server error messages"""
        error_code = error_data.get("code")
        error_message = error_data.get("message", "Unknown error")
        
        if error_code == "rate_limit":
            logger.warning("Rate limit exceeded")
            self._update_connection_status("rate_limited")
        elif error_code == "auth_expired":
            logger.warning("Authentication expired")
            self._update_connection_status("auth_expired")
        else:
            logger.error(f"Server error: {error_message}")
    
    def _handle_status_message(self, status_data: Dict[str, Any]):
        """Handle server status messages"""
        status = status_data.get("status")
        if status == "ready":
            logger.info("Server ready for messages")
        elif status == "busy":
            logger.info("Server is busy processing")
    
    def _handle_typing_indicator(self, typing_data: Dict[str, Any]):
        """Handle typing indicators"""
        is_typing = typing_data.get("is_typing", False)
        user_id = typing_data.get("user_id")
        
        # Store typing status for UI updates
        if "typing_users" not in st.session_state:
            st.session_state.typing_users = set()
        
        if is_typing:
            st.session_state.typing_users.add(user_id)
        else:
            st.session_state.typing_users.discard(user_id)
    
    async def _send_message_internal(self, message: str, conversation_id: Optional[str] = None):
        """Internal method to send message"""
        if not self.is_connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        try:
            data = {
                "type": "message",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id
            }
            
            if conversation_id:
                data["conversation_id"] = conversation_id
            
            await self.websocket.send(json.dumps(data))
            self.messages_sent += 1
            logger.info(f"Sent message: {message[:50]}...")
            
        except websockets.exceptions.ConnectionClosed:
            logger.error("Connection closed while sending message")
            self.is_connected = False
            self._update_connection_status("disconnected")
            raise
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None):
        """Send a message through WebSocket"""
        await self._send_message_internal(message, conversation_id)
    
    async def send_typing_indicator(self, is_typing: bool):
        """Send typing indicator"""
        if not self.is_connected or not self.websocket:
            return
        
        try:
            data = {
                "type": "typing",
                "is_typing": is_typing,
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(data))
            
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self.is_connected = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")
        
        self._update_connection_status("disconnected")
    
    def start_connection_thread(self, user_id: str, auth_token: str):
        """Start WebSocket connection in a separate thread"""
        def run_connection():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.connect(user_id, auth_token))
            except Exception as e:
                logger.error(f"Connection thread error: {str(e)}")
                self._update_connection_status("error")
            finally:
                loop.close()
        
        if self.connection_thread and self.connection_thread.is_alive():
            logger.warning("Connection thread already running")
            return
        
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
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        uptime = None
        if self.connection_start_time:
            uptime = (datetime.now() - self.connection_start_time).total_seconds()
        
        return {
            "is_connected": self.is_connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "reconnect_attempts": self.reconnect_attempts,
            "uptime_seconds": uptime,
            "last_ping": self.last_ping.isoformat() if self.last_ping else None
        }

# Legacy class for backward compatibility
StreamlitWebSocketClient = EnhancedStreamlitWebSocketClient

# Enhanced Streamlit integration functions
def initialize_websocket():
    """Initialize enhanced WebSocket client in Streamlit session state"""
    if "ws_client" not in st.session_state:
        ws_url = "ws://localhost:8000/api/v1"
        st.session_state.ws_client = EnhancedStreamlitWebSocketClient(ws_url)
        
        # Set up connection status callback
        def update_session_status(status: str):
            st.session_state.ws_connection_status = status
        
        st.session_state.ws_client.set_connection_status_callback(update_session_status)
    
    return st.session_state.ws_client

def connect_websocket(user_id: str, auth_token: str):
    """Connect WebSocket for the current user with enhanced error handling"""
    ws_client = initialize_websocket()
    
    if not ws_client.is_connected:
        try:
            ws_client.start_connection_thread(user_id, auth_token)
            
            # Wait a moment for connection to establish
            time.sleep(0.5)
            
            # Check if connection was successful
            if hasattr(st.session_state, 'ws_connection_status'):
                status = st.session_state.ws_connection_status
                if status in ["connected", "connecting"]:
                    return True
                elif status == "auth_error":
                    st.error("🔐 WebSocket authentication failed. Please refresh your session.")
                    return False
                elif status == "timeout":
                    st.warning("⏰ WebSocket connection timed out. Using standard chat mode.")
                    return False
                else:
                    st.warning(f"🔗 WebSocket connection issue: {status}. Using standard chat mode.")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {str(e)}")
            st.error(f"Failed to connect WebSocket: {str(e)}")
            return False
    
    return True

def send_websocket_message(message: str, conversation_id: Optional[str] = None):
    """Send message through WebSocket with enhanced error handling"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        
        if ws_client.is_connected:
            try:
                return ws_client.send_message_sync(message, conversation_id)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {str(e)}")
                return False
        else:
            logger.warning("WebSocket not connected, cannot send message")
            return False
    
    return False

def get_websocket_response():
    """Get latest WebSocket response with timeout"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        return ws_client.get_latest_response()
    return None

def get_websocket_stats():
    """Get WebSocket connection statistics"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        return ws_client.get_connection_stats()
    return None

def send_typing_indicator(is_typing: bool):
    """Send typing indicator through WebSocket"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        if ws_client.is_connected:
            try:
                # Queue typing indicator for async sending
                asyncio.create_task(ws_client.send_typing_indicator(is_typing))
                return True
            except Exception as e:
                logger.error(f"Failed to send typing indicator: {str(e)}")
                return False
    return False

def disconnect_websocket():
    """Properly disconnect WebSocket"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        
        try:
            # Attempt graceful disconnect
            if ws_client.is_connected:
                asyncio.create_task(ws_client.disconnect())
            
            # Clean up session state
            del st.session_state.ws_client
            if "ws_connection_status" in st.session_state:
                del st.session_state.ws_connection_status
            
            logger.info("WebSocket disconnected and cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {str(e)}")
            return False
    
    return True

def get_connection_status():
    """Get current WebSocket connection status"""
    return st.session_state.get("ws_connection_status", "disconnected")

def is_websocket_connected():
    """Check if WebSocket is currently connected"""
    if "ws_client" in st.session_state:
        ws_client = st.session_state.ws_client
        return ws_client.is_connected
    return False