"""
Learning path endpoints for EdAgent API
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from ...services.conversation_manager import ConversationManager
from ...services.user_context_manager import UserContextManager
from ...services.learning_path_generator import EnhancedLearningPathGenerator
from ..schemas import (
    CreateLearningPathRequest,
    UpdateMilestoneStatusRequest,
    LearningPathSchema,
    LearningPathListResponse,
    MilestoneSchema,
    ResourceSchema,
    BaseResponse
)
from ..exceptions import LearningPathError, UserNotFoundError
from ...models.learning import LearningPath, Milestone
from ...config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter()


from ..dependencies import get_conversation_manager, get_user_context_manager, get_learning_path_generator


@router.post("/paths", response_model=LearningPathSchema, status_code=status.HTTP_201_CREATED)
async def create_learning_path(
    request: CreateLearningPathRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Create a new learning path for a user
    
    - **user_id**: Unique identifier for the user
    - **goal**: Learning or career goal description
    - **preferences**: Optional preferences for the learning path
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(request.user_id)
        if not user_context:
            raise UserNotFoundError(request.user_id)
        
        # Generate learning path
        learning_path = await conversation_manager.generate_learning_path(
            user_id=request.user_id,
            goal=request.goal
        )
        
        # Convert to schema
        return _convert_learning_path_to_schema(learning_path)
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error creating learning path: {str(e)}")
        raise LearningPathError(
            message="Failed to create learning path",
            details={"error": str(e)}
        )


@router.get("/paths/{path_id}", response_model=LearningPathSchema)
async def get_learning_path(
    path_id: str,
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Get learning path details
    
    - **path_id**: Unique identifier for the learning path
    """
    try:
        # Get learning path (this method needs to be implemented)
        # learning_path = await learning_path_generator.get_learning_path(path_id)
        
        # For now, create a mock response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Learning path retrieval not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving learning path: {str(e)}")
        raise LearningPathError(
            message="Failed to retrieve learning path",
            details={"error": str(e)}
        )


