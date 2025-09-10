"""
Comprehensive Retry System for EdAgent Streamlit App
Provides intelligent retry mechanisms with exponential backoff, circuit breakers, and user feedback.
"""

import streamlit as st
import asyncio
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import httpx
from tenacity import (
    retry, stop_after_attempt, wait_exponential, wait_fixed,
    retry_if_exception_type, retry_if_result, before_sleep_log,
    after_log, RetryError
)

from streamlit_error_handler import ErrorCategory, UserFriendlyError
from streamlit_loading_components import show_loading, LoadingStyle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Different retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    JITTERED_BACKOFF = "jittered_backoff"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    timeout: Optional[float] = None
    
    # Exception types to retry on
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.ConnectError,
        ConnectionError,
        TimeoutError
    ])
    
    # HTTP status codes to retry on
    retryable_status_codes: List[int] = field(default_factory=lambda: [
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504   # Gateway Timeout
    ])
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    exception: Optional[Exception] = None
    response_code: Optional[int] = None
    delay: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False


@dataclass
class RetryHistory:
    """History of retry attempts for an operation"""
    operation_name: str
    attempts: List[RetryAttempt] = field(default_factory=list)
    total_duration: float = 0.0
    final_success: bool = False
    
    def add_attempt(self, attempt: RetryAttempt) -> None:
        """Add a retry attempt to history"""
        self.attempts.append(attempt)
    
    def get_success_rate(self) -> float:
        """Get success rate of attempts"""
        if not self.attempts:
            return 0.0
        successful = sum(1 for attempt in self.attempts if attempt.success)
        return successful / len(self.attempts)


class CircuitBreaker:
    """Circuit breaker implementation for preventing cascading failures"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if not self.config.circuit_breaker_enabled:
            return True
        
        current_time = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.state == CircuitBreakerState.OPEN:
            if (current_time - self.last_failure_time).total_seconds() >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self) -> None:
        """Record a successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker transitioning to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning("Circuit breaker transitioning to OPEN")
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker transitioning back to OPEN")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "can_execute": self.can_execute()
        }


class RetryDelayCalculator:
    """Calculate retry delays based on different strategies"""
    
    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float, multiplier: float, 
                           max_delay: float, jitter: bool = True) -> float:
        """Calculate exponential backoff delay"""
        delay = base_delay * (multiplier ** (attempt - 1))
        delay = min(delay, max_delay)
        
        if jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    @staticmethod
    def linear_backoff(attempt: int, base_delay: float, max_delay: float) -> float:
        """Calculate linear backoff delay"""
        delay = base_delay * attempt
        return min(delay, max_delay)
    
    @staticmethod
    def fibonacci_backoff(attempt: int, base_delay: float, max_delay: float) -> float:
        """Calculate Fibonacci sequence backoff delay"""
        def fibonacci(n):
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b
        
        delay = base_delay * fibonacci(attempt)
        return min(delay, max_delay)
    
    @staticmethod
    def fixed_delay(base_delay: float, jitter: bool = True) -> float:
        """Calculate fixed delay"""
        delay = base_delay
        
        if jitter:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    @staticmethod
    def calculate_delay(strategy: RetryStrategy, attempt: int, config: RetryConfig) -> float:
        """Calculate delay based on strategy"""
        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return RetryDelayCalculator.exponential_backoff(
                attempt, config.base_delay, config.multiplier, config.max_delay, config.jitter
            )
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return RetryDelayCalculator.linear_backoff(
                attempt, config.base_delay, config.max_delay
            )
        elif strategy == RetryStrategy.FIBONACCI_BACKOFF:
            return RetryDelayCalculator.fibonacci_backoff(
                attempt, config.base_delay, config.max_delay
            )
        elif strategy == RetryStrategy.FIXED_DELAY:
            return RetryDelayCalculator.fixed_delay(config.base_delay, config.jitter)
        elif strategy == RetryStrategy.JITTERED_BACKOFF:
            base_delay = RetryDelayCalculator.exponential_backoff(
                attempt, config.base_delay, config.multiplier, config.max_delay, False
            )
            # Add more aggressive jitter
            jitter_range = base_delay * 0.5
            return max(0, base_delay + random.uniform(-jitter_range, jitter_range))
        else:
            return config.base_delay


