"""
Comprehensive tests for the error handling and loading states system
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import httpx

# Import the modules we're testing
from streamlit_error_handler import (
    EnhancedErrorHandler, ErrorCategory, ErrorSeverity, UserFriendlyError,
    ErrorContext, NetworkConnectivityChecker, RateLimitHandler,
    LoadingStateManager, ErrorRecoveryManager, error_handler
)
from streamlit_loading_components import (
    EnhancedLoadingManager, LoadingStyle, LoadingPriority, LoadingOperation,
    LoadingIndicators, LoadingContextManager, loading_manager
)
from streamlit_retry_system import (
    EnhancedRetryManager, RetryConfig, RetryStrategy, CircuitBreaker,
    CircuitBreakerState, RetryDelayCalculator, retry_manager
)
from streamlit_connectivity_monitor import (
    NetworkConnectivityMonitor, ConnectivityStatus, ConnectionQuality,
    ConnectivityCheck, OfflineCapability, connectivity_monitor
)


class TestEnhancedErrorHandler:
    """Test the enhanced error handler"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.error_handler = EnhancedErrorHandler()
    
    def test_create_user_friendly_error_from_exception(self):
        """Test creating user-friendly error from exception"""
        # Test network error
        network_error = httpx.NetworkError("Connection failed")
        user_error = self.error_handler.create_user_friendly_error(
            network_error, ErrorCategory.NETWORK
        )
        
        assert user_error.category == ErrorCategory.NETWORK
        assert user_error.is_retryable == True
        assert "Connection Error" in user_error.title
    
    def test_create_user_friendly_error_from_timeout(self):
        """Test creating user-friendly error from timeout"""
        timeout_error = httpx.TimeoutException("Request timed out")
        user_error = self.error_handler.create_user_friendly_error(timeout_error)
        
        assert user_error.category == ErrorCategory.TIMEOUT
        assert user_error.is_retryable == True
    
    @pytest.mark.asyncio
    async def test_handle_authentication_error(self):
        """Test handling authentication errors"""
        auth_error = UserFriendlyError(
            title="Auth Error",
            message="Authentication failed",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH
        )
        
        context = ErrorContext(operation="login", user_id="test_user")
        
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.rerun') as mock_rerun:
            
            result = await self.error_handler.handle_error(auth_error, context)
            
            # Should attempt recovery for auth errors
            assert result == True  # Recovery attempted
    
    @pytest.mark.asyncio
    async def test_handle_network_error_with_fallback(self):
        """Test handling network errors with fallback data"""
        network_error = UserFriendlyError(
            title="Network Error",
            message="Connection failed",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            is_retryable=True
        )
        
        context = ErrorContext(operation="fetch_data")
        
        # Set up fallback data
        self.error_handler.recovery_manager.set_fallback_data("fetch_data", {"cached": "data"})
        
        with patch('streamlit.warning') as mock_warning:
            result = await self.error_handler.handle_error(network_error, context)
            
            # Should use fallback data
            assert result == True
    
    def test_error_templates(self):
        """Test error message templates"""
        templates = self.error_handler.error_templates
        
        # Check that all error categories have templates
        for category in ErrorCategory:
            assert category in templates
            template = templates[category]
            assert "title" in template
            assert "message" in template
            assert "severity" in template


