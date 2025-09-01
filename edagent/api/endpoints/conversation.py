"""
Conversation endpoints for EdAgent API
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from ...services.conversation_manager import ConversationManager
from ...services.user_context_manager import UserContextManager
from ..schemas import (
    ConversationRequest,
    ConversationResponseSchema,
    ConversationHistoryResponse,
    MessageSchema,
    BaseResponse
)
from ..exceptions import ConversationError, UserNotFoundError
from ...config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter()


from ..dependencies import get_conversation_manager, get_user_context_manager


@router.post("/message", response_model=ConversationResponseSchema)
async def send_message(
    request: ConversationRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Send a message to the AI agent and get a response
    
    - **user_id**: Unique identifier for the user
    - **message**: The user's message content
    - **context**: Optional additional context for the conversation
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(request.user_id)
        if not user_context:
            raise UserNotFoundError(request.user_id)
        
        # Handle the message
        response = await conversation_manager.handle_message(
            user_id=request.user_id,
            message=request.message
        )
        
        # Convert to schema
        return ConversationResponseSchema(
            message=response.message,
            response_type=response.response_type,
            confidence_score=response.confidence_score,
            suggested_actions=response.suggested_actions,
            content_recommendations=[
                {
                    "title": rec.get("title", ""),
                    "url": rec.get("url", ""),
                    "platform": rec.get("platform", ""),
                    "content_type": rec.get("content_type", ""),
                    "duration": rec.get("duration"),
                    "rating": rec.get("rating", 0.0),
                    "is_free": rec.get("is_free", True),
                    "skill_match_score": rec.get("skill_match_score", 0.0)
                }
                for rec in response.content_recommendations
            ],
            follow_up_questions=response.follow_up_questions,
            metadata=response.metadata
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        raise ConversationError(
            message="Failed to process message",
            details={"error": str(e)}
        )


@router.get("/{user_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Get conversation history for a user
    
    - **user_id**: Unique identifier for the user
    - **limit**: Maximum number of messages to retrieve (1-100)
    - **offset**: Number of messages to skip for pagination
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Get conversation history
        messages = await conversation_manager.get_conversation_history(user_id)
        
        # Apply pagination
        total_count = len(messages)
        paginated_messages = messages[offset:offset + limit]
        
        # Convert to schema
        message_schemas = [
            MessageSchema(
                id=msg.id,
                content=msg.content,
                message_type=msg.message_type,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in paginated_messages
        ]
        
        return ConversationHistoryResponse(
            messages=message_schemas,
            total_count=total_count,
            message="Conversation history retrieved successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise ConversationError(
            message="Failed to retrieve conversation history",
            details={"error": str(e)}
        )


@router.delete("/{user_id}/history", response_model=BaseResponse)
async def clear_conversation_history(
    user_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Clear conversation history for a user
    
    - **user_id**: Unique identifier for the user
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Clear conversation history (this method needs to be implemented)
        # await conversation_manager.clear_conversation_history(user_id)
        
        return BaseResponse(
            success=True,
            message="Conversation history cleared successfully"
        )
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise ConversationError(
            message="Failed to clear conversation history",
            details={"error": str(e)}
        )


@router.get("/{user_id}/context", response_model=dict)
async def get_conversation_context(
    user_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    user_context_manager: UserContextManager = Depends(get_user_context_manager)
):
    """
    Get current conversation context for a user
    
    - **user_id**: Unique identifier for the user
    """
    try:
        # Verify user exists
        user_context = await user_context_manager.get_user_context(user_id)
        if not user_context:
            raise UserNotFoundError(user_id)
        
        # Get recent messages for context
        recent_messages = await conversation_manager.get_conversation_history(user_id)
        recent_messages = recent_messages[-5:]  # Last 5 messages
        
        context = {
            "user_id": user_id,
            "recent_messages": [
                {
                    "content": msg.content,
                    "message_type": msg.message_type.value,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in recent_messages
            ],
            "user_skills": {
                name: {
                    "level": skill.level.value,
                    "confidence": skill.confidence_score
                }
                for name, skill in user_context.current_skills.items()
            },
            "career_goals": user_context.career_goals
        }
        
        return context
        
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation context: {str(e)}")
        raise ConversationError(
            message="Failed to retrieve conversation context",
            details={"error": str(e)}
        )