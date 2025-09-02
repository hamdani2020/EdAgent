"""
Tests for authentication middleware
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
import json

from edagent.api.middleware import AuthenticationMiddleware, InputSanitizationMiddleware
from edagent.models.auth import TokenValidationResult, UserSession, SessionStatus
from datetime import datetime, timedelta


class TestAuthenticationMiddleware:
    """Test cases for AuthenticationMiddleware"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()
        
        @app.get("/public")
        async def public_endpoint():
            return {"message": "public"}
        
        @app.get("/api/v1/conversations")
        async def protected_endpoint(request: Request):
            return {
                "message": "protected",
                "user_id": getattr(request.state, 'user_id', None)
            }
        
        return app
    
    @pytest.fixture
    def auth_middleware(self):
        """Create authentication middleware instance"""
        return AuthenticationMiddleware(None)
    
    @pytest.fixture
    def mock_auth_service(self):
        """Create mock authentication service"""
        return AsyncMock()
    
    def test_is_public_path(self, auth_middleware):
        """Test public path detection"""
        assert auth_middleware._is_public_path("/health")
        assert auth_middleware._is_public_path("/docs")
        assert auth_middleware._is_public_path("/api/v1/auth/session")
        assert not auth_middleware._is_public_path("/api/v1/conversations")
    
    def test_requires_auth(self, auth_middleware):
        """Test authentication requirement detection"""
        assert auth_middleware._requires_auth("/api/v1/conversations")
        assert auth_middleware._requires_auth("/api/v1/users")
        assert not auth_middleware._requires_auth("/health")
        assert not auth_middleware._requires_auth("/docs")
    
    @pytest.mark.asyncio
    async def test_public_path_no_auth_required(self, app, mock_auth_service):
        """Test that public paths don't require authentication"""
        middleware = AuthenticationMiddleware(app, mock_auth_service)
        app.add_middleware(AuthenticationMiddleware, auth_service=mock_auth_service)
        
        client = TestClient(app)
        response = client.get("/public")
        
        assert response.status_code == 200
        assert response.json() == {"message": "public"}
        
        # Auth service should not be called
        mock_auth_service.validate_session_token.assert_not_called()
        mock_auth_service.validate_api_key.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_protected_path_valid_session_token(self, app, mock_auth_service):
        """Test protected path with valid session token"""
        # Mock valid token validation
        mock_auth_service.validate_session_token.return_value = TokenValidationResult(
            is_valid=True,
            user_id="test_user_id",
            session_id="test_session_id",
            session=UserSession(
                session_id="test_session_id",
                user_id="test_user_id",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1),
                last_accessed=datetime.utcnow(),
                status=SessionStatus.ACTIVE
            )
        )
        
        app.add_middleware(AuthenticationMiddleware, auth_service=mock_auth_service)
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/conversations",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "protected"
        assert data["user_id"] == "test_user_id"
        
        # Auth service should be called
        mock_auth_service.validate_session_token.assert_called_once_with("valid_token")
    
    @pytest.mark.asyncio
    async def test_protected_path_valid_api_key(self, app, mock_auth_service):
        """Test protected path with valid API key"""
        # Mock valid API key validation
        mock_auth_service.validate_api_key.return_value = TokenValidationResult(
            is_valid=True,
            user_id="test_user_id",
            session_id="test_key_id"
        )
        
        app.add_middleware(AuthenticationMiddleware, auth_service=mock_auth_service)
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/conversations",
            headers={"X-API-Key": "valid_api_key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "protected"
        assert data["user_id"] == "test_user_id"
        
        # Auth service should be called
        mock_auth_service.validate_api_key.assert_called_once_with("valid_api_key")
    
    @pytest.mark.asyncio
    async def test_protected_path_invalid_token(self, app, mock_auth_service):
        """Test protected path with invalid token"""
        # Mock invalid token validation
        mock_auth_service.validate_session_token.return_value = TokenValidationResult(
            is_valid=False,
            error_message="Invalid token"
        )
        
        app.add_middleware(AuthenticationMiddleware, auth_service=mock_auth_service)
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/conversations",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Authentication required"
        assert "Invalid token" in data["message"]
    
    @pytest.mark.asyncio
    async def test_protected_path_no_auth_header(self, app, mock_auth_service):
        """Test protected path without authentication header"""
        app.add_middleware(AuthenticationMiddleware, auth_service=mock_auth_service)
        
        client = TestClient(app)
        response = client.get("/api/v1/conversations")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Authentication required"
        assert "No valid authentication provided" in data["message"]
    
    @pytest.mark.asyncio
    async def test_options_request_no_auth(self, app, mock_auth_service):
        """Test that OPTIONS requests don't require authentication"""
        app.add_middleware(AuthenticationMiddleware, auth_service=mock_auth_service)
        
        client = TestClient(app)
        response = client.options("/api/v1/conversations")
        
        # Should not require authentication for CORS preflight
        assert response.status_code in [200, 405]  # 405 if OPTIONS not implemented
        
        # Auth service should not be called
        mock_auth_service.validate_session_token.assert_not_called()
        mock_auth_service.validate_api_key.assert_not_called()


class TestInputSanitizationMiddleware:
    """Test cases for InputSanitizationMiddleware"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()
        
        @app.post("/api/test")
        async def test_endpoint(request: Request):
            body = await request.body()
            return {"received": len(body)}
        
        return app
    
    def test_content_length_limit(self, app):
        """Test content length limit enforcement"""
        middleware = InputSanitizationMiddleware(app, max_content_length=100)
        app.add_middleware(InputSanitizationMiddleware, max_content_length=100)
        
        client = TestClient(app)
        
        # Test request within limit
        small_data = {"message": "small"}
        response = client.post(
            "/api/test",
            json=small_data,
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        
        # Test request exceeding limit
        large_data = {"message": "x" * 200}  # Exceeds 100 byte limit
        response = client.post(
            "/api/test",
            json=large_data,
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 413
        data = response.json()
        assert data["error"] == "Request too large"
    
    def test_content_type_validation(self, app):
        """Test content type validation"""
        app.add_middleware(InputSanitizationMiddleware)
        
        client = TestClient(app)
        
        # Test valid content type
        response = client.post(
            "/api/test",
            json={"message": "test"},
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        
        # Test invalid content type
        response = client.post(
            "/api/test",
            data="invalid data",
            headers={"content-type": "text/plain"}
        )
        assert response.status_code == 415
        data = response.json()
        assert data["error"] == "Unsupported media type"
    
    def test_security_headers_added(self, app):
        """Test that security headers are added to responses"""
        app.add_middleware(InputSanitizationMiddleware)
        
        client = TestClient(app)
        response = client.post(
            "/api/test",
            json={"message": "test"}
        )
        
        # Check security headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_get_request_no_content_type_check(self, app):
        """Test that GET requests don't require content type validation"""
        app.add_middleware(InputSanitizationMiddleware)
        
        @app.get("/api/get-test")
        async def get_endpoint():
            return {"message": "get response"}
        
        client = TestClient(app)
        response = client.get("/api/get-test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "get response"}