class TestNetworkConnectivityChecker:
    """Test network connectivity checker"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.checker = NetworkConnectivityChecker()
    
    @pytest.mark.asyncio
    async def test_check_connectivity_success(self):
        """Test successful connectivity check"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await self.checker.check_connectivity()
            
            assert result == True
    
    @pytest.mark.asyncio
    async def test_check_connectivity_failure(self):
        """Test failed connectivity check"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock network error
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.NetworkError("Connection failed")
            
            result = await self.checker.check_connectivity()
            
            assert result == False
    
    def test_get_connectivity_guidance(self):
        """Test connectivity guidance"""
        guidance = self.checker.get_connectivity_guidance()
        
        assert "title" in guidance
        assert "message" in guidance
        assert "suggestions" in guidance
        assert "troubleshooting_steps" in guidance
        assert len(guidance["suggestions"]) > 0
        assert len(guidance["troubleshooting_steps"]) > 0


class TestRateLimitHandler:
    """Test rate limit handler"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.handler = RateLimitHandler()
    
    def test_handle_rate_limit(self):
        """Test rate limit handling"""
        with patch('streamlit.warning') as mock_warning, \
             patch('streamlit.info') as mock_info, \
             patch('time.sleep') as mock_sleep:
            
            self.handler.handle_rate_limit(60, "test_operation")
            
            # Should show warning and info messages
            mock_warning.assert_called_once()
            mock_info.assert_called_once()
    
    def test_is_rate_limited(self):
        """Test rate limit checking"""
        # Initially not rate limited
        assert self.handler.is_rate_limited("test_op") == False
        
        # Set rate limit
        self.handler.rate_limit_info["test_op"] = {
            "retry_after": 60,
            "blocked_until": datetime.now() + timedelta(seconds=60)
        }
        
        # Should be rate limited
        assert self.handler.is_rate_limited("test_op") == True
    
    def test_get_remaining_time(self):
        """Test getting remaining rate limit time"""
        # Set rate limit with 30 seconds remaining
        self.handler.rate_limit_info["test_op"] = {
            "retry_after": 30,
            "blocked_until": datetime.now() + timedelta(seconds=30)
        }
        
        remaining = self.handler.get_remaining_time("test_op")
        assert 25 <= remaining <= 30  # Allow for small timing differences


class TestLoadingStateManager:
    """Test loading state manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = LoadingStateManager()
    
    def test_start_loading(self):
        """Test starting a loading operation"""
        loading_id = self.manager.start_loading("test_op", "Testing...")
        
        assert loading_id in self.manager.active_operations
        operation = self.manager.active_operations[loading_id]
        assert operation.operation == "test_op"
        assert operation.message == "Testing..."
    
    def test_update_progress(self):
        """Test updating loading progress"""
        loading_id = self.manager.start_loading("test_op", "Testing...")
        
        self.manager.update_progress(loading_id, 0.5, "Half done")
        
        operation = self.manager.active_operations[loading_id]
        assert operation.progress == 0.5
        assert operation.message == "Half done"
    
    def test_finish_loading(self):
        """Test finishing a loading operation"""
        loading_id = self.manager.start_loading("test_op", "Testing...")
        
        assert loading_id in self.manager.active_operations
        
        self.manager.finish_loading(loading_id)
        
        assert loading_id not in self.manager.active_operations


class TestEnhancedLoadingManager:
    """Test enhanced loading manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = EnhancedLoadingManager()
    
    def test_create_operation(self):
        """Test creating a loading operation"""
        op_id = self.manager.create_operation(
            "test", "Testing...", 
            LoadingStyle.PROGRESS_BAR, 
            LoadingPriority.HIGH
        )
        
        assert op_id in self.manager.active_operations
        operation = self.manager.active_operations[op_id]
        assert operation.name == "test"
        assert operation.style == LoadingStyle.PROGRESS_BAR
        assert operation.priority == LoadingPriority.HIGH
    
    def test_update_operation(self):
        """Test updating a loading operation"""
        op_id = self.manager.create_operation("test", "Testing...")
        
        self.manager.update_operation(op_id, progress=0.7, message="Almost done")
        
        operation = self.manager.active_operations[op_id]
        assert operation.progress == 0.7
        assert operation.message == "Almost done"
    
    def test_get_active_operations_sorted(self):
        """Test getting active operations sorted by priority"""
        # Create operations with different priorities
        low_id = self.manager.create_operation("low", "Low priority", priority=LoadingPriority.LOW)
        high_id = self.manager.create_operation("high", "High priority", priority=LoadingPriority.HIGH)
        normal_id = self.manager.create_operation("normal", "Normal priority", priority=LoadingPriority.NORMAL)
        
        operations = self.manager.get_active_operations()
        
        # Should be sorted by priority (high, normal, low)
        assert operations[0].priority == LoadingPriority.HIGH
        assert operations[1].priority == LoadingPriority.NORMAL
        assert operations[2].priority == LoadingPriority.LOW