class EnhancedRetryManager:
    """Enhanced retry manager with comprehensive retry logic"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_histories: Dict[str, RetryHistory] = {}
        self.active_retries: Dict[str, bool] = {}
        
    def get_circuit_breaker(self, operation_name: str, config: RetryConfig) -> CircuitBreaker:
        """Get or create circuit breaker for operation"""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreaker(config)
        return self.circuit_breakers[operation_name]
    
    def should_retry(self, exception: Exception, response_code: Optional[int], 
                    config: RetryConfig) -> bool:
        """Determine if operation should be retried"""
        # Check exception type
        if any(isinstance(exception, exc_type) for exc_type in config.retryable_exceptions):
            return True
        
        # Check HTTP status code
        if response_code and response_code in config.retryable_status_codes:
            return True
        
        # Check for specific error patterns
        if hasattr(exception, 'response') and exception.response:
            status_code = getattr(exception.response, 'status_code', None)
            if status_code in config.retryable_status_codes:
                return True
        
        return False
    
    async def execute_with_retry(self, operation_name: str, operation: Callable,
                               config: RetryConfig, *args, **kwargs) -> Any:
        """Execute operation with retry logic"""
        
        circuit_breaker = self.get_circuit_breaker(operation_name, config)
        history = RetryHistory(operation_name)
        self.retry_histories[operation_name] = history
        
        start_time = time.time()
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            state_info = circuit_breaker.get_state_info()
            raise Exception(f"Circuit breaker is {state_info['state']} for {operation_name}")
        
        self.active_retries[operation_name] = True
        
        try:
            for attempt in range(1, config.max_attempts + 1):
                attempt_info = RetryAttempt(attempt_number=attempt)
                
                try:
                    # Show retry information to user
                    if attempt > 1:
                        self._show_retry_info(operation_name, attempt, config.max_attempts)
                    
                    # Execute operation
                    if asyncio.iscoroutinefunction(operation):
                        result = await operation(*args, **kwargs)
                    else:
                        result = operation(*args, **kwargs)
                    
                    # Success
                    attempt_info.success = True
                    history.add_attempt(attempt_info)
                    circuit_breaker.record_success()
                    history.final_success = True
                    
                    if attempt > 1:
                        st.success(f"✅ {operation_name} succeeded after {attempt} attempts!")
                    
                    return result
                
                except Exception as e:
                    attempt_info.exception = e
                    
                    # Extract response code if available
                    response_code = None
                    if hasattr(e, 'response') and e.response:
                        response_code = getattr(e.response, 'status_code', None)
                        attempt_info.response_code = response_code
                    
                    history.add_attempt(attempt_info)
                    
                    # Check if we should retry
                    if attempt >= config.max_attempts or not self.should_retry(e, response_code, config):
                        circuit_breaker.record_failure()
                        raise e
                    
                    # Calculate delay for next attempt
                    delay = RetryDelayCalculator.calculate_delay(config.strategy, attempt, config)
                    attempt_info.delay = delay
                    
                    # Show retry delay to user
                    await self._show_retry_delay(operation_name, attempt, delay, e)
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
        
        finally:
            self.active_retries[operation_name] = False
            history.total_duration = time.time() - start_time
    
    def _show_retry_info(self, operation_name: str, attempt: int, max_attempts: int) -> None:
        """Show retry information to user"""
        st.info(f"🔄 Retrying {operation_name} (attempt {attempt}/{max_attempts})")
    
    async def _show_retry_delay(self, operation_name: str, attempt: int, 
                              delay: float, exception: Exception) -> None:
        """Show retry delay with countdown"""
        error_msg = str(exception)[:100] + "..." if len(str(exception)) > 100 else str(exception)
        
        st.warning(f"⚠️ {operation_name} failed: {error_msg}")
        
        if delay > 0:
            placeholder = st.empty()
            
            for remaining in range(int(delay), 0, -1):
                placeholder.info(f"⏳ Retrying in {remaining} seconds...")
                await asyncio.sleep(1)
            
            placeholder.empty()
    
    def get_retry_statistics(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get retry statistics for an operation"""
        if operation_name not in self.retry_histories:
            return None
        
        history = self.retry_histories[operation_name]
        circuit_breaker = self.circuit_breakers.get(operation_name)
        
        stats = {
            "operation_name": operation_name,
            "total_attempts": len(history.attempts),
            "success_rate": history.get_success_rate(),
            "total_duration": history.total_duration,
            "final_success": history.final_success,
            "average_delay": sum(a.delay for a in history.attempts) / len(history.attempts) if history.attempts else 0,
            "circuit_breaker_state": circuit_breaker.get_state_info() if circuit_breaker else None
        }
        
        return stats
    
    def reset_circuit_breaker(self, operation_name: str) -> bool:
        """Manually reset circuit breaker for an operation"""
        if operation_name in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[operation_name]
            circuit_breaker.state = CircuitBreakerState.CLOSED
            circuit_breaker.failure_count = 0
            circuit_breaker.last_failure_time = None
            logger.info(f"Circuit breaker reset for {operation_name}")
            return True
        return False


