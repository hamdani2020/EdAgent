"""
Example usage of the Enhanced EdAgent API Client
Demonstrates key functionality and error handling
"""

import asyncio
import os
from streamlit_api_client import (
    create_api_client,
    handle_async_api_call,
    display_api_status
)


async def demo_api_client():
    """Demonstrate API client functionality"""
    print("🚀 Enhanced EdAgent API Client Demo")
    print("=" * 50)
    
    # Create API client
    api_base_url = os.getenv("EDAGENT_API_URL", "http://localhost:8000/api/v1")
    api_client = create_api_client(api_base_url)
    
    print(f"📡 API Base URL: {api_client.base_url}")
    print(f"🔐 Authenticated: {api_client.session_manager.is_authenticated()}")
    
    # Demo 1: User Registration (will fail without running server, but shows error handling)
    print("\n1️⃣ Testing User Registration...")
    try:
        auth_result = await api_client.register_user(
            email="demo@example.com",
            password="SecurePassword123!",
            name="Demo User"
        )
        
        if auth_result.success:
            print(f"✅ Registration successful! User ID: {auth_result.user_id}")
            api_client.session_manager.set_auth_data(auth_result)
        else:
            print(f"❌ Registration failed: {auth_result.error}")
    
    except Exception as e:
        print(f"🔧 Expected error (server not running): {e}")
    
    # Demo 2: Send Message (will also fail gracefully)
    print("\n2️⃣ Testing Message Sending...")
    try:
        response = await api_client.send_message(
            user_id="demo_user",
            message="Hello, EdAgent! How can you help me with my career?"
        )
        
        print(f"🤖 AI Response: {response.message}")
        if response.suggested_actions:
            print(f"💡 Suggested Actions: {response.suggested_actions}")
    
    except Exception as e:
        print(f"🔧 Expected error (server not running): {e}")
    
    # Demo 3: Connection Status
    print("\n3️⃣ Connection Status:")
    status = api_client.get_connection_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Demo 4: Circuit Breaker Reset
    print("\n4️⃣ Circuit Breaker Management:")
    print(f"   Failure Count: {api_client.failure_count}")
    print(f"   Circuit Breaker Open: {api_client.failure_count >= api_client.circuit_breaker_threshold}")
    
    if api_client.failure_count > 0:
        print("   🔄 Resetting circuit breaker...")
        api_client.reset_circuit_breaker()
        print(f"   ✅ Reset complete. Failure count: {api_client.failure_count}")
    
    print("\n🎉 Demo completed!")


def demo_sync_usage():
    """Demonstrate synchronous usage with handle_async_api_call"""
    print("\n🔄 Synchronous API Call Demo")
    print("=" * 30)
    
    api_client = create_api_client()
    
    # Use the utility function to handle async calls synchronously
    async def get_status():
        return api_client.get_connection_status()
    
    status = handle_async_api_call(get_status())
    print(f"📊 Connection Status: {status}")


def demo_error_scenarios():
    """Demonstrate different error scenarios"""
    print("\n⚠️ Error Handling Demo")
    print("=" * 25)
    
    from streamlit_api_client import APIError, APIErrorType
    
    # Create different types of errors
    errors = [
        APIError(APIErrorType.AUTHENTICATION_ERROR, "Token expired"),
        APIError(APIErrorType.RATE_LIMIT_ERROR, "Rate limit exceeded", retry_after=60),
        APIError(APIErrorType.NETWORK_ERROR, "Connection failed", is_retryable=True),
        APIError(APIErrorType.VALIDATION_ERROR, "Invalid input data"),
    ]
    
    for error in errors:
        print(f"🔴 {error.error_type.value}: {error.message}")
        print(f"   Retryable: {error.is_retryable}")
        if error.retry_after:
            print(f"   Retry after: {error.retry_after} seconds")
        print()


if __name__ == "__main__":
    print("🎯 Enhanced EdAgent API Client Examples")
    print("=" * 60)
    
    # Run async demo
    asyncio.run(demo_api_client())
    
    # Run sync demo
    demo_sync_usage()
    
    # Show error handling
    demo_error_scenarios()
    
    print("\n✨ All demos completed successfully!")
    print("\nTo use with a real API server:")
    print("1. Set EDAGENT_API_URL environment variable")
    print("2. Ensure the EdAgent API server is running")
    print("3. Run this script again to see real API interactions")