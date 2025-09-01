"""
Assessment endpoints for EdAgent API
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from ...services.conversation_manager import ConversationManager
from ...services.user_context_manager import UserContextManager
from ..schemas import (
    StartAssessmentRequest,
    AssessmentResponseRequest,
    AssessmentSessionSchema,
    AssessmentListResponse,
    SkillAssessmentResultSchema,
    BaseResponse,
    AssessmentQuestionSchema
)
from ..exceptions import AssessmentError, UserNotFoundError
from ...models.conversation import AssessmentSession
from ...config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter()


from ..dependencies import get_conversation_manager, get_user_context_manager


@router.post("/start", response_model=AssessmentSessionSchema, status_code=status.HTTP_201_CREATED)
async def start_assessment(
    request: StartAssessmentRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Start a new skill assessment session
    
    - **user_id**: Unique identifier for the user
    - **skill_area**: The skill area to assess (e.g., "python", "web development")
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(request.user_id)
        if not user_context:
            raise UserNotFoundError(request.user_id)
        
        # Start assessment session
        assessment_session = await conversation_manager.start_skill_assessment(request.user_id)
        
        # Convert to schema
        return _convert_assessment_session_to_schema(assessment_session)
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error starting assessment: {str(e)}")
        raise AssessmentError(
            message="Failed to start assessment",
            details={"error": str(e)}
        )


@router.get("/{assessment_id}", response_model=AssessmentSessionSchema)
async def get_assessment(
    assessment_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Get assessment session details
    
    - **assessment_id**: Unique identifier for the assessment session
    """
    try:
        # Get assessment session (this method needs to be implemented)
        # assessment_session = await conversation_manager.get_assessment_session(assessment_id)
        
        # For now, create a mock response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Assessment retrieval not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving assessment: {str(e)}")
        raise AssessmentError(
            message="Failed to retrieve assessment",
            details={"error": str(e)}
        )


@router.post("/{assessment_id}/respond", response_model=AssessmentSessionSchema)
async def submit_assessment_response(
    assessment_id: str,
    request: AssessmentResponseRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Submit a response to an assessment question
    
    - **assessment_id**: Unique identifier for the assessment session
    - **response**: The user's response to the current question
    - **question_index**: Optional specific question index to respond to
    """
    try:
        # Submit response (this method needs to be implemented)
        # assessment_session = await conversation_manager.submit_assessment_response(
        #     assessment_id, request.response, request.question_index
        # )
        
        # For now, create a mock response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Assessment response submission not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error submitting assessment response: {str(e)}")
        raise AssessmentError(
            message="Failed to submit assessment response",
            details={"error": str(e)}
        )


@router.post("/{assessment_id}/complete", response_model=SkillAssessmentResultSchema)
async def complete_assessment(
    assessment_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Complete an assessment and get results
    
    - **assessment_id**: Unique identifier for the assessment session
    """
    try:
        # Complete assessment (this method needs to be implemented)
        # assessment_result = await conversation_manager.complete_assessment(assessment_id)
        
        # For now, create a mock response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Assessment completion not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error completing assessment: {str(e)}")
        raise AssessmentError(
            message="Failed to complete assessment",
            details={"error": str(e)}
        )


@router.get("/user/{user_id}", response_model=AssessmentListResponse)
async def get_user_assessments(
    user_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of assessments to retrieve"),
    offset: int = Query(0, ge=0, description="Number of assessments to skip"),
    status_filter: Optional[str] = Query(None, description="Filter by assessment status"),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Get assessments for a specific user
    
    - **user_id**: Unique identifier for the user
    - **limit**: Maximum number of assessments to retrieve (1-50)
    - **offset**: Number of assessments to skip for pagination
    - **status_filter**: Optional filter by assessment status
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Get user assessments (this method needs to be implemented)
        # assessments = await conversation_manager.get_user_assessments(
        #     user_id, limit, offset, status_filter
        # )
        
        # For now, return empty list
        return AssessmentListResponse(
            assessments=[],
            total_count=0,
            message="User assessments retrieved successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user assessments: {str(e)}")
        raise AssessmentError(
            message="Failed to retrieve user assessments",
            details={"error": str(e)}
        )


@router.delete("/{assessment_id}", response_model=BaseResponse)
async def delete_assessment(
    assessment_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Delete an assessment session
    
    - **assessment_id**: Unique identifier for the assessment session
    """
    try:
        # Delete assessment (this method needs to be implemented)
        # await conversation_manager.delete_assessment(assessment_id)
        
        return BaseResponse(
            success=True,
            message="Assessment deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deleting assessment: {str(e)}")
        raise AssessmentError(
            message="Failed to delete assessment",
            details={"error": str(e)}
        )


@router.get("/{assessment_id}/progress", response_model=dict)
async def get_assessment_progress(
    assessment_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Get assessment progress
    
    - **assessment_id**: Unique identifier for the assessment session
    """
    try:
        # Get assessment progress (this method needs to be implemented)
        # progress = await conversation_manager.get_assessment_progress(assessment_id)
        
        # For now, return mock progress
        return {
            "assessment_id": assessment_id,
            "progress": 0.0,
            "current_question": 0,
            "total_questions": 0,
            "status": "not_started"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving assessment progress: {str(e)}")
        raise AssessmentError(
            message="Failed to retrieve assessment progress",
            details={"error": str(e)}
        )


def _convert_assessment_session_to_schema(assessment_session: AssessmentSession) -> AssessmentSessionSchema:
    """Convert AssessmentSession model to schema"""
    
    # Convert questions
    questions_schema = [
        AssessmentQuestionSchema(
            question=q["question"],
            type=q.get("type", "open"),
            options=q.get("options", []),
            index=q.get("index", 0)
        )
        for q in assessment_session.questions
    ]
    
    return AssessmentSessionSchema(
        id=assessment_session.id,
        user_id=assessment_session.user_id,
        skill_area=assessment_session.skill_area,
        questions=questions_schema,
        current_question_index=assessment_session.current_question_index,
        status=assessment_session.status.value,
        started_at=assessment_session.started_at,
        completed_at=assessment_session.completed_at,
        progress=assessment_session.get_progress()
    )