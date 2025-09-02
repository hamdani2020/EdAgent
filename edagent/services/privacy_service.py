"""
Data privacy and user data management service
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from ..database.connection import db_manager
from ..database.models import (
    User, UserSkill, Conversation, LearningPath, Milestone,
    UserSession, APIKey, ContentRecommendation
)
from ..models.privacy import (
    DataExportRequest, DataExportResult, DataDeletionRequest,
    DataDeletionResult, AuditLogEntry, PrivacyAction
)


logger = logging.getLogger(__name__)


class PrivacyService:
    """Service for handling user data privacy controls"""
    
    async def export_user_data(self, user_id: str) -> DataExportResult:
        """Export all user data in a structured format"""
        try:
            async with db_manager.get_session() as db_session:
                # Verify user exists
                user_query = select(User).where(User.id == uuid.UUID(user_id))
                result = await db_session.execute(user_query)
                user = result.scalar_one_or_none()
                
                if not user:
                    return DataExportResult(
                        success=False,
                        error_message=f"User {user_id} not found"
                    )
                
                # Collect all user data
                export_data = await self._collect_user_data(db_session, uuid.UUID(user_id))
                
                # Log the export action
                await self._log_privacy_action(
                    db_session, user_id, PrivacyAction.DATA_EXPORT,
                    {"exported_data_types": list(export_data.keys())}
                )
                
                logger.info(f"Exported data for user {user_id}")
                
                return DataExportResult(
                    success=True,
                    user_id=user_id,
                    export_data=export_data,
                    exported_at=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to export data for user {user_id}: {str(e)}")
            return DataExportResult(
                success=False,
                error_message=f"Data export failed: {str(e)}"
            )
    
    async def delete_user_data(
        self, 
        user_id: str, 
        data_types: Optional[List[str]] = None,
        confirm_deletion: bool = False
    ) -> DataDeletionResult:
        """Delete user data based on specified data types"""
        if not confirm_deletion:
            return DataDeletionResult(
                success=False,
                error_message="Deletion must be explicitly confirmed"
            )
        
        try:
            async with db_manager.get_session() as db_session:
                # Verify user exists
                user_query = select(User).where(User.id == uuid.UUID(user_id))
                result = await db_session.execute(user_query)
                user = result.scalar_one_or_none()
                
                if not user:
                    return DataDeletionResult(
                        success=False,
                        error_message=f"User {user_id} not found"
                    )
                
                # If no specific data types, delete all user data
                if not data_types:
                    data_types = [
                        "conversations", "skills", "learning_paths", 
                        "sessions", "api_keys", "user_profile"
                    ]
                
                deleted_data = {}
                
                # Delete data by type
                for data_type in data_types:
                    count = await self._delete_data_by_type(
                        db_session, uuid.UUID(user_id), data_type
                    )
                    deleted_data[data_type] = count
                
                # Log the deletion action
                await self._log_privacy_action(
                    db_session, user_id, PrivacyAction.DATA_DELETION,
                    {"deleted_data_types": data_types, "deleted_counts": deleted_data}
                )
                
                await db_session.commit()
                
                logger.info(f"Deleted data for user {user_id}: {deleted_data}")
                
                return DataDeletionResult(
                    success=True,
                    user_id=user_id,
                    deleted_data_types=data_types,
                    deleted_counts=deleted_data,
                    deleted_at=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to delete data for user {user_id}: {str(e)}")
            return DataDeletionResult(
                success=False,
                error_message=f"Data deletion failed: {str(e)}"
            )
    
    async def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of what data exists for a user"""
        try:
            async with db_manager.get_session() as db_session:
                user_uuid = uuid.UUID(user_id)
                
                # Count data by type
                summary = {}
                
                # User profile
                user_query = select(User).where(User.id == user_uuid)
                result = await db_session.execute(user_query)
                user = result.scalar_one_or_none()
                summary["user_profile"] = 1 if user else 0
                
                # Skills
                skills_query = select(UserSkill).where(UserSkill.user_id == user_uuid)
                skills_result = await db_session.execute(skills_query)
                summary["skills"] = len(skills_result.scalars().all())
                
                # Conversations
                conv_query = select(Conversation).where(Conversation.user_id == user_uuid)
                conv_result = await db_session.execute(conv_query)
                summary["conversations"] = len(conv_result.scalars().all())
                
                # Learning paths
                lp_query = select(LearningPath).where(LearningPath.user_id == user_uuid)
                lp_result = await db_session.execute(lp_query)
                summary["learning_paths"] = len(lp_result.scalars().all())
                
                # Sessions
                session_query = select(UserSession).where(UserSession.user_id == user_uuid)
                session_result = await db_session.execute(session_query)
                summary["sessions"] = len(session_result.scalars().all())
                
                # API keys
                api_query = select(APIKey).where(APIKey.user_id == user_uuid)
                api_result = await db_session.execute(api_query)
                summary["api_keys"] = len(api_result.scalars().all())
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get data summary for user {user_id}: {str(e)}")
            return {}
    
    async def _collect_user_data(self, db_session: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Collect all user data for export"""
        export_data = {}
        
        # User profile
        user_query = select(User).where(User.id == user_id)
        result = await db_session.execute(user_query)
        user = result.scalar_one_or_none()
        
        if user:
            export_data["user_profile"] = {
                "id": str(user.id),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None,
                "preferences": user.preferences
            }
        
        # Skills
        skills_query = select(UserSkill).where(UserSkill.user_id == user_id)
        skills_result = await db_session.execute(skills_query)
        skills = skills_result.scalars().all()
        
        export_data["skills"] = [
            {
                "skill_name": skill.skill_name,
                "level": skill.level,
                "confidence_score": skill.confidence_score,
                "updated_at": skill.updated_at.isoformat() if skill.updated_at else None
            }
            for skill in skills
        ]
        
        # Conversations
        conv_query = select(Conversation).where(Conversation.user_id == user_id)
        conv_result = await db_session.execute(conv_query)
        conversations = conv_result.scalars().all()
        
        export_data["conversations"] = [
            {
                "id": str(conv.id),
                "message": conv.message,
                "response": conv.response,
                "timestamp": conv.timestamp.isoformat() if conv.timestamp else None,
                "message_type": conv.message_type,
                "context_data": conv.context_data
            }
            for conv in conversations
        ]
        
        # Learning paths with milestones
        lp_query = select(LearningPath).options(
            selectinload(LearningPath.milestones)
        ).where(LearningPath.user_id == user_id)
        lp_result = await db_session.execute(lp_query)
        learning_paths = lp_result.scalars().all()
        
        export_data["learning_paths"] = [
            {
                "id": str(lp.id),
                "goal": lp.goal,
                "created_at": lp.created_at.isoformat() if lp.created_at else None,
                "updated_at": lp.updated_at.isoformat() if lp.updated_at else None,
                "estimated_duration_days": lp.estimated_duration_days,
                "difficulty_level": lp.difficulty_level,
                "is_active": lp.is_active,
                "completion_percentage": lp.completion_percentage,
                "milestones": [
                    {
                        "id": str(milestone.id),
                        "title": milestone.title,
                        "description": milestone.description,
                        "order_index": milestone.order_index,
                        "is_completed": milestone.is_completed,
                        "completed_at": milestone.completed_at.isoformat() if milestone.completed_at else None,
                        "estimated_hours": milestone.estimated_hours,
                        "prerequisites": milestone.prerequisites
                    }
                    for milestone in lp.milestones
                ]
            }
            for lp in learning_paths
        ]
        
        # Sessions (excluding sensitive data like tokens)
        session_query = select(UserSession).where(UserSession.user_id == user_id)
        session_result = await db_session.execute(session_query)
        sessions = session_result.scalars().all()
        
        export_data["sessions"] = [
            {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "last_accessed": session.last_accessed.isoformat() if session.last_accessed else None,
                "status": session.status,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent
            }
            for session in sessions
        ]
        
        # API keys (excluding sensitive key hashes)
        api_query = select(APIKey).where(APIKey.user_id == user_id)
        api_result = await db_session.execute(api_query)
        api_keys = api_result.scalars().all()
        
        export_data["api_keys"] = [
            {
                "key_id": key.key_id,
                "name": key.name,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used": key.last_used.isoformat() if key.last_used else None,
                "is_active": key.is_active,
                "permissions": key.permissions,
                "usage_count": key.usage_count,
                "rate_limit_per_minute": key.rate_limit_per_minute
            }
            for key in api_keys
        ]
        
        return export_data
    
    async def _delete_data_by_type(
        self, 
        db_session: AsyncSession, 
        user_id: uuid.UUID, 
        data_type: str
    ) -> int:
        """Delete specific type of user data"""
        count = 0
        
        if data_type == "conversations":
            delete_query = delete(Conversation).where(Conversation.user_id == user_id)
            result = await db_session.execute(delete_query)
            count = result.rowcount
            
        elif data_type == "skills":
            delete_query = delete(UserSkill).where(UserSkill.user_id == user_id)
            result = await db_session.execute(delete_query)
            count = result.rowcount
            
        elif data_type == "learning_paths":
            # Delete milestones first (cascade should handle this, but being explicit)
            milestone_query = delete(Milestone).where(
                Milestone.learning_path_id.in_(
                    select(LearningPath.id).where(LearningPath.user_id == user_id)
                )
            )
            await db_session.execute(milestone_query)
            
            # Delete learning paths
            lp_query = delete(LearningPath).where(LearningPath.user_id == user_id)
            result = await db_session.execute(lp_query)
            count = result.rowcount
            
        elif data_type == "sessions":
            delete_query = delete(UserSession).where(UserSession.user_id == user_id)
            result = await db_session.execute(delete_query)
            count = result.rowcount
            
        elif data_type == "api_keys":
            delete_query = delete(APIKey).where(APIKey.user_id == user_id)
            result = await db_session.execute(delete_query)
            count = result.rowcount
            
        elif data_type == "user_profile":
            # This should be done last and only if all other data is deleted
            delete_query = delete(User).where(User.id == user_id)
            result = await db_session.execute(delete_query)
            count = result.rowcount
        
        return count
    
    async def _log_privacy_action(
        self,
        db_session: AsyncSession,
        user_id: str,
        action: PrivacyAction,
        metadata: Dict[str, Any]
    ) -> None:
        """Log privacy-related actions for audit purposes"""
        # For now, just log to application logs
        # In production, this could be stored in a separate audit table
        logger.info(
            f"Privacy action: {action.value} for user {user_id}",
            extra={
                "user_id": user_id,
                "action": action.value,
                "action_metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
        )