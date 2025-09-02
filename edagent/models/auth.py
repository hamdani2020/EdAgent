"""
Authentication and session models for EdAgent
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class UserSession:
    """User session data model"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    status: SessionStatus
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_metadata: Optional[Dict[str, Any]] = None
    
    def is_valid(self) -> bool:
        """Check if session is valid and not expired"""
        return (
            self.status == SessionStatus.ACTIVE and
            self.expires_at > datetime.utcnow()
        )
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return self.expires_at <= datetime.utcnow()
    
    def refresh(self, expire_minutes: int = 1440) -> None:
        """Refresh session expiration time"""
        self.expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        self.last_accessed = datetime.utcnow()


@dataclass
class APIKey:
    """API key data model"""
    key_id: str
    user_id: str
    key_hash: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool
    permissions: List[str]
    usage_count: int = 0
    rate_limit_per_minute: Optional[int] = None
    
    def is_valid(self) -> bool:
        """Check if API key is valid and not expired"""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at <= datetime.utcnow():
            return False
        
        return True
    
    def increment_usage(self) -> None:
        """Increment usage counter and update last used timestamp"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()


@dataclass
class AuthenticationRequest:
    """Authentication request data model"""
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_duration_minutes: int = 1440  # 24 hours default


@dataclass
class AuthenticationResponse:
    """Authentication response data model"""
    session_token: str
    user_id: str
    expires_at: datetime
    session_id: str


@dataclass
class TokenValidationResult:
    """Token validation result"""
    is_valid: bool
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    session: Optional[UserSession] = None