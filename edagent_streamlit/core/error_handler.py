"""
Comprehensive Error Handling System for EdAgent Streamlit Application

This module provides centralized error handling with:
- User-friendly error messages and recovery suggestions
- Categorized error types with appropriate responses
- Retry mechanisms with exponential backoff
- Error tracking and alerting
- Graceful degradation for offline scenarios
"""

import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import streamlit as st

from .logger import get_logger


class ErrorCategory(Enum):
    """Error categories for appropriate handling"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    CLIENT = "client"
    DATA = "data"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "operation": self.operation,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "additional_data": self.additional_data
        }


@dataclass
class UserFriendlyError:
    """User-friendly error representation"""
    title: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    is_retryable: bool = False
    retry_after: Optional[int] = None
    suggested_actions: List[str] = field(default_factory=list)
    help_url: Optional[str] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "is_retryable": self.is_retryable,
            "retry_after": self.retry_after,
            "suggested_actions": self.suggested_actions,
            "help_url": self.help_url,
            "error_code": self.error_code
        }


class RetryConfig:
    """Configuration for retry mechanisms"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


class ErrorHandler:
    """
    Comprehensive error handling system with user-friendly messages,
    retry mechanisms, and proper error tracking
    """
    
    def __init__(self):
        self.logger = get_logger("error_handler")
        self.error_counts = {}
        self.last_error_times = {}
        
        # Error message templates
        self.error_messages = {
            ErrorCategory.AUTHENTICATION: {
                "title": "Authentication Required",
                "message": "Please log in to access this feature.",
                "actions": ["Log in", "Create account", "Reset password"]
            },
            ErrorCategory.AUTHORIZATION: {
                "title": "Access Denied",
                "message": "You don't have permission to perform this action.",
                "actions": ["Contact support", "Check permissions"]
            },
            ErrorCategory.VALIDATION: {
                "title": "Invalid Input",
                "message": "Please check your input and try again.",
                "actions": ["Review input", "Check format", "Get help"]
            },
            ErrorCategory.NETWORK: {
                "title": "Connection Problem",
                "message": "Unable to connect to the server. Please check your internet connection.",
                "actions": ["Check connection", "Retry", "Try again later"]
            },
            ErrorCategory.TIMEOUT: {
                "title": "Request Timeout",
                "message": "The request took too long to complete. This might be due to high server load.",
                "actions": ["Retry", "Try again later", "Contact support"]
            },
            ErrorCategory.RATE_LIMIT: {
                "title": "Too Many Requests",
                "message": "You've made too many requests. Please wait before trying again.",
                "actions": ["Wait and retry", "Reduce frequency"]
            },
            ErrorCategory.SERVER: {
                "title": "Server Error",
                "message": "Something went wrong on our end. We're working to fix it.",
                "actions": ["Try again later", "Contact support", "Check status page"]
            },
            ErrorCategory.CLIENT: {
                "title": "Application Error",
                "message": "An unexpected error occurred in the application.",
                "actions": ["Refresh page", "Clear cache", "Contact support"]
            },
            ErrorCategory.DATA: {
                "title": "Data Error",
                "message": "There was a problem with the data. Please try again.",
                "actions": ["Retry", "Check input", "Contact support"]
            },
            ErrorCategory.UNKNOWN: {
                "title": "Unexpected Error",
                "message": "An unexpected error occurred. Please try again.",
                "actions": ["Retry", "Refresh page", "Contact support"]
            }
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and message"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Authentication errors
        if any(keyword in error_message for keyword in ['unauthorized', 'authentication', 'login', 'token']):
            return ErrorCategory.AUTHENTICATION
        
        # Authorization errors
        if any(keyword in error_message for keyword in ['forbidden', 'permission', 'access denied']):
            return ErrorCategory.AUTHORIZATION
        
        # Validation errors
        if any(keyword in error_message for keyword in ['validation', 'invalid', 'bad request', 'malformed']):
            return ErrorCategory.VALIDATION
        
        # Network errors
        if any(keyword in error_message for keyword in ['connection', 'network', 'dns', 'unreachable']):
            return ErrorCategory.NETWORK
        
        # Timeout errors
        if any(keyword in error_message for keyword in ['timeout', 'timed out', 'deadline']):
            return ErrorCategory.TIMEOUT
        
        # Rate limit errors
        if any(keyword in error_message for keyword in ['rate limit', 'too many requests', 'quota']):
            return ErrorCategory.RATE_LIMIT
        
        # Server errors
        if any(keyword in error_message for keyword in ['server error', 'internal error', '500', '502', '503']):
            return ErrorCategory.SERVER
        
        # Data errors
        if any(keyword in error_message for keyword in ['data', 'parsing', 'format', 'json', 'xml']):
            return ErrorCategory.DATA
        
        return ErrorCategory.UNKNOWN
    
    def determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        # Critical errors that require immediate attention
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.SERVER]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors that significantly impact functionality
        if category in [ErrorCategory.AUTHORIZATION, ErrorCategory.NETWORK]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors that impact user experience
        if category in [ErrorCategory.TIMEOUT, ErrorCategory.RATE_LIMIT, ErrorCategory.DATA]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors that are recoverable
        return ErrorSeverity.LOW
    
    def is_retryable(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if error is retryable"""
        retryable_categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.SERVER
        ]
        return category in retryable_categories
    
    def create_user_friendly_error(
        self, 
        error: Exception, 
        context: ErrorContext,
        custom_message: Optional[str] = None
    ) -> UserFriendlyError:
        """Create user-friendly error from exception"""
        category = self.categorize_error(error)
        severity = self.determine_severity(error, category)
        is_retryable = self.is_retryable(error, category)
        
        # Get error template
        template = self.error_messages.get(category, self.error_messages[ErrorCategory.UNKNOWN])
        
        # Use custom message if provided
        message = custom_message or template["message"]
        
        # Extract retry-after from error if available
        retry_after = None
        error_str = str(error).lower()
        if 'retry-after' in error_str:
            try:
                import re
                match = re.search(r'retry-after[:\s]+(\d+)', error_str)
                if match:
                    retry_after = int(match.group(1))
            except:
                pass
        
        return UserFriendlyError(
            title=template["title"],
            message=message,
            category=category,
            severity=severity,
            is_retryable=is_retryable,
            retry_after=retry_after,
            suggested_actions=template["actions"],
            error_code=f"{category.value}_{type(error).__name__}"
        )
    
    async def handle_error(
        self, 
        error: Union[Exception, UserFriendlyError], 
        context: ErrorContext,
        show_to_user: bool = True
    ) -> None:
        """Handle error with comprehensive logging and user feedback"""
        # Convert exception to user-friendly error if needed
        if isinstance(error, Exception):
            user_error = self.create_user_friendly_error(error, context)
            original_error = error
        else:
            user_error = error
            original_error = None
        
        # Log error with full context
        self.logger.log_error_with_context(
            original_error or Exception(user_error.message),
            context.operation,
            context.user_id,
            **context.additional_data
        )
        
        # Track error frequency
        self._track_error_frequency(user_error, context)
        
        # Show error to user if requested
        if show_to_user:
            self._display_error_to_user(user_error, context)
        
        # Handle specific error categories
        await self._handle_category_specific_actions(user_error, context)
    
    def _track_error_frequency(self, error: UserFriendlyError, context: ErrorContext) -> None:
        """Track error frequency for alerting"""
        error_key = f"{error.category.value}:{context.operation}"
        current_time = datetime.now()
        
        # Initialize tracking if not exists
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
            self.last_error_times[error_key] = []
        
        # Increment count and track time
        self.error_counts[error_key] += 1
        self.last_error_times[error_key].append(current_time)
        
        # Clean old error times (keep only last hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.last_error_times[error_key] = [
            t for t in self.last_error_times[error_key] if t > cutoff_time
        ]
        
        # Check for error spikes
        recent_errors = len(self.last_error_times[error_key])
        if recent_errors >= 10:  # 10 errors in the last hour
            self.logger.critical(
                f"High error frequency detected: {error_key} ({recent_errors} errors in last hour)",
                event_type="error_spike",
                error_category=error.category.value,
                operation=context.operation,
                recent_count=recent_errors
            )
    
    def _display_error_to_user(self, error: UserFriendlyError, context: ErrorContext) -> None:
        """Display user-friendly error message in Streamlit"""
        # Choose appropriate Streamlit display method based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 **{error.title}**\n\n{error.message}")
        elif error.severity == ErrorSeverity.HIGH:
            st.error(f"❌ **{error.title}**\n\n{error.message}")
        elif error.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ **{error.title}**\n\n{error.message}")
        else:
            st.info(f"ℹ️ **{error.title}**\n\n{error.message}")
        
        # Show retry information
        if error.is_retryable:
            if error.retry_after:
                st.info(f"⏳ Please wait {error.retry_after} seconds before trying again.")
            else:
                st.info("🔄 You can try again now.")
        
        # Show suggested actions
        if error.suggested_actions:
            with st.expander("💡 Suggested Actions"):
                for action in error.suggested_actions:
                    st.write(f"• {action}")
        
        # Show help link if available
        if error.help_url:
            st.markdown(f"[📚 Get Help]({error.help_url})")
        
        # Show error code for support
        if error.error_code:
            st.caption(f"Error Code: {error.error_code}")
    
    async def _handle_category_specific_actions(
        self, 
        error: UserFriendlyError, 
        context: ErrorContext
    ) -> None:
        """Handle category-specific error actions"""
        if error.category == ErrorCategory.AUTHENTICATION:
            # Clear session and redirect to login
            if 'session_manager' in st.session_state:
                st.session_state.session_manager.clear_session()
            st.rerun()
        
        elif error.category == ErrorCategory.RATE_LIMIT:
            # Implement automatic retry with backoff
            if error.retry_after:
                await asyncio.sleep(error.retry_after)
        
        elif error.category == ErrorCategory.NETWORK:
            # Check connectivity and suggest offline mode
            self._suggest_offline_mode()
    
    def _suggest_offline_mode(self) -> None:
        """Suggest offline mode for network errors"""
        st.info("""
        🌐 **Connection Issues Detected**
        
        You can continue using EdAgent in limited offline mode:
        - View cached conversation history
        - Access saved learning paths
        - Review assessment results
        
        Full functionality will be restored when connection is available.
        """)
    
    def with_error_handling(
        self, 
        operation: str,
        user_id: Optional[str] = None,
        show_errors: bool = True,
        **context_data
    ):
        """Decorator for automatic error handling"""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                context = ErrorContext(
                    operation=operation,
                    user_id=user_id,
                    additional_data=context_data
                )
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    await self.handle_error(e, context, show_errors)
                    return None
            
            def sync_wrapper(*args, **kwargs):
                context = ErrorContext(
                    operation=operation,
                    user_id=user_id,
                    additional_data=context_data
                )
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Use asyncio.run for sync functions
                    asyncio.run(self.handle_error(e, context, show_errors))
                    return None
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def with_retry(
        self, 
        operation: str,
        retry_config: Optional[RetryConfig] = None,
        user_id: Optional[str] = None,
        **context_data
    ):
        """Decorator for automatic retry with error handling"""
        if retry_config is None:
            retry_config = RetryConfig()
        
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                context = ErrorContext(
                    operation=operation,
                    user_id=user_id,
                    additional_data=context_data
                )
                
                last_error = None
                for attempt in range(1, retry_config.max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        # Check if error is retryable
                        category = self.categorize_error(e)
                        if not self.is_retryable(e, category) or attempt == retry_config.max_attempts:
                            await self.handle_error(e, context)
                            return None
                        
                        # Wait before retry
                        delay = retry_config.get_delay(attempt)
                        self.logger.warning(
                            f"Attempt {attempt} failed for {operation}, retrying in {delay:.2f}s",
                            operation=operation,
                            attempt=attempt,
                            delay=delay,
                            error=str(e)
                        )
                        await asyncio.sleep(delay)
                
                # If we get here, all retries failed
                if last_error:
                    await self.handle_error(last_error, context)
                return None
            
            def sync_wrapper(*args, **kwargs):
                context = ErrorContext(
                    operation=operation,
                    user_id=user_id,
                    additional_data=context_data
                )
                
                last_error = None
                for attempt in range(1, retry_config.max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        # Check if error is retryable
                        category = self.categorize_error(e)
                        if not self.is_retryable(e, category) or attempt == retry_config.max_attempts:
                            asyncio.run(self.handle_error(e, context))
                            return None
                        
                        # Wait before retry
                        delay = retry_config.get_delay(attempt)
                        self.logger.warning(
                            f"Attempt {attempt} failed for {operation}, retrying in {delay:.2f}s",
                            operation=operation,
                            attempt=attempt,
                            delay=delay,
                            error=str(e)
                        )
                        time.sleep(delay)
                
                # If we get here, all retries failed
                if last_error:
                    asyncio.run(self.handle_error(last_error, context))
                return None
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def create_error_recovery_ui(self, error: UserFriendlyError) -> None:
        """Create interactive error recovery UI"""
        st.markdown("### 🔧 Error Recovery Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if error.is_retryable and st.button("🔄 Retry", key="error_retry"):
                st.rerun()
        
        with col2:
            if st.button("🏠 Go Home", key="error_home"):
                st.session_state.current_tab = "chat"
                st.rerun()
        
        with col3:
            if st.button("📞 Contact Support", key="error_support"):
                st.info("Please contact support at support@edagent.ai with error code: " + (error.error_code or "UNKNOWN"))
        
        # Show detailed error information for debugging
        if st.checkbox("Show technical details", key="error_details"):
            st.json(error.to_dict())
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=24)
        
        # Calculate statistics
        total_errors = sum(self.error_counts.values())
        recent_errors = {}
        
        for error_key, times in self.last_error_times.items():
            recent_count = len([t for t in times if t > cutoff_time])
            if recent_count > 0:
                recent_errors[error_key] = recent_count
        
        return {
            "total_errors": total_errors,
            "recent_errors_24h": sum(recent_errors.values()),
            "error_breakdown": recent_errors,
            "most_frequent_error": max(recent_errors.items(), key=lambda x: x[1]) if recent_errors else None,
            "timestamp": current_time.isoformat()
        }


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Convenience functions and decorators

def with_error_handling(operation: str, **kwargs):
    """Convenience decorator for error handling"""
    return get_error_handler().with_error_handling(operation, **kwargs)


def with_retry(operation: str, retry_config: Optional[RetryConfig] = None, **kwargs):
    """Convenience decorator for retry with error handling"""
    return get_error_handler().with_retry(operation, retry_config, **kwargs)


async def handle_error(error: Exception, operation: str, user_id: Optional[str] = None, **context_data):
    """Convenience function for handling errors"""
    context = ErrorContext(
        operation=operation,
        user_id=user_id,
        additional_data=context_data
    )
    await get_error_handler().handle_error(error, context)


def create_error_boundary(component_name: str):
    """Create error boundary for Streamlit components"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                context = ErrorContext(
                    operation=f"render_{component_name}",
                    additional_data={"component": component_name}
                )
                asyncio.run(error_handler.handle_error(e, context))
                
                # Show fallback UI
                st.error(f"Error loading {component_name}. Please refresh the page.")
                return None
        
        return wrapper
    return decorator