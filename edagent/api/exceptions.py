"""
Exception handlers for the EdAgent API
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback


logger = logging.getLogger(__name__)


class EdAgentAPIException(Exception):
    """Base exception for EdAgent API"""
    
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UserNotFoundError(EdAgentAPIException):
    """Exception raised when user is not found"""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"User with ID '{user_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"user_id": user_id}
        )


class ConversationError(EdAgentAPIException):
    """Exception raised for conversation-related errors"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AssessmentError(EdAgentAPIException):
    """Exception raised for assessment-related errors"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class LearningPathError(EdAgentAPIException):
    """Exception raised for learning path-related errors"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AIServiceError(EdAgentAPIException):
    """Exception raised for AI service-related errors"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the FastAPI app"""
    
    @app.exception_handler(EdAgentAPIException)
    async def edagent_exception_handler(request: Request, exc: EdAgentAPIException):
        """Handle EdAgent API exceptions"""
        logger.error(f"EdAgent API error: {exc.message}", extra={"details": exc.details})
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "type": exc.__class__.__name__,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "HTTPException"
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "message": "Request validation failed",
                    "type": "ValidationError",
                    "details": exc.errors()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(
            f"Unexpected error: {str(exc)}",
            extra={"traceback": traceback.format_exc()}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "An unexpected error occurred",
                    "type": "InternalServerError"
                }
            }
        )