# Global retry manager instance
retry_manager = EnhancedRetryManager()


# Convenience functions and decorators
def with_retry(operation_name: str, config: Optional[RetryConfig] = None):
    """Decorator for automatic retry functionality"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            return await retry_manager.execute_with_retry(
                operation_name, func, config, *args, **kwargs
            )
        
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(retry_manager.execute_with_retry(
                operation_name, func, config, *args, **kwargs
            ))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def retry_operation(operation_name: str, operation: Callable, 
                         config: Optional[RetryConfig] = None, *args, **kwargs) -> Any:
    """Execute operation with retry logic"""
    if config is None:
        config = RetryConfig()
    
    return await retry_manager.execute_with_retry(operation_name, operation, config, *args, **kwargs)


# Predefined retry configurations
class RetryConfigs:
    """Predefined retry configurations for common scenarios"""
    
    # Quick operations (API calls, database queries)
    QUICK_OPERATION = RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.5,
        max_delay=5.0,
        multiplier=2.0
    )
    
    # Standard operations (file uploads, data processing)
    STANDARD_OPERATION = RetryConfig(
        max_attempts=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=1.0,
        max_delay=30.0,
        multiplier=2.0
    )
    
    # Long operations (large file processing, complex calculations)
    LONG_OPERATION = RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        base_delay=5.0,
        max_delay=60.0,
        circuit_breaker_enabled=False  # Don't use circuit breaker for long operations
    )
    
    # Critical operations (authentication, payment processing)
    CRITICAL_OPERATION = RetryConfig(
        max_attempts=7,
        strategy=RetryStrategy.FIBONACCI_BACKOFF,
        base_delay=1.0,
        max_delay=60.0,
        failure_threshold=3,
        recovery_timeout=120
    )
    
    # Network operations (external API calls)
    NETWORK_OPERATION = RetryConfig(
        max_attempts=5,
        strategy=RetryStrategy.JITTERED_BACKOFF,
        base_delay=2.0,
        max_delay=45.0,
        multiplier=1.5,
        retryable_status_codes=[408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524]
    )


# Retry status display component
class RetryStatusDisplay:
    """Display retry status and statistics to users"""
    
    @staticmethod
    def show_retry_dashboard() -> None:
        """Show retry dashboard with statistics"""
        st.subheader("🔄 Retry Status Dashboard")
        
        # Get all retry statistics
        all_stats = []
        for operation_name in retry_manager.retry_histories.keys():
            stats = retry_manager.get_retry_statistics(operation_name)
            if stats:
                all_stats.append(stats)
        
        if not all_stats:
            st.info("No retry operations recorded yet.")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_operations = len(all_stats)
            st.metric("Total Operations", total_operations)
        
        with col2:
            avg_success_rate = sum(s['success_rate'] for s in all_stats) / len(all_stats)
            st.metric("Average Success Rate", f"{avg_success_rate:.1%}")
        
        with col3:
            total_attempts = sum(s['total_attempts'] for s in all_stats)
            st.metric("Total Attempts", total_attempts)
        
        with col4:
            avg_duration = sum(s['total_duration'] for s in all_stats) / len(all_stats)
            st.metric("Average Duration", f"{avg_duration:.1f}s")
        
        # Detailed statistics table
        st.subheader("Operation Details")
        
        for stats in all_stats:
            with st.expander(f"📊 {stats['operation_name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Attempts:** {stats['total_attempts']}")
                    st.write(f"**Success Rate:** {stats['success_rate']:.1%}")
                    st.write(f"**Duration:** {stats['total_duration']:.1f}s")
                
                with col2:
                    st.write(f"**Average Delay:** {stats['average_delay']:.1f}s")
                    st.write(f"**Final Success:** {'✅' if stats['final_success'] else '❌'}")
                    
                    # Circuit breaker status
                    if stats['circuit_breaker_state']:
                        cb_state = stats['circuit_breaker_state']['state']
                        state_colors = {
                            'closed': '🟢',
                            'open': '🔴',
                            'half_open': '🟡'
                        }
                        st.write(f"**Circuit Breaker:** {state_colors.get(cb_state, '⚪')} {cb_state.upper()}")
    
    @staticmethod
    def show_circuit_breaker_controls() -> None:
        """Show circuit breaker controls"""
        st.subheader("⚡ Circuit Breaker Controls")
        
        # List all circuit breakers
        if not retry_manager.circuit_breakers:
            st.info("No circuit breakers active.")
            return
        
        for operation_name, circuit_breaker in retry_manager.circuit_breakers.items():
            with st.expander(f"🔌 {operation_name}"):
                state_info = circuit_breaker.get_state_info()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    state_colors = {
                        'closed': '🟢 CLOSED',
                        'open': '🔴 OPEN',
                        'half_open': '🟡 HALF-OPEN'
                    }
                    st.write(f"**State:** {state_colors.get(state_info['state'], '⚪ UNKNOWN')}")
                    st.write(f"**Failure Count:** {state_info['failure_count']}")
                    st.write(f"**Can Execute:** {'✅' if state_info['can_execute'] else '❌'}")
                
                with col2:
                    if state_info['last_failure_time']:
                        st.write(f"**Last Failure:** {state_info['last_failure_time'].strftime('%H:%M:%S')}")
                    
                    # Reset button
                    if st.button(f"🔄 Reset", key=f"reset_{operation_name}"):
                        if retry_manager.reset_circuit_breaker(operation_name):
                            st.success(f"Circuit breaker reset for {operation_name}")
                            st.rerun()


# Integration with loading and error handling
async def retry_with_loading_and_error_handling(
    operation_name: str, 
    operation: Callable,
    loading_message: str,
    config: Optional[RetryConfig] = None,
    *args, **kwargs
) -> Any:
    """Execute operation with retry, loading, and error handling"""
    
    from streamlit_loading_components import with_loading_and_error_handling
    
    if config is None:
        config = RetryConfigs.STANDARD_OPERATION
    
    with with_loading_and_error_handling(operation_name, loading_message):
        return await retry_manager.execute_with_retry(
            operation_name, operation, config, *args, **kwargs
        )