class TestRetryDelayCalculator:
    """Test retry delay calculator"""
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        # Test basic exponential backoff
        delay1 = RetryDelayCalculator.exponential_backoff(1, 1.0, 2.0, 60.0, False)
        delay2 = RetryDelayCalculator.exponential_backoff(2, 1.0, 2.0, 60.0, False)
        delay3 = RetryDelayCalculator.exponential_backoff(3, 1.0, 2.0, 60.0, False)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
    
    def test_exponential_backoff_with_max_delay(self):
        """Test exponential backoff with maximum delay"""
        delay = RetryDelayCalculator.exponential_backoff(10, 1.0, 2.0, 10.0, False)
        assert delay == 10.0  # Should be capped at max_delay
    
    def test_linear_backoff(self):
        """Test linear backoff calculation"""
        delay1 = RetryDelayCalculator.linear_backoff(1, 2.0, 60.0)
        delay2 = RetryDelayCalculator.linear_backoff(2, 2.0, 60.0)
        delay3 = RetryDelayCalculator.linear_backoff(3, 2.0, 60.0)
        
        assert delay1 == 2.0
        assert delay2 == 4.0
        assert delay3 == 6.0
    
    def test_fibonacci_backoff(self):
        """Test Fibonacci backoff calculation"""
        delay1 = RetryDelayCalculator.fibonacci_backoff(1, 1.0, 60.0)
        delay2 = RetryDelayCalculator.fibonacci_backoff(2, 1.0, 60.0)
        delay3 = RetryDelayCalculator.fibonacci_backoff(3, 1.0, 60.0)
        delay4 = RetryDelayCalculator.fibonacci_backoff(4, 1.0, 60.0)
        
        assert delay1 == 1.0  # 1 * fib(1) = 1 * 1
        assert delay2 == 1.0  # 1 * fib(2) = 1 * 1
        assert delay3 == 2.0  # 1 * fib(3) = 1 * 2
        assert delay4 == 3.0  # 1 * fib(4) = 1 * 3


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = RetryConfig(
            failure_threshold=3,
            recovery_timeout=60
        )
        self.circuit_breaker = CircuitBreaker(self.config)
    
    def test_initial_state(self):
        """Test initial circuit breaker state"""
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.circuit_breaker.can_execute() == True
    
    def test_failure_threshold(self):
        """Test circuit breaker opens after failure threshold"""
        # Record failures up to threshold
        for _ in range(self.config.failure_threshold):
            self.circuit_breaker.record_failure()
        
        # Should transition to OPEN
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN
        assert self.circuit_breaker.can_execute() == False
    
    def test_recovery_after_timeout(self):
        """Test circuit breaker recovery after timeout"""
        # Force circuit breaker to OPEN state
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=70)
        
        # Should allow execution after timeout
        assert self.circuit_breaker.can_execute() == True
        assert self.circuit_breaker.state == CircuitBreakerState.HALF_OPEN
    
    def test_success_in_half_open_state(self):
        """Test successful operations in half-open state"""
        # Set to half-open state
        self.circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        self.circuit_breaker.half_open_calls = 0
        
        # Record successful calls
        for _ in range(self.config.half_open_max_calls):
            self.circuit_breaker.record_success()
        
        # Should transition back to CLOSED
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED


class TestEnhancedRetryManager:
    """Test enhanced retry manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = EnhancedRetryManager()
        self.config = RetryConfig(max_attempts=3, base_delay=0.1)
    
    def test_should_retry_on_network_error(self):
        """Test retry decision for network errors"""
        network_error = httpx.NetworkError("Connection failed")
        should_retry = self.manager.should_retry(network_error, None, self.config)
        assert should_retry == True
    
    def test_should_retry_on_status_code(self):
        """Test retry decision for HTTP status codes"""
        should_retry = self.manager.should_retry(Exception(), 500, self.config)
        assert should_retry == True
        
        should_retry = self.manager.should_retry(Exception(), 404, self.config)
        assert should_retry == False
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution with retry"""
        async def successful_operation():
            return "success"
        
        result = await self.manager.execute_with_retry(
            "test_op", successful_operation, self.config
        )
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self):
        """Test eventual success after retries"""
        call_count = 0
        
        async def eventually_successful_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.NetworkError("Temporary failure")
            return "success"
        
        with patch('asyncio.sleep'):  # Speed up test
            result = await self.manager.execute_with_retry(
                "test_op", eventually_successful_operation, self.config
            )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_attempts_exceeded(self):
        """Test failure after max attempts exceeded"""
        async def always_failing_operation():
            raise httpx.NetworkError("Always fails")
        
        with patch('asyncio.sleep'):  # Speed up test
            with pytest.raises(httpx.NetworkError):
                await self.manager.execute_with_retry(
                    "test_op", always_failing_operation, self.config
                )


