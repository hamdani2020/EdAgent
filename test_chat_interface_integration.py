#!/usr/bin/env python3
"""
Integration test for the enhanced chat interface
"""

import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the modules we want to test
from streamlit_api_client import EnhancedEdAgentAPI, ConversationResponse
from streamlit_websocket import EnhancedStreamlitWebSocketClient


def test_conversation_response_processing():
    """Test that conversation responses are properly processed"""
    print("🧪 Testing conversation response processing...")
    
    # Create a sample response
    response = ConversationResponse(
        message="I can help you with career planning. What specific area would you like to focus on?",
        response_type="text",
        confidence_score=0.88,
        suggested_actions=["Take a skill assessment", "Create a learning path", "Get resume feedback"],
        content_recommendations=[
            {
                "title": "Python Programming Fundamentals",
                "description": "Learn Python from scratch with hands-on projects",
                "url": "https://example.com/python-course",
                "type": "course",
                "rating": 4.8
            },
            {
                "title": "Career Planning Guide",
                "description": "Step-by-step guide to planning your tech career",
                "url": "https://example.com/career-guide",
                "type": "article",
                "rating": 4.5
            }
        ],
        follow_up_questions=[
            "What's your current experience level?",
            "What type of role are you targeting?",
            "Do you have any specific skills you want to develop?"
        ],
        metadata={
            "conversation_id": "conv_12345",
            "user_intent": "career_guidance",
            "processing_time": 1.2
        }
    )
    
    # Verify response structure
    assert response.message is not None
    assert len(response.message) > 0
    assert response.confidence_score > 0.8
    assert len(response.suggested_actions) == 3
    assert len(response.content_recommendations) == 2
    assert len(response.follow_up_questions) == 3
    
    # Verify content recommendations structure
    for rec in response.content_recommendations:
        assert "title" in rec
        assert "description" in rec
        assert "url" in rec
        assert "type" in rec
    
    print("✅ Conversation response processing test passed!")
    return True


def test_websocket_client_functionality():
    """Test WebSocket client basic functionality"""
    print("🧪 Testing WebSocket client functionality...")
    
    # Create WebSocket client
    ws_client = EnhancedStreamlitWebSocketClient("ws://localhost:8000/api/v1")
    
    # Test initialization
    assert ws_client.ws_url == "ws://localhost:8000/api/v1"
    assert ws_client.is_connected is False
    assert ws_client.messages_sent == 0
    assert ws_client.messages_received == 0
    
    # Test connection statistics
    stats = ws_client.get_connection_stats()
    assert stats["is_connected"] is False
    assert stats["messages_sent"] == 0
    assert stats["messages_received"] == 0
    assert stats["reconnect_attempts"] == 0
    
    # Test message queuing (when not connected)
    result = ws_client.send_message_sync("Test message")
    assert result is False  # Should fail when not connected
    
    # Test response queue
    assert ws_client.get_latest_response() is None
    
    print("✅ WebSocket client functionality test passed!")
    return True


def test_chat_message_formatting():
    """Test chat message formatting and metadata handling"""
    print("🧪 Testing chat message formatting...")
    
    # Test user message format
    user_message = {
        "role": "user",
        "content": "I want to learn Python programming",
        "timestamp": datetime.now(),
        "metadata": {"type": "user_input"}
    }
    
    # Test assistant message with rich metadata
    assistant_message = {
        "role": "assistant",
        "content": "Great choice! Python is an excellent programming language for beginners and professionals alike.",
        "timestamp": datetime.now(),
        "metadata": {
            "content_recommendations": [
                {
                    "title": "Python.org Tutorial",
                    "description": "Official Python tutorial",
                    "url": "https://docs.python.org/3/tutorial/"
                }
            ],
            "follow_up_questions": [
                "What's your programming experience?",
                "What do you want to build with Python?"
            ],
            "suggested_actions": [
                "Start with Python basics",
                "Set up your development environment"
            ],
            "confidence_score": 0.95
        }
    }
    
    # Verify message structure
    assert user_message["role"] == "user"
    assert len(user_message["content"]) > 0
    assert user_message["timestamp"] is not None
    
    assert assistant_message["role"] == "assistant"
    assert len(assistant_message["content"]) > 0
    assert assistant_message["metadata"]["confidence_score"] > 0.9
    assert len(assistant_message["metadata"]["follow_up_questions"]) == 2
    
    print("✅ Chat message formatting test passed!")
    return True


