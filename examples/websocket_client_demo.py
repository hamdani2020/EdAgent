"""
WebSocket client demo for testing EdAgent real-time chat functionality
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Optional


class EdAgentWebSocketClient:
    """Simple WebSocket client for testing EdAgent chat functionality"""
    
    def __init__(self, base_url: str = "ws://localhost:8000", user_id: str = "demo-user"):
        self.base_url = base_url
        self.user_id = user_id
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
    
    async def connect(self):
        """Connect to the EdAgent WebSocket endpoint"""
        try:
            url = f"{self.base_url}/api/v1/ws/{self.user_id}"
            print(f"Connecting to {url}...")
            
            self.websocket = await websockets.connect(url)
            self.running = True
            
            print("✅ Connected to EdAgent!")
            print("Type 'quit' to exit, 'help' for commands\n")
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the WebSocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("👋 Disconnected from EdAgent")
    
    async def send_message(self, message: str):
        """Send a message to EdAgent"""
        if not self.websocket:
            print("❌ Not connected")
            return
        
        try:
            message_data = {
                "message": message,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "client": "demo"
                }
            }
            
            await self.websocket.send(json.dumps(message_data))
            print(f"📤 You: {message}")
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
    
    async def listen_for_messages(self):
        """Listen for incoming messages from EdAgent"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_incoming_message(data)
                except json.JSONDecodeError:
                    print(f"❌ Received invalid JSON: {message}")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
            self.running = False
        except Exception as e:
            print(f"❌ Error in message listener: {e}")
            self.running = False
    
    async def handle_incoming_message(self, data: dict):
        """Handle different types of incoming messages"""
        message_type = data.get("type", "unknown")
        
        if message_type == "connection_established":
            print(f"🤖 EdAgent: {data.get('message', 'Connected!')}")
        
        elif message_type == "ai_response":
            print(f"🤖 EdAgent: {data.get('message', '')}")
            
            # Show additional information if available
            if data.get("confidence_score"):
                confidence = data["confidence_score"]
                confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                print(f"   {confidence_emoji} Confidence: {confidence:.1%}")
            
            if data.get("suggested_actions"):
                print("   💡 Suggested actions:")
                for action in data["suggested_actions"]:
                    print(f"      • {action}")
            
            if data.get("follow_up_questions"):
                print("   ❓ Follow-up questions:")
                for question in data["follow_up_questions"]:
                    print(f"      • {question}")
            
            if data.get("content_recommendations"):
                print("   📚 Content recommendations:")
                for rec in data["content_recommendations"][:3]:  # Show first 3
                    title = rec.get("title", "Unknown")
                    platform = rec.get("platform", "Unknown")
                    is_free = "🆓" if rec.get("is_free", False) else "💰"
                    print(f"      {is_free} {title} ({platform})")
        
        elif message_type == "typing_indicator":
            if data.get("is_typing"):
                print("🤖 EdAgent is typing...")
            # Don't print when typing stops to avoid clutter
        
        elif message_type == "error":
            error_msg = data.get("message", "Unknown error")
            error_code = data.get("error_code", "unknown")
            print(f"❌ Error ({error_code}): {error_msg}")
        
        elif message_type == "broadcast":
            print(f"📢 Broadcast: {data.get('message', '')}")
        
        elif message_type == "disconnection":
            reason = data.get("reason", "unknown")
            print(f"👋 Disconnected: {reason}")
            self.running = False
        
        else:
            print(f"❓ Unknown message type '{message_type}': {data}")
        
        print()  # Add blank line for readability
    
    async def handle_user_input(self):
        """Handle user input from console"""
        while self.running:
            try:
                # Use asyncio to get user input without blocking
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "💬 "
                )
                
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                elif user_input.lower() == 'status':
                    await self.show_status()
                    continue
                
                # Send message to EdAgent
                await self.send_message(user_input)
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error handling input: {e}")
        
        await self.disconnect()
    
    def show_help(self):
        """Show available commands"""
        print("\n📋 Available commands:")
        print("  help     - Show this help message")
        print("  status   - Show connection status")
        print("  quit     - Exit the chat")
        print("\n💡 Try asking EdAgent about:")
        print("  • Your career goals")
        print("  • Skill assessments")
        print("  • Learning paths")
        print("  • Course recommendations")
        print()
    
    async def show_status(self):
        """Show connection status"""
        if self.websocket and not self.websocket.closed:
            print(f"✅ Connected as user: {self.user_id}")
            print(f"🔗 WebSocket state: {self.websocket.state.name}")
        else:
            print("❌ Not connected")
        print()
    
    async def run(self):
        """Run the WebSocket client"""
        try:
            await self.connect()
            
            # Start listening for messages and handling user input concurrently
            await asyncio.gather(
                self.listen_for_messages(),
                self.handle_user_input()
            )
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            if self.websocket and not self.websocket.closed:
                await self.disconnect()


async def main():
    """Main function to run the demo client"""
    print("🚀 EdAgent WebSocket Client Demo")
    print("=" * 40)
    
    # You can customize these values
    base_url = "ws://localhost:8000"
    user_id = f"demo-user-{datetime.now().strftime('%H%M%S')}"
    
    client = EdAgentWebSocketClient(base_url, user_id)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())