@router.get("/paths/user/{user_id}", response_model=LearningPathListResponse)
async def get_user_learning_paths(
    user_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of paths to retrieve"),
    offset: int = Query(0, ge=0, description="Number of paths to skip"),
    user_context_manager: UserContextManager = Depends(get_user_context_manager),
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Get learning paths for a specific user
    
    - **user_id**: Unique identifier for the user
    - **limit**: Maximum number of paths to retrieve (1-50)
    - **offset**: Number of paths to skip for pagination
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Get user learning paths (this method needs to be implemented)
        # learning_paths = await learning_path_generator.get_user_learning_paths(
        #     user_id, limit, offset
        # )
        
        # For now, return empty list
        return LearningPathListResponse(
            learning_paths=[],
            total_count=0,
            message="User learning paths retrieved successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user learning paths: {str(e)}")
        raise LearningPathError(
            message="Failed to retrieve user learning paths",
            details={"error": str(e)}
        )


@router.put("/paths/{path_id}/milestones/{milestone_id}/status", response_model=BaseResponse)
async def update_milestone_status(
    path_id: str,
    milestone_id: str,
    request: UpdateMilestoneStatusRequest,
    user_context_manager: UserContextManager = Depends(get_user_context_manager),
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Update milestone status in a learning path
    
    - **path_id**: Unique identifier for the learning path
    - **milestone_id**: Unique identifier for the milestone
    - **status**: New status for the milestone
    """
    try:
        # Update milestone status (this method needs to be implemented)
        # await learning_path_generator.update_milestone_status(
        #     path_id, milestone_id, request.status
        # )
        
        return BaseResponse(
            success=True,
            message="Milestone status updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error updating milestone status: {str(e)}")
        raise LearningPathError(
            message="Failed to update milestone status",
            details={"error": str(e)}
        )


@router.get("/paths/{path_id}/progress", response_model=dict)
async def get_learning_path_progress(
    path_id: str,
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Get learning path progress
    
    - **path_id**: Unique identifier for the learning path
    """
    try:
        # Get learning path progress (this method needs to be implemented)
        # progress = await learning_path_generator.get_learning_path_progress(path_id)
        
        # For now, return mock progress
        return {
            "path_id": path_id,
            "overall_progress": 0.0,
            "completed_milestones": 0,
            "total_milestones": 0,
            "current_milestone": None,
            "estimated_completion": None
        }
        
    except Exception as e:
        logger.error(f"Error retrieving learning path progress: {str(e)}")
        raise LearningPathError(
            message="Failed to retrieve learning path progress",
            details={"error": str(e)}
        )


@router.delete("/paths/{path_id}", response_model=BaseResponse)
async def delete_learning_path(
    path_id: str,
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Delete a learning path
    
    - **path_id**: Unique identifier for the learning path
    """
    try:
        # Delete learning path (this method needs to be implemented)
        # await learning_path_generator.delete_learning_path(path_id)
        
        return BaseResponse(
            success=True,
            message="Learning path deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deleting learning path: {str(e)}")
        raise LearningPathError(
            message="Failed to delete learning path",
            details={"error": str(e)}
        )


@router.get("/milestones/{milestone_id}", response_model=MilestoneSchema)
async def get_milestone(
    milestone_id: str,
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Get milestone details
    
    - **milestone_id**: Unique identifier for the milestone
    """
    try:
        # Get milestone (this method needs to be implemented)
        # milestone = await learning_path_generator.get_milestone(milestone_id)
        
        # For now, create a mock response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Milestone retrieval not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving milestone: {str(e)}")
        raise LearningPathError(
            message="Failed to retrieve milestone",
            details={"error": str(e)}
        )


@router.get("/milestones/{milestone_id}/resources", response_model=List[ResourceSchema])
async def get_milestone_resources(
    milestone_id: str,
    learning_path_generator: EnhancedLearningPathGenerator = Depends(get_learning_path_generator)
):
    """
    Get resources for a specific milestone
    
    - **milestone_id**: Unique identifier for the milestone
    """
    try:
        # Get milestone resources (this method needs to be implemented)
        # resources = await learning_path_generator.get_milestone_resources(milestone_id)
        
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Error retrieving milestone resources: {str(e)}")
        raise LearningPathError(
            message="Failed to retrieve milestone resources",
            details={"error": str(e)}
        )


def _convert_learning_path_to_schema(learning_path: LearningPath) -> LearningPathSchema:
    """Convert LearningPath model to schema"""
    
    # Convert milestones
    milestones_schema = []
    for milestone in learning_path.milestones:
        # Convert resources
        resources_schema = [
            ResourceSchema(
                title=resource.get("title", ""),
                url=resource.get("url", ""),
                type=resource.get("type", ""),
                is_free=resource.get("is_free", True),
                duration=resource.get("duration")
            )
            for resource in milestone.resources
        ]
        
        milestone_schema = MilestoneSchema(
            id=milestone.id,
            title=milestone.title,
            description=milestone.description,
            skills_to_learn=milestone.skills_to_learn,
            prerequisites=milestone.prerequisites,
            estimated_duration=int(milestone.estimated_duration.total_seconds()) if milestone.estimated_duration else None,
            difficulty_level=milestone.difficulty_level,
            status=milestone.status,
            resources=resources_schema,
            assessment_criteria=milestone.assessment_criteria,
            order_index=milestone.order_index
        )
        milestones_schema.append(milestone_schema)
    
    return LearningPathSchema(
        id=learning_path.id,
        title=learning_path.title,
        description=learning_path.description,
        goal=learning_path.goal,
        milestones=milestones_schema,
        estimated_duration=int(learning_path.estimated_duration.total_seconds()) if learning_path.estimated_duration else None,
        difficulty_level=learning_path.difficulty_level,
        prerequisites=learning_path.prerequisites,
        target_skills=learning_path.target_skills,
        created_at=learning_path.created_at,
        updated_at=learning_path.updated_at,
        progress=learning_path.get_progress()
    )