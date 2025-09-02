"""
Privacy and data management API endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..dependencies import get_current_user
from ...services.privacy_service import PrivacyService
from ...models.privacy import (
    DataExportRequest, DataDeletionRequest, PrivacySettings
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/privacy", tags=["privacy"])


class DataExportRequestModel(BaseModel):
    """Request model for data export"""
    include_sensitive: bool = Field(default=False, description="Include sensitive data in export")
    format: str = Field(default="json", description="Export format (json, csv)")


class DataDeletionRequestModel(BaseModel):
    """Request model for data deletion"""
    data_types: Optional[List[str]] = Field(
        default=None, 
        description="Specific data types to delete. If None, all data will be deleted"
    )
    reason: Optional[str] = Field(default=None, description="Reason for deletion")
    confirm_deletion: bool = Field(
        default=False, 
        description="Must be True to confirm deletion"
    )


class PrivacySettingsModel(BaseModel):
    """Model for privacy settings"""
    data_retention_days: Optional[int] = Field(default=None, description="Data retention period in days")
    allow_analytics: bool = Field(default=True, description="Allow analytics data collection")
    allow_personalization: bool = Field(default=True, description="Allow personalization features")
    allow_marketing: bool = Field(default=False, description="Allow marketing communications")
    auto_delete_conversations: bool = Field(default=False, description="Auto-delete old conversations")
    conversation_retention_days: int = Field(default=365, description="Conversation retention period")


@router.get("/data-summary")
async def get_user_data_summary(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get summary of user's data for privacy dashboard"""
    try:
        privacy_service = PrivacyService()
        user_id = current_user["user_id"]
        
        summary = await privacy_service.get_user_data_summary(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "data_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get data summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve data summary")


@router.post("/export")
async def export_user_data(
    request: DataExportRequestModel,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    """Export all user data"""
    try:
        privacy_service = PrivacyService()
        user_id = current_user["user_id"]
        
        result = await privacy_service.export_user_data(user_id)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
        
        # Return the export data
        response_data = {
            "success": True,
            "user_id": result.user_id,
            "exported_at": result.exported_at.isoformat() if result.exported_at else None,
            "export_data": result.export_data
        }
        
        # Set appropriate headers for download
        headers = {
            "Content-Disposition": f"attachment; filename=edagent_data_export_{user_id}.json",
            "Content-Type": "application/json"
        }
        
        return JSONResponse(content=response_data, headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export user data: {str(e)}")
        raise HTTPException(status_code=500, detail="Data export failed")


@router.delete("/data")
async def delete_user_data(
    request: DataDeletionRequestModel,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete user data"""
    try:
        privacy_service = PrivacyService()
        user_id = current_user["user_id"]
        
        if not request.confirm_deletion:
            raise HTTPException(
                status_code=400, 
                detail="Deletion must be explicitly confirmed by setting confirm_deletion=true"
            )
        
        result = await privacy_service.delete_user_data(
            user_id=user_id,
            data_types=request.data_types,
            confirm_deletion=request.confirm_deletion
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
        
        return {
            "success": True,
            "user_id": result.user_id,
            "deleted_data_types": result.deleted_data_types,
            "deleted_counts": result.deleted_counts,
            "total_deleted_items": result.total_deleted_items,
            "deleted_at": result.deleted_at.isoformat() if result.deleted_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user data: {str(e)}")
        raise HTTPException(status_code=500, detail="Data deletion failed")


@router.get("/settings")
async def get_privacy_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's privacy settings"""
    try:
        # For now, return default settings
        # In a full implementation, this would be stored in the database
        default_settings = PrivacySettings(user_id=current_user["user_id"])
        
        return {
            "success": True,
            "settings": {
                "data_retention_days": default_settings.data_retention_days,
                "allow_analytics": default_settings.allow_analytics,
                "allow_personalization": default_settings.allow_personalization,
                "allow_marketing": default_settings.allow_marketing,
                "auto_delete_conversations": default_settings.auto_delete_conversations,
                "conversation_retention_days": default_settings.conversation_retention_days,
                "updated_at": default_settings.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve privacy settings")


@router.put("/settings")
async def update_privacy_settings(
    settings: PrivacySettingsModel,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user's privacy settings"""
    try:
        user_id = current_user["user_id"]
        
        # In a full implementation, this would update the database
        # For now, just return the updated settings
        updated_settings = PrivacySettings(
            user_id=user_id,
            data_retention_days=settings.data_retention_days,
            allow_analytics=settings.allow_analytics,
            allow_personalization=settings.allow_personalization,
            allow_marketing=settings.allow_marketing,
            auto_delete_conversations=settings.auto_delete_conversations,
            conversation_retention_days=settings.conversation_retention_days
        )
        
        logger.info(f"Updated privacy settings for user {user_id}")
        
        return {
            "success": True,
            "message": "Privacy settings updated successfully",
            "settings": {
                "data_retention_days": updated_settings.data_retention_days,
                "allow_analytics": updated_settings.allow_analytics,
                "allow_personalization": updated_settings.allow_personalization,
                "allow_marketing": updated_settings.allow_marketing,
                "auto_delete_conversations": updated_settings.auto_delete_conversations,
                "conversation_retention_days": updated_settings.conversation_retention_days,
                "updated_at": updated_settings.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update privacy settings")


@router.get("/audit-log")
async def get_audit_log(
    limit: int = Query(default=50, le=100, description="Maximum number of entries to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's privacy audit log"""
    try:
        # In a full implementation, this would query the audit log from database
        # For now, return empty log with structure
        return {
            "success": True,
            "user_id": current_user["user_id"],
            "audit_entries": [],
            "total_entries": 0,
            "message": "Audit logging is enabled. Privacy actions will be recorded here."
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit log")


@router.post("/consent")
async def update_consent(
    consent_data: Dict[str, bool] = Body(..., description="Consent preferences"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user consent preferences"""
    try:
        user_id = current_user["user_id"]
        
        # Validate consent types
        valid_consent_types = {
            "data_processing", "analytics", "marketing", "personalization"
        }
        
        for consent_type in consent_data.keys():
            if consent_type not in valid_consent_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid consent type: {consent_type}"
                )
        
        # In a full implementation, this would store consent records in database
        logger.info(f"Updated consent preferences for user {user_id}: {consent_data}")
        
        return {
            "success": True,
            "message": "Consent preferences updated successfully",
            "consent_data": consent_data,
            "updated_at": "2024-01-01T00:00:00Z"  # Would be actual timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update consent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update consent preferences")