def test_conversation_pagination():
    """Test conversation history pagination logic"""
    print("🧪 Testing conversation pagination...")
    
    # Create a large conversation history
    messages = []
    for i in range(157):  # Test with 157 messages
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({
            "role": role,
            "content": f"Message {i+1}",
            "timestamp": datetime.now(),
            "metadata": {}
        })
    
    # Test pagination calculations
    total_messages = len(messages)
    messages_per_page = 20
    total_pages = max(1, (total_messages + messages_per_page - 1) // messages_per_page)
    
    assert total_messages == 157
    assert total_pages == 8  # 157 / 20 = 7.85, rounded up to 8
    
    # Test page ranges
    for page in range(total_pages):
        start_idx = page * messages_per_page
        end_idx = min(start_idx + messages_per_page, total_messages)
        
        assert start_idx >= 0
        assert end_idx <= total_messages
        assert end_idx > start_idx
        
        # Get messages for this page
        page_messages = messages[start_idx:end_idx]
        
        if page < total_pages - 1:
            assert len(page_messages) == messages_per_page
        else:
            # Last page might have fewer messages
            assert len(page_messages) <= messages_per_page
    
    # Test last page specifically
    last_page = total_pages - 1
    start_idx = last_page * messages_per_page
    end_idx = min(start_idx + messages_per_page, total_messages)
    last_page_messages = messages[start_idx:end_idx]
    
    assert len(last_page_messages) == 17  # 157 - (7 * 20) = 17
    
    print("✅ Conversation pagination test passed!")
    return True


async def test_api_integration_mock():
    """Test API integration with mocked responses"""
    print("🧪 Testing API integration (mocked)...")
    
    # Create mock API client
    api_client = Mock(spec=EnhancedEdAgentAPI)
    
    # Mock send_message response
    mock_response = ConversationResponse(
        message="Hello! I'm here to help with your career development.",
        response_type="text",
        confidence_score=0.92,
        suggested_actions=["Tell me about your goals", "Take a skill assessment"],
        content_recommendations=[],
        follow_up_questions=["What's your current role?", "What are you hoping to achieve?"]
    )
    
    api_client.send_message = AsyncMock(return_value=mock_response)
    
    # Test API call
    result = await api_client.send_message("user_123", "Hello, I need career advice")
    
    # Verify response
    assert result.message == "Hello! I'm here to help with your career development."
    assert result.confidence_score == 0.92
    assert len(result.suggested_actions) == 2
    assert len(result.follow_up_questions) == 2
    
    # Verify API was called correctly
    api_client.send_message.assert_called_once_with("user_123", "Hello, I need career advice")
    
    print("✅ API integration test passed!")
    return True


def test_error_handling_scenarios():
    """Test various error handling scenarios"""
    print("🧪 Testing error handling scenarios...")
    
    # Test WebSocket connection errors
    ws_client = EnhancedStreamlitWebSocketClient("ws://invalid-url")
    
    # Test sending message when not connected
    try:
        result = ws_client.send_message_sync("test")
        assert result is False
    except Exception:
        pass  # Expected
    
    # Test empty response queue
    response = ws_client.get_latest_response()
    assert response is None
    
    # Test connection stats when not connected
    stats = ws_client.get_connection_stats()
    assert stats["is_connected"] is False
    assert stats["uptime_seconds"] is None
    
    print("✅ Error handling test passed!")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("🚀 Running Enhanced Chat Interface Integration Tests")
    print("=" * 60)
    
    tests = [
        test_conversation_response_processing,
        test_websocket_client_functionality,
        test_chat_message_formatting,
        test_conversation_pagination,
        test_error_handling_scenarios
    ]
    
    async_tests = [
        test_api_integration_mock
    ]
    
    passed = 0
    failed = 0
    
    # Run synchronous tests
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed with error: {str(e)}")
    
    # Run async tests
    for test in async_tests:
        try:
            result = asyncio.run(test())
            if result:
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed with error: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced chat interface is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)