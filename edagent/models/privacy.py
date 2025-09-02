"""
Privacy and data management models for EdAgent
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class PrivacyAction(Enum):
    """Privacy action types for audit logging"""
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    DATA_ACCESS = "data_access"
    CONSENT_UPDATE = "consent_update"


@dataclass
class DataExportRequest:
    """Request for user data export"""
    user_id: str
    requested_at: datetime
    include_sensitive: bool = False
    format: str = "json"  # json, csv, xml
    
    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.utcnow()


@dataclass
class DataExportResult:
    """Result of user data export"""
    success: bool
    user_id: Optional[str] = None
    export_data: Optional[Dict[str, Any]] = None
    exported_at: Optional[datetime] = None
    error_message: Optional[str] = None
    export_size_bytes: Optional[int] = None
    
    def to_json_string(self) -> str:
        """Convert export data to JSON string"""
        import json
        if self.export_data:
            return json.dumps(self.export_data, indent=2, default=str)
        return "{}"


@dataclass
class DataDeletionRequest:
    """Request for user data deletion"""
    user_id: str
    requested_at: datetime
    data_types: Optional[List[str]] = None  # None means delete all
    reason: Optional[str] = None
    confirm_deletion: bool = False
    
    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.utcnow()


@dataclass
class DataDeletionResult:
    """Result of user data deletion"""
    success: bool
    user_id: Optional[str] = None
    deleted_data_types: Optional[List[str]] = None
    deleted_counts: Optional[Dict[str, int]] = None
    deleted_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def total_deleted_items(self) -> int:
        """Get total number of deleted items"""
        if self.deleted_counts:
            return sum(self.deleted_counts.values())
        return 0


@dataclass
class AuditLogEntry:
    """Audit log entry for privacy actions"""
    id: str
    user_id: str
    action: PrivacyAction
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class UserDataSummary:
    """Summary of user data for privacy dashboard"""
    user_id: str
    data_types: Dict[str, int]  # data_type -> count
    total_conversations: int
    total_skills: int
    total_learning_paths: int
    total_sessions: int
    total_api_keys: int
    account_created: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    data_retention_days: Optional[int] = None
    
    @property
    def total_data_points(self) -> int:
        """Get total number of data points"""
        return sum(self.data_types.values())


@dataclass
class PrivacySettings:
    """User privacy settings and preferences"""
    user_id: str
    data_retention_days: Optional[int] = None  # None means indefinite
    allow_analytics: bool = True
    allow_personalization: bool = True
    allow_marketing: bool = False
    auto_delete_conversations: bool = False
    conversation_retention_days: int = 365
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ConsentRecord:
    """Record of user consent for data processing"""
    user_id: str
    consent_type: str  # "data_processing", "analytics", "marketing", etc.
    granted: bool
    granted_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    consent_version: str = "1.0"
    
    def __post_init__(self):
        if self.granted_at is None:
            self.granted_at = datetime.utcnow()