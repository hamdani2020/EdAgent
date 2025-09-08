"""
Enhanced EdAgent API Client
Provides robust API communication with comprehensive error handling, retry logic, and response processing.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json

import httpx
import streamlit as st
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIErrorType(Enum):
    """API error types for categorized error handling"""
    AUTHENTICATION_ERROR = "auth_error"
    AUTHORIZATION_ERROR = "authz_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class APIError(Exception):
    """Enhanced API error with detailed information"""
    error_type: APIErrorType
    message: str
    status_code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None
    is_retryable: bool = False
    
    def __str__(self) -> str:
        return f"{self.error_type.value}: {self.message}"


@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    success: bool
    data: Any
    error: Optional[APIError] = None
    status_code: int = 200
    headers: Dict[str, str] = None
    response_time: float = 0.0
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class AuthResult:
    """Authentication result data"""
    success: bool
    access_token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ConversationResponse:
    """Conversation response data"""
    message: str
    response_type: str = "text"
    confidence_score: float = 1.0
    suggested_actions: List[str] = None
    content_recommendations: List[Dict[str, Any]] = None
    follow_up_questions: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []
        if self.content_recommendations is None:
            self.content_recommendations = []
        if self.follow_up_questions is None:
            self.follow_up_questions = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AssessmentSession:
    """Assessment session data"""
    id: str
    user_id: str
    skill_area: str
    questions: List[Dict[str, Any]] = None
    current_question_index: int = 0
    status: str = "active"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    
    def __post_init__(self):
        if self.questions is None:
            self.questions = []
        if self.started_at is None:
            self.started_at = datetime.now()


@dataclass
class LearningPath:
    """Learning path data"""
    id: str
    title: str
    description: str = ""
    goal: str = ""
    milestones: List[Dict[str, Any]] = None
    estimated_duration: Optional[int] = None
    difficulty_level: str = "intermediate"
    prerequisites: List[str] = None
    target_skills: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    progress: float = 0.0
    
    def __post_init__(self):
        if self.milestones is None:
            self.milestones = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.target_skills is None:
            self.target_skills = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class SessionManager:
    """Manages user session state and authentication"""
    
    def __init__(self):
        self.session_key_prefix = "edagent_"
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return (
            st.session_state.get(f"{self.session_key_prefix}user_id") is not None and
            st.session_state.get(f"{self.session_key_prefix}access_token") is not None and
            not self.is_token_expired()
        )
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return st.session_state.get(f"{self.session_key_prefix}user_id")
    
    def get_auth_token(self) -> Optional[str]:
        """Get current authentication token"""
        return st.session_state.get(f"{self.session_key_prefix}access_token")
    
    def get_user_email(self) -> Optional[str]:
        """Get current user email"""
        return st.session_state.get(f"{self.session_key_prefix}user_email")
    
    def get_user_name(self) -> Optional[str]:
        """Get current user name"""
        return st.session_state.get(f"{self.session_key_prefix}user_name")
    
    def set_auth_data(self, auth_result: AuthResult) -> None:
        """Store authentication data in session"""
        if auth_result.success:
            st.session_state[f"{self.session_key_prefix}access_token"] = auth_result.access_token
            st.session_state[f"{self.session_key_prefix}user_id"] = auth_result.user_id
            st.session_state[f"{self.session_key_prefix}user_email"] = auth_result.email
            st.session_state[f"{self.session_key_prefix}user_name"] = auth_result.name
            st.session_state[f"{self.session_key_prefix}token_expires_at"] = auth_result.expires_at
            logger.info(f"Authentication data stored for user {auth_result.user_id}")
    
    def clear_session(self) -> None:
        """Clear all session data"""
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith(self.session_key_prefix)]
        for key in keys_to_remove:
            del st.session_state[key]
        logger.info("Session data cleared")
    
    def is_token_expired(self) -> bool:
        """Check if authentication token is expired"""
        expires_at = st.session_state.get(f"{self.session_key_prefix}token_expires_at")
        if not expires_at:
            return True
        return datetime.now() >= expires_at
    
    def get_token_expiry_time(self) -> Optional[datetime]:
        """Get token expiry time"""
        return st.session_state.get(f"{self.session_key_prefix}token_expires_at")


class EnhancedEdAgentAPI:
    """
    Enhanced API client with comprehensive error handling, retry logic, and response processing
    """
    
    def __init__(self, base_url: str, session_manager: SessionManager = None):
        self.base_url = base_url.rstrip('/')
        self.session_manager = session_manager or SessionManager()
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum time between requests
        
        # Circuit breaker state
        self.failure_count = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.circuit_breaker_last_failure = 0
        
        logger.info(f"Enhanced EdAgent API client initialized with base URL: {base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EdAgent-Streamlit/1.0",
            "Accept": "application/json"
        }
        
        if self.session_manager.is_authenticated():
            token = self.session_manager.get_auth_token()
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def _categorize_error(self, response: httpx.Response, exception: Exception = None) -> APIErrorType:
        """Categorize error based on response or exception"""
        if exception:
            if isinstance(exception, httpx.TimeoutException):
                return APIErrorType.TIMEOUT_ERROR
            elif isinstance(exception, (httpx.NetworkError, httpx.ConnectError)):
                return APIErrorType.NETWORK_ERROR
            else:
                return APIErrorType.UNKNOWN_ERROR
        
        if response.status_code == 401:
            return APIErrorType.AUTHENTICATION_ERROR
        elif response.status_code == 403:
            return APIErrorType.AUTHORIZATION_ERROR
        elif response.status_code == 422:
            return APIErrorType.VALIDATION_ERROR
        elif response.status_code == 429:
            return APIErrorType.RATE_LIMIT_ERROR
        elif 500 <= response.status_code < 600:
            return APIErrorType.SERVER_ERROR
        else:
            return APIErrorType.UNKNOWN_ERROR
    
    def _create_api_error(self, response: httpx.Response = None, exception: Exception = None) -> APIError:
        """Create APIError from response or exception"""
        if exception:
            error_type = self._categorize_error(None, exception)
            return APIError(
                error_type=error_type,
                message=str(exception),
                is_retryable=error_type in [APIErrorType.NETWORK_ERROR, APIErrorType.TIMEOUT_ERROR]
            )
        
        error_type = self._categorize_error(response)
        
        # Extract error details from response
        try:
            error_data = response.json()
            message = error_data.get("error", {}).get("message", response.text)
            details = error_data.get("error", {}).get("details")
        except:
            message = response.text or f"HTTP {response.status_code}"
            details = None
        
        # Check for retry-after header
        retry_after = None
        if "retry-after" in response.headers:
            try:
                retry_after = int(response.headers["retry-after"])
            except ValueError:
                pass
        
        is_retryable = error_type in [
            APIErrorType.RATE_LIMIT_ERROR,
            APIErrorType.SERVER_ERROR,
            APIErrorType.TIMEOUT_ERROR,
            APIErrorType.NETWORK_ERROR
        ]
        
        return APIError(
            error_type=error_type,
            message=message,
            status_code=response.status_code,
            details=details,
            retry_after=retry_after,
            is_retryable=is_retryable
        )
    
    def _should_retry(self, error: APIError) -> bool:
        """Determine if request should be retried"""
        return error.is_retryable and self.failure_count < self.circuit_breaker_threshold
    
    def _handle_circuit_breaker(self) -> None:
        """Handle circuit breaker logic"""
        current_time = time.time()
        
        # Check if circuit breaker should be reset
        if (current_time - self.circuit_breaker_last_failure) > self.circuit_breaker_timeout:
            self.failure_count = 0
            logger.info("Circuit breaker reset")
        
        # Check if circuit breaker is open
        if self.failure_count >= self.circuit_breaker_threshold:
            time_since_failure = current_time - self.circuit_breaker_last_failure
            if time_since_failure < self.circuit_breaker_timeout:
                raise APIError(
                    error_type=APIErrorType.SERVER_ERROR,
                    message=f"Circuit breaker open. Try again in {self.circuit_breaker_timeout - time_since_failure:.0f} seconds",
                    is_retryable=False
                )
    
    def _rate_limit(self) -> None:
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        **kwargs
    ) -> APIResponse:
        """
        Make HTTP request with comprehensive error handling and retry logic
        """
        # Handle circuit breaker
        self._handle_circuit_breaker()
        
        # Apply rate limiting
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
                logger.info(f"Making {method} request to {url}")
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    **kwargs
                )
                
                response_time = time.time() - start_time
                logger.info(f"Request completed in {response_time:.2f}s with status {response.status_code}")
                
                # Handle successful response
                if response.is_success:
                    self.failure_count = 0  # Reset failure count on success
                    
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        data = response.text
                    
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        response_time=response_time
                    )
                
                # Handle error response
                else:
                    self.failure_count += 1
                    self.circuit_breaker_last_failure = time.time()
                    
                    api_error = self._create_api_error(response=response)
                    logger.error(f"API request failed: {api_error}")
                    
                    return APIResponse(
                        success=False,
                        data=None,
                        error=api_error,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        response_time=response_time
                    )
        
        except Exception as e:
            self.failure_count += 1
            self.circuit_breaker_last_failure = time.time()
            
            response_time = time.time() - start_time
            api_error = self._create_api_error(exception=e)
            logger.error(f"Request exception: {api_error}")
            
            return APIResponse(
                success=False,
                data=None,
                error=api_error,
                response_time=response_time
            )
    
    def _handle_api_error(self, error: APIError, context: str) -> None:
        """Handle API errors with user-friendly messages"""
        error_messages = {
            APIErrorType.AUTHENTICATION_ERROR: {
                "title": "🔐 Authentication Required",
                "message": "Your session has expired. Please log in again.",
                "action": "login_required"
            },
            APIErrorType.AUTHORIZATION_ERROR: {
                "title": "🚫 Access Denied",
                "message": "You don't have permission to perform this action.",
                "action": "permission_denied"
            },
            APIErrorType.VALIDATION_ERROR: {
                "title": "⚠️ Invalid Input",
                "message": "Please check your input and try again.",
                "action": "fix_input"
            },
            APIErrorType.RATE_LIMIT_ERROR: {
                "title": "⏱️ Rate Limit Exceeded",
                "message": f"Too many requests. Please wait {error.retry_after or 60} seconds.",
                "action": "wait_and_retry"
            },
            APIErrorType.SERVER_ERROR: {
                "title": "🔧 Server Error",
                "message": "The server is experiencing issues. Please try again later.",
                "action": "retry_later"
            },
            APIErrorType.NETWORK_ERROR: {
                "title": "🌐 Connection Error",
                "message": "Please check your internet connection and try again.",
                "action": "check_connection"
            },
            APIErrorType.TIMEOUT_ERROR: {
                "title": "⏰ Request Timeout",
                "message": "The request took too long. Please try again.",
                "action": "retry"
            }
        }
        
        error_info = error_messages.get(error.error_type, {
            "title": "❌ Unknown Error",
            "message": "An unexpected error occurred. Please try again.",
            "action": "retry"
        })
        
        # Display error in Streamlit
        st.error(f"{error_info['title']}: {error_info['message']}")
        
        # Handle specific actions
        if error_info["action"] == "login_required":
            self.session_manager.clear_session()
            st.rerun()
        
        logger.error(f"API error in {context}: {error}")
    
    # Authentication methods
    async def register_user(self, email: str, password: str, name: str) -> AuthResult:
        """Register a new user"""
        try:
            response = await self._make_request(
                "POST",
                "/auth/register",
                json_data={
                    "email": email,
                    "password": password,
                    "name": name
                }
            )
            
            if response.success:
                data = response.data
                return AuthResult(
                    success=True,
                    access_token=data.get("access_token"),
                    user_id=data.get("user_id"),
                    email=data.get("email"),
                    name=data.get("name"),
                    expires_at=datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None
                )
            else:
                self._handle_api_error(response.error, "user registration")
                return AuthResult(success=False, error=response.error.message)
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return AuthResult(success=False, error=str(e))
    
    async def login_user(self, email: str, password: str) -> AuthResult:
        """Login user with email and password"""
        try:
            response = await self._make_request(
                "POST",
                "/auth/login",
                json_data={
                    "email": email,
                    "password": password
                }
            )
            
            if response.success:
                data = response.data
                return AuthResult(
                    success=True,
                    access_token=data.get("access_token"),
                    user_id=data.get("user_id"),
                    email=data.get("email"),
                    name=data.get("name"),
                    expires_at=datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None
                )
            else:
                self._handle_api_error(response.error, "user login")
                return AuthResult(success=False, error=response.error.message)
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            return AuthResult(success=False, error=str(e))
    
    async def refresh_token(self) -> bool:
        """Refresh authentication token"""
        try:
            response = await self._make_request("POST", "/auth/refresh")
            
            if response.success:
                data = response.data
                auth_result = AuthResult(
                    success=True,
                    access_token=data.get("access_token"),
                    user_id=self.session_manager.get_current_user_id(),
                    email=self.session_manager.get_user_email(),
                    name=self.session_manager.get_user_name(),
                    expires_at=datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None
                )
                self.session_manager.set_auth_data(auth_result)
                return True
            else:
                self._handle_api_error(response.error, "token refresh")
                return False
        
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False  
  
    # Conversation methods
    async def send_message(self, user_id: str, message: str) -> ConversationResponse:
        """Send a chat message and get AI response"""
        try:
            response = await self._make_request(
                "POST",
                "/conversations/message",
                json_data={
                    "user_id": user_id,
                    "message": message
                }
            )
            
            if response.success:
                data = response.data
                return ConversationResponse(
                    message=data.get("message", ""),
                    response_type=data.get("response_type", "text"),
                    confidence_score=data.get("confidence_score", 1.0),
                    suggested_actions=data.get("suggested_actions", []),
                    content_recommendations=data.get("content_recommendations", []),
                    follow_up_questions=data.get("follow_up_questions", []),
                    metadata=data.get("metadata", {})
                )
            else:
                self._handle_api_error(response.error, "send message")
                return ConversationResponse(
                    message="I'm sorry, I'm having trouble connecting right now. Please try again later."
                )
        
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return ConversationResponse(
                message="An unexpected error occurred. Please try again."
            )
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        try:
            response = await self._make_request(
                "GET",
                f"/conversations/history/{user_id}",
                params={"limit": limit}
            )
            
            if response.success:
                data = response.data
                return data.get("messages", [])
            else:
                self._handle_api_error(response.error, "get conversation history")
                return []
        
        except Exception as e:
            logger.error(f"Get conversation history error: {e}")
            return []
    
    async def clear_conversation_history(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        try:
            response = await self._make_request(
                "DELETE",
                f"/conversations/history/{user_id}"
            )
            
            if response.success:
                return True
            else:
                self._handle_api_error(response.error, "clear conversation history")
                return False
        
        except Exception as e:
            logger.error(f"Clear conversation history error: {e}")
            return False
    
    # Assessment methods
    async def start_assessment(self, user_id: str, skill_area: str) -> Optional[AssessmentSession]:
        """Start a skill assessment"""
        try:
            response = await self._make_request(
                "POST",
                "/assessments/start",
                json_data={
                    "user_id": user_id,
                    "skill_area": skill_area
                }
            )
            
            if response.success:
                data = response.data
                return AssessmentSession(
                    id=data.get("id"),
                    user_id=data.get("user_id"),
                    skill_area=data.get("skill_area"),
                    questions=data.get("questions", []),
                    current_question_index=data.get("current_question_index", 0),
                    status=data.get("status", "active"),
                    started_at=datetime.fromisoformat(data.get("started_at")) if data.get("started_at") else None,
                    progress=data.get("progress", 0.0)
                )
            else:
                self._handle_api_error(response.error, "start assessment")
                return None
        
        except Exception as e:
            logger.error(f"Start assessment error: {e}")
            return None
    
    async def submit_assessment_response(self, assessment_id: str, response: str) -> Optional[AssessmentSession]:
        """Submit assessment response"""
        try:
            api_response = await self._make_request(
                "POST",
                f"/assessments/{assessment_id}/response",
                json_data={
                    "assessment_id": assessment_id,
                    "response": response
                }
            )
            
            if api_response.success:
                data = api_response.data
                return AssessmentSession(
                    id=data.get("id"),
                    user_id=data.get("user_id"),
                    skill_area=data.get("skill_area"),
                    questions=data.get("questions", []),
                    current_question_index=data.get("current_question_index", 0),
                    status=data.get("status", "active"),
                    started_at=datetime.fromisoformat(data.get("started_at")) if data.get("started_at") else None,
                    progress=data.get("progress", 0.0)
                )
            else:
                self._handle_api_error(api_response.error, "submit assessment response")
                return None
        
        except Exception as e:
            logger.error(f"Submit assessment response error: {e}")
            return None
    
    async def complete_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Complete assessment and get results"""
        try:
            response = await self._make_request(
                "POST",
                f"/assessments/{assessment_id}/complete"
            )
            
            if response.success:
                return response.data
            else:
                self._handle_api_error(response.error, "complete assessment")
                return None
        
        except Exception as e:
            logger.error(f"Complete assessment error: {e}")
            return None
    
    async def get_user_assessments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's assessment history"""
        try:
            response = await self._make_request(
                "GET",
                f"/assessments/user/{user_id}"
            )
            
            if response.success:
                data = response.data
                return data.get("assessments", [])
            else:
                self._handle_api_error(response.error, "get user assessments")
                return []
        
        except Exception as e:
            logger.error(f"Get user assessments error: {e}")
            return []
    
    # Learning Path methods
    async def create_learning_path(self, user_id: str, goal: str) -> Optional[LearningPath]:
        """Create a learning path"""
        try:
            response = await self._make_request(
                "POST",
                "/learning/paths",
                json_data={
                    "user_id": user_id,
                    "goal": goal
                }
            )
            
            if response.success:
                data = response.data
                return LearningPath(
                    id=data.get("id"),
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    goal=data.get("goal", ""),
                    milestones=data.get("milestones", []),
                    estimated_duration=data.get("estimated_duration"),
                    difficulty_level=data.get("difficulty_level", "intermediate"),
                    prerequisites=data.get("prerequisites", []),
                    target_skills=data.get("target_skills", []),
                    created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else None,
                    progress=data.get("progress", 0.0)
                )
            else:
                self._handle_api_error(response.error, "create learning path")
                return None
        
        except Exception as e:
            logger.error(f"Create learning path error: {e}")
            return None
    
    async def get_user_learning_paths(self, user_id: str) -> List[LearningPath]:
        """Get user's learning paths"""
        try:
            response = await self._make_request(
                "GET",
                f"/learning/paths/user/{user_id}"
            )
            
            if response.success:
                data = response.data
                paths = []
                for path_data in data.get("learning_paths", []):
                    paths.append(LearningPath(
                        id=path_data.get("id"),
                        title=path_data.get("title", ""),
                        description=path_data.get("description", ""),
                        goal=path_data.get("goal", ""),
                        milestones=path_data.get("milestones", []),
                        estimated_duration=path_data.get("estimated_duration"),
                        difficulty_level=path_data.get("difficulty_level", "intermediate"),
                        prerequisites=path_data.get("prerequisites", []),
                        target_skills=path_data.get("target_skills", []),
                        created_at=datetime.fromisoformat(path_data.get("created_at")) if path_data.get("created_at") else None,
                        updated_at=datetime.fromisoformat(path_data.get("updated_at")) if path_data.get("updated_at") else None,
                        progress=path_data.get("progress", 0.0)
                    ))
                return paths
            else:
                self._handle_api_error(response.error, "get user learning paths")
                return []
        
        except Exception as e:
            logger.error(f"Get user learning paths error: {e}")
            return []
    
    async def update_milestone_status(self, path_id: str, milestone_id: str, status: str) -> bool:
        """Update milestone status"""
        try:
            response = await self._make_request(
                "PUT",
                f"/learning/paths/{path_id}/milestones/{milestone_id}",
                json_data={
                    "milestone_id": milestone_id,
                    "status": status
                }
            )
            
            if response.success:
                return True
            else:
                self._handle_api_error(response.error, "update milestone status")
                return False
        
        except Exception as e:
            logger.error(f"Update milestone status error: {e}")
            return False
    
    async def get_learning_path_progress(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Get learning path progress"""
        try:
            response = await self._make_request(
                "GET",
                f"/learning/paths/{path_id}/progress"
            )
            
            if response.success:
                return response.data
            else:
                self._handle_api_error(response.error, "get learning path progress")
                return None
        
        except Exception as e:
            logger.error(f"Get learning path progress error: {e}")
            return None
    
    # User Management methods
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            response = await self._make_request(
                "GET",
                f"/users/{user_id}"
            )
            
            if response.success:
                return response.data
            else:
                self._handle_api_error(response.error, "get user profile")
                return None
        
        except Exception as e:
            logger.error(f"Get user profile error: {e}")
            return None
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            response = await self._make_request(
                "PUT",
                f"/users/{user_id}/preferences",
                json_data={"learning_preferences": preferences}
            )
            
            if response.success:
                return True
            else:
                self._handle_api_error(response.error, "update user preferences")
                return False
        
        except Exception as e:
            logger.error(f"Update user preferences error: {e}")
            return False
    
    async def update_user_skills(self, user_id: str, skills: Dict[str, Any]) -> bool:
        """Update user skills"""
        try:
            response = await self._make_request(
                "PUT",
                f"/users/{user_id}/skills",
                json_data={"skills": skills}
            )
            
            if response.success:
                return True
            else:
                self._handle_api_error(response.error, "update user skills")
                return False
        
        except Exception as e:
            logger.error(f"Update user skills error: {e}")
            return False
    
    async def update_user_goals(self, user_id: str, goals: List[str]) -> bool:
        """Update user goals"""
        try:
            response = await self._make_request(
                "PUT",
                f"/users/{user_id}/goals",
                json_data={"career_goals": goals}
            )
            
            if response.success:
                return True
            else:
                self._handle_api_error(response.error, "update user goals")
                return False
        
        except Exception as e:
            logger.error(f"Update user goals error: {e}")
            return False
    
    # Privacy methods
    async def get_privacy_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get privacy settings"""
        try:
            response = await self._make_request(
                "GET",
                "/privacy/settings"
            )
            
            if response.success:
                return response.data
            else:
                self._handle_api_error(response.error, "get privacy settings")
                return None
        
        except Exception as e:
            logger.error(f"Get privacy settings error: {e}")
            return None
    
    async def update_privacy_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update privacy settings"""
        try:
            response = await self._make_request(
                "PUT",
                "/privacy/settings",
                json_data=settings
            )
            
            if response.success:
                return True
            else:
                self._handle_api_error(response.error, "update privacy settings")
                return False
        
        except Exception as e:
            logger.error(f"Update privacy settings error: {e}")
            return False
    
    async def export_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Export user data"""
        try:
            response = await self._make_request(
                "POST",
                "/privacy/export",
                json_data={
                    "include_sensitive": False,
                    "format": "json"
                }
            )
            
            if response.success:
                return response.data
            else:
                self._handle_api_error(response.error, "export user data")
                return None
        
        except Exception as e:
            logger.error(f"Export user data error: {e}")
            return None
    
    async def delete_user_data(self, user_id: str, data_types: List[str] = None) -> Optional[Dict[str, Any]]:
        """Delete user data"""
        try:
            json_data = {}
            if data_types:
                json_data["data_types"] = data_types
            
            response = await self._make_request(
                "DELETE",
                "/privacy/delete",
                json_data=json_data
            )
            
            if response.success:
                return response.data
            else:
                self._handle_api_error(response.error, "delete user data")
                return None
        
        except Exception as e:
            logger.error(f"Delete user data error: {e}")
            return None
    
    # Utility methods
    def get_connection_status(self) -> Dict[str, Any]:
        """Get API connection status"""
        return {
            "base_url": self.base_url,
            "authenticated": self.session_manager.is_authenticated(),
            "user_id": self.session_manager.get_current_user_id(),
            "failure_count": self.failure_count,
            "circuit_breaker_open": self.failure_count >= self.circuit_breaker_threshold,
            "token_expires_at": self.session_manager.get_token_expiry_time()
        }
    
    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.circuit_breaker_last_failure = 0
        logger.info("Circuit breaker manually reset")


# Utility functions for Streamlit integration
def create_api_client(base_url: str = None) -> EnhancedEdAgentAPI:
    """Create and configure API client"""
    if base_url is None:
        # Try to get from environment or use default
        import os
        base_url = os.getenv("EDAGENT_API_URL", "http://localhost:8000/api/v1")
    
    session_manager = SessionManager()
    return EnhancedEdAgentAPI(base_url, session_manager)


def handle_async_api_call(coro):
    """Handle async API calls in Streamlit"""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(coro)


def display_api_status(api_client: EnhancedEdAgentAPI) -> None:
    """Display API connection status in Streamlit"""
    status = api_client.get_connection_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status["authenticated"]:
            st.success("🔐 Authenticated")
        else:
            st.warning("🔓 Not Authenticated")
    
    with col2:
        if status["circuit_breaker_open"]:
            st.error("🔴 Circuit Breaker Open")
        else:
            st.success("🟢 API Available")
    
    with col3:
        if status["failure_count"] > 0:
            st.warning(f"⚠️ {status['failure_count']} Recent Failures")
        else:
            st.success("✅ No Recent Failures")
    
    # Show detailed status in expander
    with st.expander("API Status Details"):
        st.json(status)