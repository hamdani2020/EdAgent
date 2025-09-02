"""
Custom middleware for the EdAgent API
"""

import time
import logging
from typing import Dict, Any
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm"""
    
    def __init__(self, app, requests_per_minute: int = 60, burst_size: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.window_size = 60  # 1 minute in seconds
        
        # Store request timestamps per client IP
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Cleanup task
        self._cleanup_task = None
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests for this client
        self._cleanup_old_requests(client_ip, current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record this request
        self.request_history[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.request_history[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_ip: str, current_time: float) -> None:
        """Remove requests older than the window"""
        cutoff_time = current_time - self.window_size
        history = self.request_history[client_ip]
        
        while history and history[0] < cutoff_time:
            history.popleft()
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        history = self.request_history[client_ip]
        
        # Check burst limit (requests in last few seconds)
        burst_cutoff = current_time - 10  # 10 seconds for burst
        recent_requests = sum(1 for timestamp in history if timestamp > burst_cutoff)
        
        if recent_requests >= self.burst_size:
            return True
        
        # Check overall rate limit
        return len(history) >= self.requests_per_minute


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response details"""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"in {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"in {process_time:.3f}s - {str(e)}"
            )
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for session and API key validation"""
    
    def __init__(self, app, auth_service=None):
        super().__init__(app)
        self.auth_service = auth_service
        
        # Paths that don't require authentication
        self.public_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/session",  # Session creation endpoint
            "/api/v1/auth/register",  # User registration endpoint
            "/api/v1/auth/login",  # User login endpoint
        }
        
        # Paths that require authentication
        self.protected_paths = {
            "/api/v1/conversations",
            "/api/v1/users",
            "/api/v1/assessments",
            "/api/v1/learning",
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with authentication"""
        # Skip authentication for public paths
        if self._is_public_path(request.url.path, request.method):
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check if path requires authentication
        if not self._requires_auth(request.url.path):
            return await call_next(request)
        
        # Validate authentication
        auth_result = await self._validate_authentication(request)
        
        if not auth_result.is_valid:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication required",
                    "message": auth_result.error_message or "Invalid or missing authentication"
                }
            )
        
        # Add user info to request state
        request.state.user_id = auth_result.user_id
        request.state.session_id = auth_result.session_id
        request.state.auth_session = auth_result.session
        
        return await call_next(request)
    
    def _is_public_path(self, path: str, method: str = None) -> bool:
        """Check if path is public (no auth required)"""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _requires_auth(self, path: str) -> bool:
        """Check if path requires authentication"""
        return any(path.startswith(protected_path) for protected_path in self.protected_paths)
    
    async def _validate_authentication(self, request: Request):
        """Validate authentication from request headers"""
        from ..services.auth_service import AuthenticationService
        
        if not self.auth_service:
            self.auth_service = AuthenticationService()
        
        # Check for session token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            return await self.auth_service.validate_session_token(token)
        
        # Check for API key in X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return await self.auth_service.validate_api_key(api_key)
        
        # No valid authentication found
        from ..models.auth import TokenValidationResult
        return TokenValidationResult(
            is_valid=False,
            error_message="No valid authentication provided"
        )


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Input sanitization and validation middleware"""
    
    def __init__(self, app, max_content_length: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_content_length = max_content_length
    
    async def dispatch(self, request: Request, call_next):
        """Sanitize and validate input"""
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request too large",
                    "message": f"Request body must be less than {self.max_content_length} bytes"
                }
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error": "Unsupported media type",
                        "message": "Content-Type must be application/json or multipart/form-data"
                    }
                )
        
        # Add security headers to prevent common attacks
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response