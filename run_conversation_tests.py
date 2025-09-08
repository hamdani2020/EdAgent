#!/usr/bin/env python3
"""
Test runner for conversation interface and WebSocket integration tests
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run conversation integration tests"""
    print("🧪 Running Conversation Interface and WebSocket Integration Tests")
    print("=" * 70)
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Test files to run
    test_files = [
        "test_conversation_integration.py"
    ]
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
        import pytest
    
    # Check if required modules are available
    required_modules = [
        "streamlit",
        "httpx", 
        "websockets",
        "tenacity"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} is available")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} not found")
    
    if missing_modules:
        print(f"\n📦 Installing missing modules: {', '.join(missing_modules)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_modules)
    
    print("\n🚀 Starting tests...")
    print("-" * 50)
    
    # Run tests with detailed output
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📋 Running {test_file}")
            print("-" * 30)
            
            # Run pytest with verbose output
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file,
                "-v",
                "--tb=short",
                "--no-header",
                "--disable-warnings"
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed with return code {result.returncode}")
        else:
            print(f"⚠️  Test file {test_file} not found")
    
    print("\n" + "=" * 70)
    print("🏁 Test execution completed")

def run_specific_test_class(test_class: str):
    """Run a specific test class"""
    print(f"🧪 Running specific test class: {test_class}")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_conversation_integration.py",
        f"-k", test_class,
        "-v",
        "--tb=short"
    ])
    
    return result.returncode == 0

def run_integration_demo():
    """Run a demo of the conversation integration"""
    print("🎭 Running Conversation Integration Demo")
    print("=" * 50)
    
    try:
        # Import required modules
        import asyncio
        from unittest.mock import Mock
        from streamlit_api_client import ConversationResponse
        from streamlit_websocket import EnhancedStreamlitWebSocketClient
        
        print("✅ All modules imported successfully")
        
        # Demo 1: API Client Response Processing
        print("\n📡 Demo 1: API Response Processing")
        print("-" * 30)
        
        sample_response = ConversationResponse(
            message="Hello! I can help you with career planning. What would you like to work on?",
            response_type="text",
            confidence_score=0.92,
            suggested_actions=["Take a skill assessment", "Create a learning path"],
            content_recommendations=[
                {
                    "title": "Python for Beginners",
                    "description": "Learn Python programming from scratch",
                    "url": "https://example.com/python-course",
                    "type": "course"
                }
            ],
            follow_up_questions=["What's your current experience level?", "What are your career goals?"]
        )
        
        print(f"Message: {sample_response.message}")
        print(f"Confidence: {sample_response.confidence_score}")
        print(f"Suggested Actions: {sample_response.suggested_actions}")
        print(f"Recommendations: {len(sample_response.content_recommendations)}")
        print(f"Follow-up Questions: {len(sample_response.follow_up_questions)}")
        
        # Demo 2: WebSocket Client Initialization
        print("\n🔗 Demo 2: WebSocket Client")
        print("-" * 30)
        
        ws_client = EnhancedStreamlitWebSocketClient("ws://localhost:8000/api/v1")
        print(f"WebSocket URL: {ws_client.ws_url}")
        print(f"Connected: {ws_client.is_connected}")
        print(f"Max Reconnect Attempts: {ws_client.max_reconnect_attempts}")
        
        # Demo 3: Connection Statistics
        stats = ws_client.get_connection_stats()
        print(f"Connection Stats: {stats}")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "demo":
            run_integration_demo()
        elif command.startswith("class:"):
            test_class = command.split(":", 1)[1]
            success = run_specific_test_class(test_class)
            sys.exit(0 if success else 1)
        elif command == "help":
            print("Usage:")
            print("  python run_conversation_tests.py          # Run all tests")
            print("  python run_conversation_tests.py demo     # Run integration demo")
            print("  python run_conversation_tests.py class:TestConversationFlow  # Run specific test class")
            print("  python run_conversation_tests.py help     # Show this help")
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        run_tests()