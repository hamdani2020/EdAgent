"""
Comprehensive Error Handling and Loading States System for EdAgent Streamlit App
Provides centralized error handling, user-friendly messages, retry mechanisms, and loading indicators.
"""

import streamlit as st
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    SERVER = "server"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    DATA = "data"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors"""
    operation: str
    user_id: Optional[str] = None
    timestamp: datetime = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class UserFriendlyError:
    """User-friendly error representation"""
    title: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    is_retryable: bool = False
    retry_after: Optional[int] = None
    suggested_actions: List[str] = None
    help_url: Optional[str] = None
    error_code: Optional[str] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


@dataclass
class LoadingState:
    """Loading state information"""
    operation: str
    message: str
    progress: Optional[float] = None
    start_time: datetime = None
    estimated_duration: Optional[int] = None
    cancellable: bool = False
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


class NetworkConnectivityChecker:
    """Check network connectivity and provide guidance"""
    
    def __init__(self):
        self.last_check_time = 0
        self.check_interval = 30  # seconds
        self.is_online = True
        
    async def check_connectivity(self, timeout: float = 5.0) -> bool:
        """Check if we can reach the internet"""
        current_time = time.time()
        
        # Don't check too frequently
        if current_time - self.last_check_time < self.check_interval:
            return self.is_online
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try to reach a reliable endpoint
                response = await client.get("https://httpbin.org/status/200")
                self.is_online = response.status_code == 200
        except Exception:
            self.is_online = False
        
        self.last_check_time = current_time
        return self.is_online
    
    def get_connectivity_guidance(self) -> Dict[str, Any]:
        """Get guidance for connectivity issues"""
        return {
            "title": "🌐 Connection Issue",
            "message": "Unable to connect to EdAgent services.",
            "suggestions": [
                "Check your internet connection",
                "Try refreshing the page",
                "Disable VPN if you're using one",
                "Check if your firewall is blocking the connection",
                "Try again in a few minutes"
            ],
            "troubleshooting_steps": [
                "1. Check if other websites are working",
                "2. Restart your router/modem",
                "3. Clear your browser cache",
                "4. Try using a different browser",
                "5. Contact your network administrator"
            ]
        }


class RateLimitHandler:
    """Handle rate limiting with user feedback"""
    
    def __init__(self):
        self.rate_limit_info = {}
        
    def handle_rate_limit(self, retry_after: int, operation: str) -> None:
        """Handle rate limit with user feedback"""
        self.rate_limit_info[operation] = {
            "retry_after": retry_after,
            "blocked_until": datetime.now() + timedelta(seconds=retry_after)
        }
        
        # Show user-friendly rate limit message
        st.warning(f"⏱️ **Rate Limit Reached**")
        st.info(f"Too many requests for {operation}. Please wait {retry_after} seconds before trying again.")
        
        # Show countdown timer
        self._show_countdown_timer(retry_after, operation)
    
    def _show_countdown_timer(self, retry_after: int, operation: str) -> None:
        """Show countdown timer for rate limit"""
        placeholder = st.empty()
        
        for remaining in range(retry_after, 0, -1):
            placeholder.info(f"⏳ You can try {operation} again in {remaining} seconds...")
            time.sleep(1)
        
        placeholder.success(f"✅ You can now try {operation} again!")
        
        # Clear rate limit info
        if operation in self.rate_limit_info:
            del self.rate_limit_info[operation]
    
    def is_rate_limited(self, operation: str) -> bool:
        """Check if operation is currently rate limited"""
        if operation not in self.rate_limit_info:
            return False
        
        blocked_until = self.rate_limit_info[operation]["blocked_until"]
        if datetime.now() >= blocked_until:
            del self.rate_limit_info[operation]
            return False
        
        return True
    
    def get_remaining_time(self, operation: str) -> int:
        """Get remaining time for rate limit"""
        if operation not in self.rate_limit_info:
            return 0
        
        blocked_until = self.rate_limit_info[operation]["blocked_until"]
        remaining = (blocked_until - datetime.now()).total_seconds()
        return max(0, int(remaining))


class LoadingStateManager:
    """Manage loading states with progress indicators"""
    
    def __init__(self):
        self.active_operations = {}
        
    def start_loading(self, operation: str, message: str, 
                     estimated_duration: Optional[int] = None,
                     cancellable: bool = False) -> str:
        """Start a loading operation"""
        loading_id = f"{operation}_{int(time.time())}"
        
        self.active_operations[loading_id] = LoadingState(
            operation=operation,
            message=message,
            estimated_duration=estimated_duration,
            cancellable=cancellable
        )
        
        return loading_id
    
    def update_progress(self, loading_id: str, progress: float, message: Optional[str] = None) -> None:
        """Update loading progress"""
        if loading_id in self.active_operations:
            self.active_operations[loading_id].progress = progress
            if message:
                self.active_operations[loading_id].message = message
    
    def finish_loading(self, loading_id: str) -> None:
        """Finish a loading operation"""
        if loading_id in self.active_operations:
            del self.active_operations[loading_id]
    
    def show_loading_spinner(self, loading_id: str) -> None:
        """Show loading spinner with progress"""
        if loading_id not in self.active_operations:
            return
        
        loading_state = self.active_operations[loading_id]
        
        # Show spinner with message
        with st.spinner(loading_state.message):
            # Show progress bar if progress is available
            if loading_state.progress is not None:
                st.progress(loading_state.progress)
            
            # Show estimated time remaining
            if loading_state.estimated_duration:
                elapsed = (datetime.now() - loading_state.start_time).total_seconds()
                remaining = max(0, loading_state.estimated_duration - elapsed)
                if remaining > 0:
                    st.caption(f"⏱️ Estimated time remaining: {int(remaining)}s")
            
            # Show cancel button if cancellable
            if loading_state.cancellable:
                if st.button("❌ Cancel", key=f"cancel_{loading_id}"):
                    self.finish_loading(loading_id)
                    st.warning("Operation cancelled")
                    st.stop()


class ErrorRecoveryManager:
    """Manage error recovery flows and graceful degradation"""
    
    def __init__(self):
        self.recovery_strategies = {}
        self.fallback_data = {}
        
    def register_recovery_strategy(self, error_category: ErrorCategory, 
                                 strategy: Callable) -> None:
        """Register a recovery strategy for an error category"""
        self.recovery_strategies[error_category] = strategy
    
    def set_fallback_data(self, operation: str, data: Any) -> None:
        """Set fallback data for an operation"""
        self.fallback_data[operation] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    def get_fallback_data(self, operation: str, max_age_minutes: int = 30) -> Optional[Any]:
        """Get fallback data if available and not too old"""
        if operation not in self.fallback_data:
            return None
        
        fallback_info = self.fallback_data[operation]
        age = (datetime.now() - fallback_info["timestamp"]).total_seconds() / 60
        
        if age <= max_age_minutes:
            return fallback_info["data"]
        
        # Remove old fallback data
        del self.fallback_data[operation]
        return None
    
    def attempt_recovery(self, error: UserFriendlyError, context: ErrorContext) -> bool:
        """Attempt to recover from an error"""
        if error.category in self.recovery_strategies:
            try:
                return self.recovery_strategies[error.category](error, context)
            except Exception as e:
                logger.error(f"Recovery strategy failed: {e}")
        
        return False


class EnhancedErrorHandler:
    """Comprehensive error handling system"""
    
    def __init__(self):
        self.connectivity_checker = NetworkConnectivityChecker()
        self.rate_limit_handler = RateLimitHandler()
        self.loading_manager = LoadingStateManager()
        self.recovery_manager = ErrorRecoveryManager()
        
        # Error message templates
        self.error_templates = {
            ErrorCategory.AUTHENTICATION: {
                "title": "🔐 Authentication Required",
                "message": "Your session has expired or is invalid.",
                "severity": ErrorSeverity.HIGH,
                "suggested_actions": [
                    "Log in again",
                    "Check your credentials",
                    "Clear browser cache if issues persist"
                ]
            },
            ErrorCategory.AUTHORIZATION: {
                "title": "🚫 Access Denied",
                "message": "You don't have permission to perform this action.",
                "severity": ErrorSeverity.MEDIUM,
                "suggested_actions": [
                    "Contact your administrator",
                    "Check if you have the required permissions",
                    "Try logging out and back in"
                ]
            },
            ErrorCategory.VALIDATION: {
                "title": "⚠️ Invalid Input",
                "message": "Please check your input and try again.",
                "severity": ErrorSeverity.LOW,
                "suggested_actions": [
                    "Review the form fields",
                    "Check for required fields",
                    "Ensure data formats are correct"
                ]
            },
            ErrorCategory.NETWORK: {
                "title": "🌐 Connection Error",
                "message": "Unable to connect to EdAgent services.",
                "severity": ErrorSeverity.HIGH,
                "is_retryable": True,
                "suggested_actions": [
                    "Check your internet connection",
                    "Try again in a moment",
                    "Contact support if the issue persists"
                ]
            },
            ErrorCategory.SERVER: {
                "title": "🔧 Server Error",
                "message": "The server is experiencing issues.",
                "severity": ErrorSeverity.HIGH,
                "is_retryable": True,
                "suggested_actions": [
                    "Try again in a few minutes",
                    "Check the status page",
                    "Contact support if the issue persists"
                ]
            },
            ErrorCategory.RATE_LIMIT: {
                "title": "⏱️ Rate Limit Exceeded",
                "message": "Too many requests. Please slow down.",
                "severity": ErrorSeverity.MEDIUM,
                "is_retryable": True,
                "suggested_actions": [
                    "Wait before trying again",
                    "Reduce the frequency of requests"
                ]
            },
            ErrorCategory.TIMEOUT: {
                "title": "⏰ Request Timeout",
                "message": "The request took too long to complete.",
                "severity": ErrorSeverity.MEDIUM,
                "is_retryable": True,
                "suggested_actions": [
                    "Try again",
                    "Check your connection speed",
                    "Try with a smaller request"
                ]
            }
        }
        
        # Register default recovery strategies
        self._register_default_recovery_strategies()
    
    def _register_default_recovery_strategies(self) -> None:
        """Register default recovery strategies"""
        
        def auth_recovery(error: UserFriendlyError, context: ErrorContext) -> bool:
            """Recovery strategy for authentication errors"""
            # Clear session and redirect to login
            if "session_manager" in st.session_state:
                st.session_state.session_manager.clear_session()
            st.rerun()
            return True
        
        def network_recovery(error: UserFriendlyError, context: ErrorContext) -> bool:
            """Recovery strategy for network errors"""
            # Try to use cached data
            fallback_data = self.recovery_manager.get_fallback_data(context.operation)
            if fallback_data:
                st.warning("🔄 Using cached data due to connection issues")
                return True
            return False
        
        self.recovery_manager.register_recovery_strategy(ErrorCategory.AUTHENTICATION, auth_recovery)
        self.recovery_manager.register_recovery_strategy(ErrorCategory.NETWORK, network_recovery)
    
    def create_user_friendly_error(self, exception: Exception, 
                                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                                 context: Optional[ErrorContext] = None) -> UserFriendlyError:
        """Create a user-friendly error from an exception"""
        
        # Get template for this category
        template = self.error_templates.get(category, {
            "title": "❌ Unexpected Error",
            "message": "An unexpected error occurred.",
            "severity": ErrorSeverity.MEDIUM,
            "suggested_actions": ["Try again", "Contact support if the issue persists"]
        })
        
        # Extract specific information from exception
        error_message = template["message"]
        retry_after = None
        
        if hasattr(exception, 'response') and exception.response:
            # HTTP error with response
            if hasattr(exception.response, 'status_code'):
                if exception.response.status_code == 429:
                    category = ErrorCategory.RATE_LIMIT
                    retry_after = self._extract_retry_after(exception.response)
                elif exception.response.status_code >= 500:
                    category = ErrorCategory.SERVER
                elif exception.response.status_code == 401:
                    category = ErrorCategory.AUTHENTICATION
                elif exception.response.status_code == 403:
                    category = ErrorCategory.AUTHORIZATION
        
        elif isinstance(exception, (httpx.TimeoutException, asyncio.TimeoutError)):
            category = ErrorCategory.TIMEOUT
        elif isinstance(exception, (httpx.NetworkError, httpx.ConnectError)):
            category = ErrorCategory.NETWORK
        
        return UserFriendlyError(
            title=template["title"],
            message=error_message,
            category=category,
            severity=template.get("severity", ErrorSeverity.MEDIUM),
            is_retryable=template.get("is_retryable", False),
            retry_after=retry_after,
            suggested_actions=template.get("suggested_actions", []),
            error_code=getattr(exception, 'code', None)
        )
    
    def _extract_retry_after(self, response) -> Optional[int]:
        """Extract retry-after header from response"""
        if hasattr(response, 'headers') and 'retry-after' in response.headers:
            try:
                return int(response.headers['retry-after'])
            except ValueError:
                pass
        return None
    
    async def handle_error(self, error: Union[Exception, UserFriendlyError], 
                          context: Optional[ErrorContext] = None,
                          show_details: bool = False) -> bool:
        """
        Handle an error with comprehensive error handling
        Returns True if error was recovered, False otherwise
        """
        
        # Convert exception to user-friendly error if needed
        if isinstance(error, Exception):
            user_error = self.create_user_friendly_error(error, context=context)
        else:
            user_error = error
        
        # Log the error
        logger.error(f"Error in {context.operation if context else 'unknown'}: {user_error.title} - {user_error.message}")
        
        # Check for network connectivity if it's a network error
        if user_error.category == ErrorCategory.NETWORK:
            is_online = await self.connectivity_checker.check_connectivity()
            if not is_online:
                self._show_connectivity_guidance()
                return False
        
        # Handle rate limiting
        if user_error.category == ErrorCategory.RATE_LIMIT and user_error.retry_after:
            self.rate_limit_handler.handle_rate_limit(
                user_error.retry_after, 
                context.operation if context else "operation"
            )
            return False
        
        # Attempt recovery
        recovery_successful = self.recovery_manager.attempt_recovery(user_error, context)
        if recovery_successful:
            return True
        
        # Show error to user
        self._display_error(user_error, show_details)
        
        return False
    
    def _show_connectivity_guidance(self) -> None:
        """Show connectivity guidance to user"""
        guidance = self.connectivity_checker.get_connectivity_guidance()
        
        st.error(f"{guidance['title']}: {guidance['message']}")
        
        with st.expander("🔧 Troubleshooting Steps"):
            for suggestion in guidance["suggestions"]:
                st.write(f"• {suggestion}")
            
            st.subheader("Detailed Steps:")
            for step in guidance["troubleshooting_steps"]:
                st.write(step)
    
    def _display_error(self, error: UserFriendlyError, show_details: bool = False) -> None:
        """Display error to user with appropriate styling"""
        
        # Choose appropriate Streamlit method based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            st.error(f"{error.title}")
            st.error(f"**Critical:** {error.message}")
        elif error.severity == ErrorSeverity.HIGH:
            st.error(f"{error.title}: {error.message}")
        elif error.severity == ErrorSeverity.MEDIUM:
            st.warning(f"{error.title}: {error.message}")
        else:
            st.info(f"{error.title}: {error.message}")
        
        # Show suggested actions
        if error.suggested_actions:
            with st.expander("💡 Suggested Actions"):
                for action in error.suggested_actions:
                    st.write(f"• {action}")
        
        # Show retry information
        if error.is_retryable:
            if error.retry_after:
                st.info(f"⏳ You can try again in {error.retry_after} seconds")
            else:
                st.info("🔄 You can try this operation again")
        
        # Show help URL if available
        if error.help_url:
            st.markdown(f"[📖 Get Help]({error.help_url})")
        
        # Show error details if requested
        if show_details and error.error_code:
            with st.expander("🔍 Technical Details"):
                st.code(f"Error Code: {error.error_code}")
    
    def with_error_handling(self, operation: str, show_loading: bool = True):
        """Decorator for functions that need error handling"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                context = ErrorContext(operation=operation)
                loading_id = None
                
                try:
                    if show_loading:
                        loading_id = self.loading_manager.start_loading(
                            operation, f"Processing {operation}..."
                        )
                        self.loading_manager.show_loading_spinner(loading_id)
                    
                    result = await func(*args, **kwargs)
                    
                    if loading_id:
                        self.loading_manager.finish_loading(loading_id)
                    
                    return result
                
                except Exception as e:
                    if loading_id:
                        self.loading_manager.finish_loading(loading_id)
                    
                    await self.handle_error(e, context)
                    return None
            
            return wrapper
        return decorator


