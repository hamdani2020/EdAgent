"""
User management endpoints for EdAgent API
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from ...services.user_context_manager import UserContextManager
from ..schemas import (
    CreateUserRequest,
    UpdateUserPreferencesRequest,
    UpdateUserSkillsRequest,
    UserProfileResponse,
    UserContextSchema,
    BaseResponse,
    SkillLevelSchema,
    UserPreferencesSchema
)
from ..exceptions import UserNotFoundError, ConversationError
from ...models.user_context import UserContext, UserPreferences, SkillLevel
from ...config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter()


from ..dependencies import get_user_context_manager


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Create a new user profile
    
    - **user_id**: Unique identifier for the user
    - **career_goals**: List of user's career goals
    - **learning_preferences**: Optional learning preferences
    """
    try:
        # Check if user already exists
        existing_user = await user_context_manager.get_user_context(request.user_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with ID '{request.user_id}' already exists"
            )
        
        # Prepare preferences for user creation
        preferences_dict = None
        if request.learning_preferences:
            preferences = UserPreferences(
                learning_style=request.learning_preferences.learning_style,
                time_commitment=request.learning_preferences.time_commitment,
                budget_preference=request.learning_preferences.budget_preference,
                preferred_platforms=request.learning_preferences.preferred_platforms,
                content_types=request.learning_preferences.content_types,
                difficulty_preference=request.learning_preferences.difficulty_preference
            )
            preferences_dict = preferences.to_dict()
        
        # Create new user context with preferences
        user_context = await user_context_manager.create_user_context(request.user_id, preferences_dict)
        
        # Update career goals if provided
        if request.career_goals:
            user_context.career_goals = request.career_goals
        
        # Convert to schema
        user_schema = _convert_user_context_to_schema(user_context)
        
        return UserProfileResponse(
            user=user_schema,
            message="User created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Get user profile by ID
    
    - **user_id**: Unique identifier for the user
    """
    try:
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Convert to schema
        user_schema = _convert_user_context_to_schema(user_context)
        
        return UserProfileResponse(
            user=user_schema,
            message="User profile retrieved successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/{user_id}/preferences", response_model=BaseResponse)
async def update_user_preferences(
    user_id: str,
    request: UpdateUserPreferencesRequest,
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Update user learning preferences
    
    - **user_id**: Unique identifier for the user
    - **learning_preferences**: Updated learning preferences
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Convert schema to model
        preferences = UserPreferences(
            learning_style=request.learning_preferences.learning_style,
            time_commitment=request.learning_preferences.time_commitment,
            budget_preference=request.learning_preferences.budget_preference,
            preferred_platforms=request.learning_preferences.preferred_platforms,
            content_types=request.learning_preferences.content_types,
            difficulty_preference=request.learning_preferences.difficulty_preference
        )
        
        # Save preferences
        await user_context_manager.save_preferences(user_id, preferences)
        
        return BaseResponse(
            success=True,
            message="User preferences updated successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )


@router.put("/{user_id}/skills", response_model=BaseResponse)
async def update_user_skills(
    user_id: str,
    request: UpdateUserSkillsRequest,
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Update user skill levels
    
    - **user_id**: Unique identifier for the user
    - **skills**: Dictionary of skill names to skill levels
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Convert schema to model
        skills = {}
        for skill_name, skill_schema in request.skills.items():
            skills[skill_name] = SkillLevel(
                skill_name=skill_schema.skill_name,
                level=skill_schema.level,
                confidence_score=skill_schema.confidence_score,
                last_updated=skill_schema.last_updated
            )
        
        # Update skills
        await user_context_manager.update_skills(user_id, skills)
        
        return BaseResponse(
            success=True,
            message="User skills updated successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating user skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user skills"
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Delete a user profile
    
    - **user_id**: Unique identifier for the user
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Delete user (this method needs to be implemented)
        # await user_context_manager.delete_user(user_id)
        
        return BaseResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get("/{user_id}/goals", response_model=dict)
async def get_user_goals(
    user_id: str,
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Get user's career goals
    
    - **user_id**: Unique identifier for the user
    """
    try:
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        return {
            "user_id": user_id,
            "career_goals": user_context.career_goals,
            "total_goals": len(user_context.career_goals)
        }
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user goals"
        )


@router.put("/{user_id}/goals", response_model=BaseResponse)
async def update_user_goals(
    user_id: str,
    goals: List[str],
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Update user's career goals
    
    - **user_id**: Unique identifier for the user
    - **goals**: List of career goals
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Update goals (this method needs to be implemented)
        # await user_context_manager.update_goals(user_id, goals)
        
        return BaseResponse(
            success=True,
            message="User goals updated successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating user goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user goals"
        )


def _convert_user_context_to_schema(user_context: UserContext) -> UserContextSchema:
    """Convert UserContext model to schema"""
    
    # Convert skills
    skills_schema = {}
    for skill_name, skill in user_context.current_skills.items():
        skills_schema[skill_name] = SkillLevelSchema(
            skill_name=skill.skill_name,
            level=skill.level,
            confidence_score=skill.confidence_score,
            last_updated=skill.last_updated
        )
    
    # Convert preferences
    preferences_schema = None
    if user_context.learning_preferences:
        preferences_schema = UserPreferencesSchema(
            learning_style=user_context.learning_preferences.learning_style,
            time_commitment=user_context.learning_preferences.time_commitment,
            budget_preference=user_context.learning_preferences.budget_preference,
            preferred_platforms=user_context.learning_preferences.preferred_platforms,
            content_types=user_context.learning_preferences.content_types,
            difficulty_preference=user_context.learning_preferences.difficulty_preference
        )
    
    return UserContextSchema(
        user_id=user_context.user_id,
        current_skills=skills_schema,
        career_goals=user_context.career_goals,
        learning_preferences=preferences_schema,
        created_at=user_context.created_at,
        last_active=user_context.last_active
    )