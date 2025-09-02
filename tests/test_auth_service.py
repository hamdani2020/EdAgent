"""
Tests for authentication service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import uuid

from edagent.services.auth_service import AuthenticationService
from edagent.models.auth import (
    AuthenticationRequest, SessionStatus, TokenValidationResult
)
from edagent.database.models import User, UserSession as DBUserSession, APIKey as DBAPIKey


class TestAuthenticationService:
    """Test cases for AuthenticationService"""
    
    @pytest.fixture
    def auth_service(self):
        """Create authentication service instance"""
        return AuthenticationService()
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def sample_auth_request(self, sample_user_id):
        """Sample authentication request"""
        return AuthenticationRequest(
            user_id=sample_user_id,
            ip_address="192.168.1.1",
            user_agent="Test User Agent",
            session_duration_minutes=60
        )
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, auth_service, sample_auth_request):
        """Test successful session creation"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user exists
            mock_user = User(id=sample_auth_request.user_id)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Create session
            response = await auth_service.create_session(sample_auth_request)
            
            # Verify response
            assert response.user_id == sample_auth_request.user_id
            assert response.session_token is not None
            assert response.session_id is not None
            assert response.expires_at > datetime.utcnow()
            
            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_user_not_found(self, auth_service, sample_auth_request):
        """Test session creation with non-existent user"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user not found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # Test session creation fails
            with pytest.raises(ValueError, match="User .* not found"):
                await auth_service.create_session(sample_auth_request)
    
    @pytest.mark.asyncio
    async def test_validate_session_token_success(self, auth_service):
        """Test successful session token validation"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Create a valid token
            user_id = str(uuid.uuid4())
            session_id = "test_session_id"
            
            with patch.object(auth_service, '_verify_session_token') as mock_verify:
                mock_verify.return_value = TokenValidationResult(
                    is_valid=True,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Mock database session
                mock_db_session = DBUserSession(
                    session_id=session_id,
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                    last_accessed=datetime.utcnow(),
                    status="active"
                )
                mock_session.execute.return_value.scalar_one_or_none.return_value = mock_db_session
                
                # Validate token
                result = await auth_service.validate_session_token("valid_token")
                
                # Verify result
                assert result.is_valid is True
                assert result.user_id == user_id
                assert result.session_id == session_id
                assert result.session is not None
    
    @pytest.mark.asyncio
    async def test_validate_session_token_expired(self, auth_service):
        """Test validation of expired session token"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            user_id = str(uuid.uuid4())
            session_id = "expired_session_id"
            
            with patch.object(auth_service, '_verify_session_token') as mock_verify:
                mock_verify.return_value = TokenValidationResult(
                    is_valid=True,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Mock expired database session
                mock_db_session = DBUserSession(
                    session_id=session_id,
                    user_id=user_id,
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
                    last_accessed=datetime.utcnow() - timedelta(hours=1),
                    status="active"
                )
                mock_session.execute.return_value.scalar_one_or_none.return_value = mock_db_session
                
                # Validate token
                result = await auth_service.validate_session_token("expired_token")
                
                # Verify result
                assert result.is_valid is False
                assert "expired" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_session_token_invalid_jwt(self, auth_service):
        """Test validation of invalid JWT token"""
        with patch.object(auth_service, '_verify_session_token') as mock_verify:
            mock_verify.return_value = TokenValidationResult(
                is_valid=False,
                error_message="Invalid token"
            )
            
            # Validate invalid token
            result = await auth_service.validate_session_token("invalid_token")
            
            # Verify result
            assert result.is_valid is False
            assert result.error_message == "Invalid token"
    
    @pytest.mark.asyncio
    async def test_revoke_session_success(self, auth_service):
        """Test successful session revocation"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock successful update
            with patch.object(auth_service, '_update_session_status') as mock_update:
                mock_update.return_value = None
                
                # Revoke session
                result = await auth_service.revoke_session("test_session_id")
                
                # Verify result
                assert result is True
                mock_update.assert_called_once_with(
                    mock_session, "test_session_id", SessionStatus.REVOKED
                )
    
    @pytest.mark.asyncio
    async def test_create_api_key_success(self, auth_service, sample_user_id):
        """Test successful API key creation"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user exists
            mock_user = User(id=sample_user_id)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Create API key
            api_key, key_id = await auth_service.create_api_key(
                user_id=sample_user_id,
                name="Test API Key",
                permissions=["read", "write"],
                expires_in_days=30
            )
            
            # Verify response
            assert api_key.startswith("eda_")
            assert key_id is not None
            
            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, auth_service):
        """Test successful API key validation"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            user_id = str(uuid.uuid4())
            key_id = "test_key_id"
            
            # Mock database API key
            mock_db_key = DBAPIKey(
                key_id=key_id,
                user_id=user_id,
                key_hash="test_hash",
                name="Test Key",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                is_active=True,
                permissions=["read"],
                usage_count=0
            )
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_db_key
            
            # Mock hash generation
            with patch.object(auth_service, '_hash_api_key') as mock_hash:
                mock_hash.return_value = "test_hash"
                
                # Validate API key
                result = await auth_service.validate_api_key("test_api_key")
                
                # Verify result
                assert result.is_valid is True
                assert result.user_id == user_id
                assert result.session_id == key_id
    
    @pytest.mark.asyncio
    async def test_validate_api_key_not_found(self, auth_service):
        """Test API key validation with non-existent key"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock API key not found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # Mock hash generation
            with patch.object(auth_service, '_hash_api_key') as mock_hash:
                mock_hash.return_value = "test_hash"
                
                # Validate non-existent API key
                result = await auth_service.validate_api_key("invalid_api_key")
                
                # Verify result
                assert result.is_valid is False
                assert "Invalid API key" in result.error_message
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, auth_service):
        """Test cleanup of expired sessions"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock update and delete results
            mock_session.execute.return_value.rowcount = 5
            
            # Cleanup expired sessions
            result = await auth_service.cleanup_expired_sessions()
            
            # Verify result
            assert result == 10  # 5 updated + 5 deleted
            assert mock_session.execute.call_count == 2  # Update and delete queries
            assert mock_session.commit.call_count == 2
    
    def test_generate_api_key(self, auth_service):
        """Test API key generation"""
        api_key, key_hash = auth_service._generate_api_key()
        
        # Verify API key format
        assert api_key.startswith("eda_")
        assert len(api_key) > 10
        
        # Verify hash is different from key
        assert key_hash != api_key
        assert len(key_hash) == 64  # SHA256 hex digest length
    
    def test_hash_api_key(self, auth_service):
        """Test API key hashing"""
        api_key = "test_api_key"
        hash1 = auth_service._hash_api_key(api_key)
        hash2 = auth_service._hash_api_key(api_key)
        
        # Verify consistent hashing
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length
        
        # Verify different keys produce different hashes
        different_hash = auth_service._hash_api_key("different_key")
        assert hash1 != different_hash
    
    def test_generate_session_token(self, auth_service):
        """Test session token generation"""
        user_id = str(uuid.uuid4())
        session_id = "test_session"
        
        token = auth_service._generate_session_token(user_id, session_id)
        
        # Verify token is generated
        assert token is not None
        assert len(token) > 50  # JWT tokens are typically long
        
        # Verify token contains expected payload
        result = auth_service._verify_session_token(token)
        assert result.is_valid is True
        assert result.user_id == user_id
        assert result.session_id == session_id
    
    def test_verify_session_token_invalid(self, auth_service):
        """Test verification of invalid session token"""
        result = auth_service._verify_session_token("invalid_token")
        
        assert result.is_valid is False
        assert result.error_message is not None