# Global error handler instance
error_handler = EnhancedErrorHandler()


# Convenience functions for common operations
def show_loading(message: str, progress: Optional[float] = None, 
                estimated_duration: Optional[int] = None) -> str:
    """Show loading state with optional progress"""
    loading_id = error_handler.loading_manager.start_loading(
        "operation", message, estimated_duration
    )
    
    if progress is not None:
        error_handler.loading_manager.update_progress(loading_id, progress)
    
    error_handler.loading_manager.show_loading_spinner(loading_id)
    return loading_id


def update_loading_progress(loading_id: str, progress: float, message: Optional[str] = None):
    """Update loading progress"""
    error_handler.loading_manager.update_progress(loading_id, progress, message)


def finish_loading(loading_id: str):
    """Finish loading operation"""
    error_handler.loading_manager.finish_loading(loading_id)


async def handle_api_error(exception: Exception, operation: str, 
                          user_id: Optional[str] = None) -> bool:
    """Handle API error with context"""
    context = ErrorContext(operation=operation, user_id=user_id)
    return await error_handler.handle_error(exception, context)


def with_retry(max_attempts: int = 3, backoff_factor: float = 1.0):
    """Decorator for retry logic with exponential backoff"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=backoff_factor, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )


# Error handling context manager
class ErrorHandlingContext:
    """Context manager for error handling"""
    
    def __init__(self, operation: str, show_loading: bool = True, 
                 loading_message: Optional[str] = None):
        self.operation = operation
        self.show_loading = show_loading
        self.loading_message = loading_message or f"Processing {operation}..."
        self.loading_id = None
        self.context = ErrorContext(operation=operation)
    
    def __enter__(self):
        if self.show_loading:
            self.loading_id = error_handler.loading_manager.start_loading(
                self.operation, self.loading_message
            )
            error_handler.loading_manager.show_loading_spinner(self.loading_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.loading_id:
            error_handler.loading_manager.finish_loading(self.loading_id)
        
        if exc_type is not None:
            # Handle the exception
            asyncio.create_task(error_handler.handle_error(exc_val, self.context))
            return True  # Suppress the exception
        
        return False
    
    def update_progress(self, progress: float, message: Optional[str] = None):
        """Update loading progress"""
        if self.loading_id:
            error_handler.loading_manager.update_progress(self.loading_id, progress, message)


# Utility function to create error handling context
def error_context(operation: str, show_loading: bool = True, 
                 loading_message: Optional[str] = None) -> ErrorHandlingContext:
    """Create error handling context"""
    return ErrorHandlingContext(operation, show_loading, loading_message)