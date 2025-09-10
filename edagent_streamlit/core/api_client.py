"""
Enhanced API Client for EdAgent Streamlit Application

This module provides a robust, maintainable API client with:
- Comprehensive error handling and retry logic
- Automatic token refresh and session management
- Response caching and offline support
- Performance monitoring and logging
- Consistent API integration patterns
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx

from .config import get_config
from .logger import get_logger, PerformanceContext
from .error_handler import get_error_handler, ErrorCategory, ErrorContext, RetryConfig
from .session_manager import SessionManager


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
    headers: Dict[str, str] = field(default_factory=dict)
    response_time: float = 0.0
    cached: bool = False
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class AuthResult:
    """Authentication result data"""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
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
    suggested_actions: List[str] = field(default_factory=list)
    content_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssessmentSession:
    """Assessment session data"""
    id: str
    user_id: str
    skill_area: str
    questions: List[Dict[str, Any]] = field(default_factory=list)
    current_question_index: int = 0
    status: str = "active"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0


@dataclass
class LearningPath:
    """Learning path data"""
    id: str
    title: str
    description: str = ""
    goal: str = ""
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration: Optional[int] = None
    difficulty_level: str = "intermediate"
    prerequisites: List[str] = field(default_factory=list)
    target_skills: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    progress: float = 0.0


class ResponseCache:
    """Simple in-memory response cache with TTL"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached response if not expired"""
        if key in self.cache:
            data, expires_at = self.cache[key]
            if datetime.now() < expires_at:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Cache response with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (data, expires_at)
    
    def clear(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, expires_at) in self.cache.items()
            if current_time >= expires_at
        ]
        for key in expired_keys:
            del self.cache[key]


