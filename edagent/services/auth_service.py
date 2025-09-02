"""
Authentication and session management service
"""

import secrets
import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from ..database.connection import db_manager
from ..database.models import User, UserSession as DBUserSession, APIKey as DBAPIKey
from ..models.auth import (
    UserSession, APIKey, AuthenticationRequest, AuthenticationResponse,
    TokenValidationResult, SessionStatus
)
from ..config import get_settings


logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for handling authentication and session management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        
    def _generate_session_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT session token"""
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.settings.session_expire_minutes)
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.algorithm)
    
    def _verify_session_token(self, token: str) -> TokenValidationResult:
        """Verify and decode JWT session token"""
        try:
            payload = jwt.decode(token, self.settings.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            
            if not user_id or not session_id:
                return TokenValidationResult(
                    is_valid=False,
                    error_message="Invalid token payload"
                )
            
            return TokenValidationResult(
                is_valid=True,
                user_id=user_id,
                session_id=session_id
            )
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return TokenValidationResult(
                is_valid=False,
                error_message="Invalid or expired token"
            )
    
    def _generate_api_key(self) -> tuple[str, str]:
        """Generate API key and its hash"""
        # Generate a secure random API key
        api_key = f"eda_{secrets.token_urlsafe(32)}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return api_key, key_hash
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_session(self, request: AuthenticationRequest) -> AuthenticationResponse:
        """Create a new user session"""
        try:
            async with db_manager.get_session() as db_session:
                # Verify user exists
                user_query = select(User).where(User.id == uuid.UUID(request.user_id))
                result = await db_session.execute(user_query)
                user = result.scalar_one_or_none()
                
                if not user:
                    raise ValueError(f"User {request.user_id} not found")
                
                # Generate session ID and token
                session_id = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(minutes=request.session_duration_minutes)
                
                # Create session record
                db_user_session = DBUserSession(
                    session_id=session_id,
                    user_id=uuid.UUID(request.user_id),
                    expires_at=expires_at,
                    ip_address=request.ip_address,
                    user_agent=request.user_agent,
                    status="active"
                )
                
                db_session.add(db_user_session)
                await db_session.commit()
                
                # Generate JWT token
                token = self._generate_session_token(request.user_id, session_id)
                
                logger.info(f"Created session {session_id} for user {request.user_id}")
                
                return AuthenticationResponse(
                    session_token=token,
                    user_id=request.user_id,
                    expires_at=expires_at,
                    session_id=session_id
                )
                
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    async def validate_session_token(self, token: str) -> TokenValidationResult:
        """Validate session token and return session info"""
        # First verify the JWT token
        token_result = self._verify_session_token(token)
        if not token_result.is_valid:
            return token_result
        
        try:
            async with db_manager.get_session() as db_session:
                # Get session from database
                session_query = select(DBUserSession).where(
                    DBUserSession.session_id == token_result.session_id
                )
                result = await db_session.execute(session_query)
                db_user_session = result.scalar_one_or_none()
                
                if not db_user_session:
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Session not found"
                    )
                
                # Convert to domain model
                user_session = UserSession(
                    session_id=db_user_session.session_id,
                    user_id=str(db_user_session.user_id),
                    created_at=db_user_session.created_at,
                    expires_at=db_user_session.expires_at,
                    last_accessed=db_user_session.last_accessed,
                    status=SessionStatus(db_user_session.status),
                    ip_address=db_user_session.ip_address,
                    user_agent=db_user_session.user_agent,
                    session_metadata=db_user_session.session_metadata
                )
                
                # Check if session is valid
                if not user_session.is_valid():
                    # Update session status if expired
                    if user_session.is_expired():
                        await self._update_session_status(
                            db_session, db_user_session.session_id, SessionStatus.EXPIRED
                        )
                    
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Session expired or invalid"
                    )
                
                # Update last accessed time
                await self._update_last_accessed(db_session, db_user_session.session_id)
                
                return TokenValidationResult(
                    is_valid=True,
                    user_id=user_session.user_id,
                    session_id=user_session.session_id,
                    session=user_session
                )
                
        except Exception as e:
            logger.error(f"Failed to validate session: {str(e)}")
            return TokenValidationResult(
                is_valid=False,
                error_message="Session validation failed"
            )
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a user session"""
        try:
            async with db_manager.get_session() as db_session:
                await self._update_session_status(db_session, session_id, SessionStatus.REVOKED)
                logger.info(f"Revoked session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to revoke session {session_id}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from database"""
        try:
            async with db_manager.get_session() as db_session:
                # Update expired sessions
                current_time = datetime.utcnow()
                update_query = (
                    update(DBUserSession)
                    .where(
                        DBUserSession.expires_at <= current_time,
                        DBUserSession.status == "active"
                    )
                    .values(status="expired")
                )
                
                result = await db_session.execute(update_query)
                await db_session.commit()
                
                expired_count = result.rowcount
                logger.info(f"Marked {expired_count} sessions as expired")
                
                # Optionally delete old expired sessions (older than 30 days)
                cutoff_date = current_time - timedelta(days=30)
                delete_query = delete(DBUserSession).where(
                    DBUserSession.expires_at <= cutoff_date,
                    DBUserSession.status.in_(["expired", "revoked"])
                )
                
                delete_result = await db_session.execute(delete_query)
                await db_session.commit()
                
                deleted_count = delete_result.rowcount
                logger.info(f"Deleted {deleted_count} old sessions")
                
                return expired_count + deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0
    
    async def create_api_key(
        self, 
        user_id: str, 
        name: str, 
        permissions: List[str] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_per_minute: Optional[int] = None
    ) -> tuple[str, str]:
        """Create a new API key for a user"""
        try:
            async with db_manager.get_session() as db_session:
                # Verify user exists
                user_query = select(User).where(User.id == uuid.UUID(user_id))
                result = await db_session.execute(user_query)
                user = result.scalar_one_or_none()
                
                if not user:
                    raise ValueError(f"User {user_id} not found")
                
                # Generate API key
                api_key, key_hash = self._generate_api_key()
                key_id = secrets.token_urlsafe(16)
                
                # Calculate expiration
                expires_at = None
                if expires_in_days:
                    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
                
                # Create API key record
                db_api_key = DBAPIKey(
                    key_id=key_id,
                    user_id=uuid.UUID(user_id),
                    key_hash=key_hash,
                    name=name,
                    expires_at=expires_at,
                    permissions=permissions or [],
                    rate_limit_per_minute=rate_limit_per_minute
                )
                
                db_session.add(db_api_key)
                await db_session.commit()
                
                logger.info(f"Created API key {key_id} for user {user_id}")
                
                return api_key, key_id
                
        except Exception as e:
            logger.error(f"Failed to create API key: {str(e)}")
            raise
    
    async def validate_api_key(self, api_key: str) -> TokenValidationResult:
        """Validate API key and return user info"""
        try:
            key_hash = self._hash_api_key(api_key)
            
            async with db_manager.get_session() as db_session:
                # Get API key from database
                key_query = select(DBAPIKey).where(DBAPIKey.key_hash == key_hash)
                result = await db_session.execute(key_query)
                db_key = result.scalar_one_or_none()
                
                if not db_key:
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="Invalid API key"
                    )
                
                # Convert to domain model
                api_key_obj = APIKey(
                    key_id=db_key.key_id,
                    user_id=str(db_key.user_id),
                    key_hash=db_key.key_hash,
                    name=db_key.name,
                    created_at=db_key.created_at,
                    expires_at=db_key.expires_at,
                    last_used=db_key.last_used,
                    is_active=db_key.is_active,
                    permissions=db_key.permissions,
                    usage_count=db_key.usage_count,
                    rate_limit_per_minute=db_key.rate_limit_per_minute
                )
                
                # Check if API key is valid
                if not api_key_obj.is_valid():
                    return TokenValidationResult(
                        is_valid=False,
                        error_message="API key expired or inactive"
                    )
                
                # Update usage statistics
                await self._update_api_key_usage(db_session, db_key.key_id)
                
                return TokenValidationResult(
                    is_valid=True,
                    user_id=api_key_obj.user_id,
                    session_id=api_key_obj.key_id  # Use key_id as session identifier
                )
                
        except Exception as e:
            logger.error(f"Failed to validate API key: {str(e)}")
            return TokenValidationResult(
                is_valid=False,
                error_message="API key validation failed"
            )
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        try:
            async with db_manager.get_session() as db_session:
                update_query = (
                    update(DBAPIKey)
                    .where(DBAPIKey.key_id == key_id)
                    .values(is_active=False)
                )
                
                result = await db_session.execute(update_query)
                await db_session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Revoked API key {key_id}")
                    return True
                else:
                    logger.warning(f"API key {key_id} not found")
                    return False
                
        except Exception as e:
            logger.error(f"Failed to revoke API key {key_id}: {str(e)}")
            return False
    
    async def _update_session_status(
        self, 
        db_session: AsyncSession, 
        session_id: str, 
        status: SessionStatus
    ) -> None:
        """Update session status in database"""
        update_query = (
            update(DBUserSession)
            .where(DBUserSession.session_id == session_id)
            .values(status=status.value)
        )
        await db_session.execute(update_query)
        await db_session.commit()
    
    async def _update_last_accessed(self, db_session: AsyncSession, session_id: str) -> None:
        """Update session last accessed time"""
        update_query = (
            update(DBUserSession)
            .where(DBUserSession.session_id == session_id)
            .values(last_accessed=datetime.utcnow())
        )
        await db_session.execute(update_query)
        await db_session.commit()
    
    async def _update_api_key_usage(self, db_session: AsyncSession, key_id: str) -> None:
        """Update API key usage statistics"""
        update_query = (
            update(DBAPIKey)
            .where(DBAPIKey.key_id == key_id)
            .values(
                usage_count=DBAPIKey.usage_count + 1,
                last_used=datetime.utcnow()
            )
        )
        await db_session.execute(update_query)
        await db_session.commit()