class TestNetworkConnectivityMonitor:
    """Test network connectivity monitor"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.monitor = NetworkConnectivityMonitor()
    
    @pytest.mark.asyncio
    async def test_check_connectivity_online(self):
        """Test connectivity check when online"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            check = await self.monitor.check_connectivity()
            
            assert check.status == ConnectivityStatus.ONLINE
            assert check.latency is not None
    
    @pytest.mark.asyncio
    async def test_check_connectivity_offline(self):
        """Test connectivity check when offline"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.NetworkError("No connection")
            
            check = await self.monitor.check_connectivity()
            
            assert check.status == ConnectivityStatus.OFFLINE
            assert check.error is not None
    
    def test_register_offline_capability(self):
        """Test registering offline capabilities"""
        capability = OfflineCapability(
            feature_name="test_feature",
            can_work_offline=True,
            offline_message="Test feature works offline"
        )
        
        self.monitor.register_offline_capability(capability)
        
        assert "test_feature" in self.monitor.offline_capabilities
        assert self.monitor.can_use_feature_offline("test_feature") == True
    
    def test_get_connectivity_stats(self):
        """Test getting connectivity statistics"""
        # Add some mock history
        self.monitor.connectivity_history = [
            ConnectivityCheck(datetime.now(), ConnectivityStatus.ONLINE, 0.1),
            ConnectivityCheck(datetime.now(), ConnectivityStatus.ONLINE, 0.2),
            ConnectivityCheck(datetime.now(), ConnectivityStatus.OFFLINE, error="Failed")
        ]
        
        stats = self.monitor.get_connectivity_stats()
        
        assert stats["total_checks"] == 3
        assert stats["online_checks"] == 2
        assert stats["uptime_percentage"] == 66.66666666666667
        assert stats["average_latency"] == 0.15


class TestLoadingContextManager:
    """Test loading context manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.loading_manager = EnhancedLoadingManager()
    
    def test_context_manager_lifecycle(self):
        """Test loading context manager lifecycle"""
        with patch('streamlit.empty') as mock_empty:
            mock_placeholder = Mock()
            mock_empty.return_value = mock_placeholder
            
            with LoadingContextManager(
                self.loading_manager, "test", "Testing...", LoadingStyle.SPINNER
            ) as loading:
                # Should create operation
                assert len(self.loading_manager.active_operations) == 1
                
                # Test progress update
                loading.update_progress(0.5, "Half done")
                
                # Operation should still exist
                assert len(self.loading_manager.active_operations) == 1
            
            # Should clean up after context exit
            assert len(self.loading_manager.active_operations) == 0


class TestIntegration:
    """Integration tests for the complete error handling system"""
    
    @pytest.mark.asyncio
    async def test_error_handling_with_retry_and_loading(self):
        """Test complete integration of error handling, retry, and loading"""
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.NetworkError("Temporary failure")
            return "success"
        
        # Mock Streamlit functions
        with patch('streamlit.spinner'), \
             patch('streamlit.info'), \
             patch('streamlit.warning'), \
             patch('streamlit.success'), \
             patch('asyncio.sleep'):
            
            config = RetryConfig(max_attempts=5, base_delay=0.1)
            result = await retry_manager.execute_with_retry(
                "integration_test", flaky_operation, config
            )
            
            assert result == "success"
            assert call_count == 3
    
    def test_offline_capability_with_error_handling(self):
        """Test offline capability integration with error handling"""
        # Register offline capability
        capability = OfflineCapability(
            feature_name="test_feature",
            can_work_offline=False,
            cached_data_available=True,
            offline_message="Using cached data"
        )
        
        connectivity_monitor.register_offline_capability(capability)
        
        # Simulate offline status
        connectivity_monitor.current_status = ConnectivityStatus.OFFLINE
        
        # Test offline mode handling
        with patch('streamlit.warning') as mock_warning:
            can_use = connectivity_monitor.can_use_feature_offline("test_feature")
            assert can_use == True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])