class EnhancedEdAgentAPI:
    """
    Enhanced API client with comprehensive error handling, retry logic, 
    caching, and performance monitoring
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.config = get_config()
        self.logger = get_logger("api_client")
        self.error_handler = get_error_handler()
        self.session_manager = session_manager
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=self.config.api.timeout,
            write=10.0,
            pool=5.0
        )
        self.limits = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20
        )
        
        # Response cache
        self.cache = ResponseCache()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0 / self.config.api.rate_limit_requests * 60  # Convert to seconds
        
        # Circuit breaker state
        self.failure_count = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.circuit_breaker_last_failure = 0
        
        self.logger.info(f"Enhanced EdAgent API client initialized with base URL: {self.config.api.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = self.config.get_api_headers()
        
        if self.session_manager and self.session_manager.is_authenticated():
            token = self.session_manager.get_auth_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def _create_cache_key(self, method: str, endpoint: str, params: Optional[Dict] = None) -> str:
        """Create cache key for request"""
        key_parts = [method.upper(), endpoint]
        if params:
            # Sort params for consistent cache keys
            sorted_params = sorted(params.items())
            key_parts.append(json.dumps(sorted_params, sort_keys=True))
        return ":".join(key_parts)
    
    def _is_cacheable(self, method: str, endpoint: str) -> bool:
        """Determine if request is cacheable"""
        # Only cache GET requests for specific endpoints
        if method.upper() != "GET":
            return False
        
        cacheable_endpoints = [
            "/users/",
            "/learning/paths",
            "/assessments/history",
            "/privacy/settings"
        ]
        
        return any(endpoint.startswith(ep) for ep in cacheable_endpoints)
    
    def _categorize_error(self, response: httpx.Response = None, exception: Exception = None) -> APIErrorType:
        """Categorize error based on response or exception"""
        if exception:
            if isinstance(exception, httpx.TimeoutException):
                return APIErrorType.TIMEOUT_ERROR
            elif isinstance(exception, (httpx.NetworkError, httpx.ConnectError)):
                return APIErrorType.NETWORK_ERROR
            else:
                return APIErrorType.UNKNOWN_ERROR
        
        if response:
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
        
        return APIErrorType.UNKNOWN_ERROR
    
    def _create_api_error(self, response: httpx.Response = None, exception: Exception = None) -> APIError:
        """Create APIError from response or exception"""
        if exception:
            error_type = self._categorize_error(exception=exception)
            return APIError(
                error_type=error_type,
                message=str(exception),
                is_retryable=error_type in [APIErrorType.NETWORK_ERROR, APIErrorType.TIMEOUT_ERROR]
            )
        
        error_type = self._categorize_error(response=response)
        
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
    
    def _handle_circuit_breaker(self) -> None:
        """Handle circuit breaker logic"""
        current_time = time.time()
        
        # Check if circuit breaker should be reset
        if (current_time - self.circuit_breaker_last_failure) > self.circuit_breaker_timeout:
            self.failure_count = 0
            self.logger.info("Circuit breaker reset")
        
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
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        **kwargs
    ) -> APIResponse:
        """
        Make HTTP request with comprehensive error handling, caching, and monitoring
        """
        # Handle circuit breaker
        self._handle_circuit_breaker()
        
        # Apply rate limiting
        self._rate_limit()
        
        # Check cache for GET requests
        cache_key = None
        if use_cache and self._is_cacheable(method, endpoint):
            cache_key = self._create_cache_key(method, endpoint, params)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for {method} {endpoint}")
                return APIResponse(
                    success=True,
                    data=cached_response,
                    cached=True
                )
        
        url = f"{self.config.api.base_url}{endpoint}"
        headers = self._get_headers()
        
        with PerformanceContext(self.logger, f"api_request_{method}_{endpoint.replace('/', '_')}"):
            start_time = time.time()
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
                    self.logger.debug(f"Making {method} request to {url}")
                    
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        params=params,
                        **kwargs
                    )
                    
                    response_time = time.time() - start_time
                    
                    # Log API call performance
                    self.logger.log_api_interaction(
                        endpoint=endpoint,
                        method=method,
                        status_code=response.status_code,
                        duration=response_time,
                        user_id=self.session_manager.get_current_user().user_id if self.session_manager and self.session_manager.is_authenticated() else None
                    )
                    
                    # Handle successful response
                    if response.is_success:
                        self.failure_count = 0  # Reset failure count on success
                        
                        try:
                            data = response.json()
                        except json.JSONDecodeError:
                            data = response.text
                        
                        # Cache successful GET responses
                        if cache_key and use_cache:
                            self.cache.set(cache_key, data, cache_ttl)
                        
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
                        self.logger.error(f"API request failed: {api_error}")
                        
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
                self.logger.error(f"Request exception: {api_error}")
                
                return APIResponse(
                    success=False,
                    data=None,
                    error=api_error,
                    response_time=response_time
                )
    
    # Authentication methods with enhanced error handling
    
    @get_error_handler().with_retry("user_registration", RetryConfig(max_attempts=2))
    async def register_user(self, email: str, password: str, name: str) -> AuthResult:
        """Register a new user with enhanced error handling"""
        try:
            response = await self._make_request(
                "POST",
                "/auth/register",
                json_data={
                    "email": email,
                    "password": password,
                    "name": name
                },
                use_cache=False
            )
            
            if response.success:
                data = response.data
                return AuthResult(
                    success=True,
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    user_id=data.get("user_id"),
                    email=data.get("email"),
                    name=data.get("name"),
                    expires_at=self._parse_datetime(data.get("expires_at"))
                )
            else:
                return AuthResult(success=False, error=response.error.message)
        
        except Exception as e:
            self.logger.exception("Registration error")
            return AuthResult(success=False, error=str(e))
    
    @get_error_handler().with_retry("user_login", RetryConfig(max_attempts=2))
    async def login_user(self, email: str, password: str) -> AuthResult:
        """Login user with enhanced error handling"""
        try:
            response = await self._make_request(
                "POST",
                "/auth/login",
                json_data={
                    "email": email,
                    "password": password
                },
                use_cache=False
            )
            
            if response.success:
                data = response.data
                return AuthResult(
                    success=True,
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    user_id=data.get("user_id"),
                    email=data.get("email"),
                    name=data.get("name"),
                    expires_at=self._parse_datetime(data.get("expires_at"))
                )
            else:
                return AuthResult(success=False, error=response.error.message)
        
        except Exception as e:
            self.logger.exception("Login error")
            return AuthResult(success=False, error=str(e))
    
    async def refresh_token(self) -> bool:
        """Refresh authentication token"""
        try:
            response = await self._make_request("POST", "/auth/refresh", use_cache=False)
            
            if response.success:
                data = response.data
                if self.session_manager:
                    self.session_manager.update_token(
                        access_token=data.get("access_token"),
                        expires_at=self._parse_datetime(data.get("expires_at")),
                        refresh_token=data.get("refresh_token")
                    )
                return True
            else:
                self.logger.error(f"Token refresh failed: {response.error}")
                return False
        
        except Exception as e:
            self.logger.exception("Token refresh error")
            return False
    
    # Conversation methods
    
    @get_error_handler().with_retry("send_message")
    async def send_message(self, user_id: str, message: str) -> ConversationResponse:
        """Send a chat message with enhanced error handling"""
        try:
            response = await self._make_request(
                "POST",
                "/conversations/message",
                json_data={
                    "user_id": user_id,
                    "message": message
                },
                use_cache=False
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
                # Return fallback response for errors
                return ConversationResponse(
                    message="I'm sorry, I'm having trouble connecting right now. Please try again later.",
                    metadata={"error": True, "error_message": response.error.message}
                )
        
        except Exception as e:
            self.logger.exception("Send message error")
            return ConversationResponse(
                message="An unexpected error occurred. Please try again.",
                metadata={"error": True, "error_message": str(e)}
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
                self.logger.error(f"Get conversation history failed: {response.error}")
                return []
        
        except Exception as e:
            self.logger.exception("Get conversation history error")
            return []
    
    async def clear_conversation_history(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        try:
            response = await self._make_request(
                "DELETE",
                f"/conversations/history/{user_id}",
                use_cache=False
            )
            
            if response.success:
                # Clear related cache entries
                self.cache.clear()
                return True
            else:
                self.logger.error(f"Clear conversation history failed: {response.error}")
                return False
        
        except Exception as e:
            self.logger.exception("Clear conversation history error")
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
                },
                use_cache=False
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
                    started_at=self._parse_datetime(data.get("started_at")),
                    progress=data.get("progress", 0.0)
                )
            else:
                self.logger.error(f"Start assessment failed: {response.error}")
                return None
        
        except Exception as e:
            self.logger.exception("Start assessment error")
            return None
    
    # Learning path methods
    
    async def create_learning_path(self, user_id: str, goal: str) -> Optional[LearningPath]:
        """Create a learning path"""
        try:
            response = await self._make_request(
                "POST",
                "/learning/paths",
                json_data={
                    "user_id": user_id,
                    "goal": goal
                },
                use_cache=False
            )
            
            if response.success:
                data = response.data
                return LearningPath(
                    id=data.get("id"),
                    title=data.get("title"),
                    description=data.get("description", ""),
                    goal=data.get("goal", ""),
                    milestones=data.get("milestones", []),
                    estimated_duration=data.get("estimated_duration"),
                    difficulty_level=data.get("difficulty_level", "intermediate"),
                    prerequisites=data.get("prerequisites", []),
                    target_skills=data.get("target_skills", []),
                    created_at=self._parse_datetime(data.get("created_at")),
                    updated_at=self._parse_datetime(data.get("updated_at")),
                    progress=data.get("progress", 0.0)
                )
            else:
                self.logger.error(f"Create learning path failed: {response.error}")
                return None
        
        except Exception as e:
            self.logger.exception("Create learning path error")
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
                for path_data in data.get("paths", []):
                    paths.append(LearningPath(
                        id=path_data.get("id"),
                        title=path_data.get("title"),
                        description=path_data.get("description", ""),
                        goal=path_data.get("goal", ""),
                        milestones=path_data.get("milestones", []),
                        estimated_duration=path_data.get("estimated_duration"),
                        difficulty_level=path_data.get("difficulty_level", "intermediate"),
                        prerequisites=path_data.get("prerequisites", []),
                        target_skills=path_data.get("target_skills", []),
                        created_at=self._parse_datetime(path_data.get("created_at")),
                        updated_at=self._parse_datetime(path_data.get("updated_at")),
                        progress=path_data.get("progress", 0.0)
                    ))
                return paths
            else:
                self.logger.error(f"Get user learning paths failed: {response.error}")
                return []
        
        except Exception as e:
            self.logger.exception("Get user learning paths error")
            return []
    
    # Privacy methods
    
    async def export_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Export user data"""
        try:
            response = await self._make_request(
                "POST",
                "/privacy/export",
                json_data={
                    "include_sensitive": False,
                    "format": "json"
                },
                use_cache=False
            )
            
            if response.success:
                return response.data
            else:
                self.logger.error(f"Export user data failed: {response.error}")
                return None
        
        except Exception as e:
            self.logger.exception("Export user data error")
            return None
    
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
                self.logger.error(f"Get privacy settings failed: {response.error}")
                return None
        
        except Exception as e:
            self.logger.exception("Get privacy settings error")
            return None
    
    # User management methods
    
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
                self.logger.error(f"Get user profile failed: {response.error}")
                return None
        
        except Exception as e:
            self.logger.exception("Get user profile error")
            return None
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            response = await self._make_request(
                "PUT",
                f"/users/{user_id}/preferences",
                json_data=preferences,
                use_cache=False
            )
            
            if response.success:
                # Clear related cache entries
                self.cache.clear()
                return True
            else:
                self.logger.error(f"Update user preferences failed: {response.error}")
                return False
        
        except Exception as e:
            self.logger.exception("Update user preferences error")
            return False
    
    # Utility methods
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Safely parse datetime strings"""
        if not datetime_str:
            return None
        
        try:
            # Handle 'Z' suffix by replacing it with '+00:00'
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            
            # Try parsing with timezone info first
            try:
                dt = datetime.fromisoformat(datetime_str)
                # Convert to naive datetime (assume UTC if timezone-aware)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except ValueError:
                # Fallback: try without timezone info
                if '+' in datetime_str:
                    datetime_str = datetime_str.split('+')[0]
                return datetime.fromisoformat(datetime_str)
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Failed to parse datetime string '{datetime_str}': {e}")
            return None
    
    def clear_cache(self) -> None:
        """Clear response cache"""
        self.cache.clear()
        self.logger.info("API response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.cache.cleanup_expired()
        return {
            "cache_size": len(self.cache.cache),
            "cache_keys": list(self.cache.cache.keys())
        }
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "failure_count": self.failure_count,
            "circuit_breaker_open": self.failure_count >= self.circuit_breaker_threshold,
            "last_failure_time": self.circuit_breaker_last_failure,
            "cache_stats": self.get_cache_stats()
        }