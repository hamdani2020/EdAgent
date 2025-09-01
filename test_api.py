"""
Simple test script to verify the FastAPI application works
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from edagent.api.app import create_app


def test_api_creation():
    """Test that the FastAPI app can be created"""
    try:
        app = create_app()
        print("✓ FastAPI app created successfully")
        
        # Test with TestClient
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        print(f"✓ Health endpoint status: {response.status_code}")
        print(f"✓ Health response: {response.json()}")
        
        # Test OpenAPI docs
        response = client.get("/docs")
        print(f"✓ Docs endpoint status: {response.status_code}")
        
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        print(f"✓ OpenAPI schema status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing FastAPI application...")
    success = test_api_creation()
    
    if success:
        print("\n✓ All tests passed! FastAPI application is working correctly.")
    else:
        print("\n✗ Tests failed. Check the errors above.")
        sys.exit(1)