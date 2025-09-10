"""
Comprehensive Error Handling and Loading States Demo
Demonstrates all features of the enhanced error handling system.
"""

import streamlit as st
import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Optional, Any
import httpx

# Import all error handling components
from streamlit_error_handler import (
    error_handler, ErrorCategory, ErrorContext, UserFriendlyError, 
    ErrorSeverity, error_context
)
from streamlit_loading_components import (
    show_loading, LoadingStyle, LoadingPriority, show_progress_loading,
    show_skeleton_loading, with_loading, loading_steps, APILoadingComponents
)
from streamlit_retry_system import (
    retry_manager, RetryConfig, RetryConfigs, with_retry, 
    RetryStatusDisplay, retry_with_loading_and_error_handling
)
from streamlit_connectivity_monitor import (
    connectivity_monitor, connectivity_ui, ConnectivityStatus,
    require_online_connection, with_offline_fallback
)


def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Error Handling Demo",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Enhanced Error Handling & Loading States Demo")
    st.markdown("Comprehensive demonstration of error handling, loading states, retry mechanisms, and connectivity monitoring.")
    
    # Show connectivity status
    connectivity_ui.show_connectivity_status("header")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔄 Loading States", "❌ Error Handling", "🔁 Retry System", 
        "🌐 Connectivity", "📊 Monitoring", "🧪 Integration Tests"
    ])
    
    with tab1:
        demo_loading_states()
    
    with tab2:
        demo_error_handling()
    
    with tab3:
        demo_retry_system()
    
    with tab4:
        demo_connectivity_monitoring()
    
    with tab5:
        demo_monitoring_dashboard()
    
    with tab6:
        demo_integration_tests()


def demo_loading_states():
    """Demonstrate different loading states"""
    st.header("🔄 Loading States Demo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Basic Loading Indicators")
        
        if st.button("Spinner Loading", key="spinner_demo"):
            with show_loading("spinner_demo", "Processing with spinner..."):
                time.sleep(2)
            st.success("Spinner loading completed!")
        
        if st.button("Progress Bar Loading", key="progress_demo"):
            steps = ["Initializing", "Processing", "Finalizing", "Complete"]
            with show_progress_loading("progress_demo", "Multi-step process", steps, 8) as loading:
                for i, step in enumerate(steps):
                    loading.update_progress(i / len(steps), f"Step {i+1}: {step}", i)
                    time.sleep(1)
                loading.update_progress(1.0, "Process completed!", len(steps) - 1)
            st.success("Progress loading completed!")
        
        if st.button("Skeleton Loading", key="skeleton_demo"):
            st.write("**Loading content...**")
            show_skeleton_loading(5)
            time.sleep(2)
            st.success("Content loaded!")
    
    with col2:
        st.subheader("API Loading Components")
        
        if st.button("API Call Loading", key="api_demo"):
            with APILoadingComponents.api_call_loading("User Data", "/api/users"):
                time.sleep(3)
            st.success("API call completed!")
        
        if st.button("Data Loading", key="data_demo"):
            with APILoadingComponents.data_loading("User Profiles", 150):
                time.sleep(2)
            st.success("Data loading completed!")
        
        if st.button("File Upload Loading", key="upload_demo"):
            with APILoadingComponents.file_upload_loading("document.pdf", 2048000):
                time.sleep(4)
            st.success("File upload completed!")
    
    st.subheader("Decorator Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Decorated Function", key="decorated_demo"):
            result = decorated_function_demo()
            st.success(f"Result: {result}")
    
    with col2:
        if st.button("Async Decorated Function", key="async_decorated_demo"):
            result = asyncio.run(async_decorated_function_demo())
            st.success(f"Result: {result}")


@with_loading("decorated_demo", "Processing decorated function...", LoadingStyle.SPINNER)
def decorated_function_demo() -> str:
    """Demo function with loading decorator"""
    time.sleep(2)
    return "Decorated function completed"


@loading_steps("Initializing", "Processing data", "Generating result", "Finalizing")
@with_loading("async_decorated_demo", "Processing async function...", LoadingStyle.PROGRESS_BAR, show_progress=True)
async def async_decorated_function_demo() -> str:
    """Demo async function with loading decorator and steps"""
    await asyncio.sleep(1)
    return "Async decorated function completed"


def demo_error_handling():
    """Demonstrate error handling capabilities"""
    st.header("❌ Error Handling Demo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Error Types")
        
        error_type = st.selectbox(
            "Select error type to simulate:",
            ["Network Error", "Authentication Error", "Validation Error", 
             "Rate Limit Error", "Server Error", "Timeout Error"]
        )
        
        if st.button("Simulate Error", key="error_sim"):
            simulate_error(error_type)
    
    with col2:
        st.subheader("Error Recovery")
        
        if st.button("Test Error Recovery", key="recovery_demo"):
            test_error_recovery()
        
        if st.button("Test Fallback Data", key="fallback_demo"):
            test_fallback_data()
    
    st.subheader("Context Manager Demo")
    
    if st.button("Error Context Manager", key="context_demo"):
        with error_context("demo_operation", show_loading=True, loading_message="Testing error context..."):
            time.sleep(1)
            if random.choice([True, False]):
                raise Exception("Random error for demonstration")
        st.success("Operation completed successfully!")


def simulate_error(error_type: str):
    """Simulate different types of errors"""
    error_mapping = {
        "Network Error": (ErrorCategory.NETWORK, "Connection failed"),
        "Authentication Error": (ErrorCategory.AUTHENTICATION, "Invalid credentials"),
        "Validation Error": (ErrorCategory.VALIDATION, "Invalid input data"),
        "Rate Limit Error": (ErrorCategory.RATE_LIMIT, "Too many requests"),
        "Server Error": (ErrorCategory.SERVER, "Internal server error"),
        "Timeout Error": (ErrorCategory.TIMEOUT, "Request timed out")
    }
    
    category, message = error_mapping[error_type]
    
    user_error = UserFriendlyError(
        title=f"Simulated {error_type}",
        message=message,
        category=category,
        severity=ErrorSeverity.MEDIUM,
        is_retryable=category in [ErrorCategory.NETWORK, ErrorCategory.SERVER, ErrorCategory.TIMEOUT],
        suggested_actions=[
            "Try again in a moment",
            "Check your connection",
            "Contact support if issue persists"
        ]
    )
    
    context = ErrorContext(
        operation="error_simulation",
        additional_data={"simulated_error": error_type}
    )
    
    asyncio.run(error_handler.handle_error(user_error, context))


def test_error_recovery():
    """Test error recovery mechanisms"""
    try:
        # Simulate an operation that might fail
        if random.choice([True, False]):
            raise httpx.NetworkError("Simulated network failure")
        
        st.success("✅ Operation succeeded without errors!")
    
    except Exception as e:
        context = ErrorContext(operation="recovery_test")
        
        # Set up fallback data
        error_handler.recovery_manager.set_fallback_data("recovery_test", {
            "message": "Using cached data due to network issues",
            "timestamp": datetime.now().isoformat()
        })
        
        # Handle error (will attempt recovery)
        asyncio.run(error_handler.handle_error(e, context))


def test_fallback_data():
    """Test fallback data functionality"""
    fallback_data = error_handler.recovery_manager.get_fallback_data("recovery_test")
    
    if fallback_data:
        st.info("📦 Using fallback data:")
        st.json(fallback_data)
    else:
        st.warning("No fallback data available. Run 'Test Error Recovery' first.")


def demo_retry_system():
    """Demonstrate retry system capabilities"""
    st.header("🔁 Retry System Demo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retry Configurations")
        
        config_type = st.selectbox(
            "Select retry configuration:",
            ["Quick Operation", "Standard Operation", "Long Operation", 
             "Critical Operation", "Network Operation"]
        )
        
        config_mapping = {
            "Quick Operation": RetryConfigs.QUICK_OPERATION,
            "Standard Operation": RetryConfigs.STANDARD_OPERATION,
            "Long Operation": RetryConfigs.LONG_OPERATION,
            "Critical Operation": RetryConfigs.CRITICAL_OPERATION,
            "Network Operation": RetryConfigs.NETWORK_OPERATION
        }
        
        selected_config = config_mapping[config_type]
        
        # Show config details
        st.write(f"**Max Attempts:** {selected_config.max_attempts}")
        st.write(f"**Strategy:** {selected_config.strategy.value}")
        st.write(f"**Base Delay:** {selected_config.base_delay}s")
        st.write(f"**Max Delay:** {selected_config.max_delay}s")
        
        if st.button("Test Retry Operation", key="retry_demo"):
            asyncio.run(test_retry_operation(selected_config))
    
    with col2:
        st.subheader("Circuit Breaker Demo")
        
        if st.button("Test Circuit Breaker", key="circuit_demo"):
            asyncio.run(test_circuit_breaker())
        
        if st.button("Reset Circuit Breakers", key="reset_circuit"):
            # Reset all circuit breakers
            for operation_name in list(retry_manager.circuit_breakers.keys()):
                retry_manager.reset_circuit_breaker(operation_name)
            st.success("All circuit breakers reset!")
    
    st.subheader("Retry Statistics")
    RetryStatusDisplay.show_retry_dashboard()


async def test_retry_operation(config: RetryConfig):
    """Test retry operation with specified configuration"""
    attempt_count = 0
    
    async def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        
        # Fail first few attempts, then succeed
        if attempt_count < 3:
            raise httpx.NetworkError(f"Simulated failure (attempt {attempt_count})")
        
        return f"Success after {attempt_count} attempts!"
    
    try:
        result = await retry_manager.execute_with_retry(
            "retry_demo", flaky_operation, config
        )
        st.success(f"✅ {result}")
    
    except Exception as e:
        st.error(f"❌ Operation failed after all retries: {e}")


async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    async def failing_operation():
        raise httpx.NetworkError("Persistent failure")
    
    config = RetryConfig(
        max_attempts=2,
        failure_threshold=3,
        recovery_timeout=30
    )
    
    # Trigger multiple failures to open circuit breaker
    for i in range(5):
        try:
            await retry_manager.execute_with_retry(
                "circuit_breaker_test", failing_operation, config
            )
        except Exception:
            pass  # Expected to fail
    
    # Show circuit breaker status
    RetryStatusDisplay.show_circuit_breaker_controls()


def demo_connectivity_monitoring():
    """Demonstrate connectivity monitoring"""
    st.header("🌐 Connectivity Monitoring Demo")
    
    # Show detailed connectivity dashboard
    connectivity_ui.show_connectivity_dashboard()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Offline Capabilities")
        
        feature_name = st.selectbox(
            "Test offline capability for:",
            ["chat", "assessments", "learning_paths", "user_profile", "analytics"]
        )
        
        if st.button("Test Offline Mode", key="offline_demo"):
            test_offline_capability(feature_name)
    
    with col2:
        st.subheader("Connection Quality")
        
        quality = connectivity_monitor.get_connection_quality()
        if quality:
            st.write(f"**Current Quality:** {quality.value.title()}")
        else:
            st.write("**Current Quality:** Unknown")
        
        stats = connectivity_monitor.get_connectivity_stats()
        st.metric("Uptime", f"{stats['uptime_percentage']:.1f}%")
        
        if stats['average_latency']:
            st.metric("Average Latency", f"{stats['average_latency']*1000:.0f}ms")


def test_offline_capability(feature_name: str):
    """Test offline capability for a feature"""
    can_use_offline = connectivity_ui.show_offline_mode_info(feature_name)
    
    if can_use_offline:
        st.success(f"✅ {feature_name} can be used offline!")
    else:
        st.error(f"❌ {feature_name} requires internet connection")


def demo_monitoring_dashboard():
    """Show monitoring and statistics dashboard"""
    st.header("📊 Monitoring Dashboard")
    
    # Retry statistics
    st.subheader("🔁 Retry Statistics")
    RetryStatusDisplay.show_retry_dashboard()
    
    # Circuit breaker controls
    st.subheader("⚡ Circuit Breaker Status")
    RetryStatusDisplay.show_circuit_breaker_controls()
    
    # Connectivity statistics
    st.subheader("🌐 Connectivity Statistics")
    connectivity_ui.show_connectivity_dashboard()


def demo_integration_tests():
    """Demonstrate integration of all systems"""
    st.header("🧪 Integration Tests")
    
    st.subheader("Complete Error Handling Pipeline")
    
    if st.button("Test Complete Pipeline", key="pipeline_demo"):
        asyncio.run(test_complete_pipeline())
    
    st.subheader("Stress Test")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_operations = st.slider("Number of operations:", 1, 20, 5)
        
        if st.button("Run Stress Test", key="stress_demo"):
            asyncio.run(run_stress_test(num_operations))
    
    with col2:
        st.subheader("Performance Metrics")
        
        if st.button("Show Performance Stats", key="perf_demo"):
            show_performance_stats()


async def test_complete_pipeline():
    """Test the complete error handling pipeline"""
    
    async def complex_operation():
        """Simulate a complex operation with multiple failure points"""
        
        # Step 1: Check connectivity
        if not connectivity_monitor.is_online():
            raise ConnectionError("No internet connection")
        
        # Step 2: Simulate random failure
        if random.random() < 0.3:
            raise httpx.NetworkError("Random network failure")
        
        # Step 3: Simulate rate limiting
        if random.random() < 0.2:
            raise httpx.HTTPStatusError(
                "Rate limited", 
                request=None, 
                response=type('Response', (), {'status_code': 429})()
            )
        
        # Step 4: Success
        await asyncio.sleep(1)
        return "Complex operation completed successfully!"
    
    # Execute with full error handling pipeline
    try:
        result = await retry_with_loading_and_error_handling(
            "complex_pipeline_test",
            complex_operation,
            "Executing complex operation...",
            RetryConfigs.STANDARD_OPERATION
        )
        
        st.success(f"✅ Pipeline test completed: {result}")
    
    except Exception as e:
        st.error(f"❌ Pipeline test failed: {e}")


async def run_stress_test(num_operations: int):
    """Run stress test with multiple concurrent operations"""
    
    async def stress_operation(operation_id: int):
        """Individual stress test operation"""
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        if random.random() < 0.3:
            raise httpx.NetworkError(f"Stress test failure {operation_id}")
        
        return f"Operation {operation_id} completed"
    
    # Run operations concurrently
    tasks = []
    for i in range(num_operations):
        task = retry_manager.execute_with_retry(
            f"stress_test_{i}",
            lambda op_id=i: stress_operation(op_id),
            RetryConfigs.QUICK_OPERATION
        )
        tasks.append(task)
    
    # Wait for all operations to complete
    with show_loading("stress_test", f"Running {num_operations} concurrent operations..."):
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Show results
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = len(results) - successes
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Successful Operations", successes)
    with col2:
        st.metric("Failed Operations", failures)
    
    st.write(f"**Success Rate:** {successes/len(results)*100:.1f}%")


def show_performance_stats():
    """Show performance statistics"""
    
    # Get retry statistics
    all_stats = []
    for operation_name in retry_manager.retry_histories.keys():
        stats = retry_manager.get_retry_statistics(operation_name)
        if stats:
            all_stats.append(stats)
    
    if all_stats:
        import pandas as pd
        
        df = pd.DataFrame(all_stats)
        
        st.subheader("📈 Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_success_rate = df['success_rate'].mean()
            st.metric("Average Success Rate", f"{avg_success_rate:.1%}")
        
        with col2:
            avg_duration = df['total_duration'].mean()
            st.metric("Average Duration", f"{avg_duration:.2f}s")
        
        with col3:
            total_operations = len(df)
            st.metric("Total Operations", total_operations)
        
        # Performance chart
        if len(df) > 1:
            import plotly.express as px
            
            fig = px.scatter(
                df, 
                x='total_duration', 
                y='success_rate',
                size='total_attempts',
                hover_data=['operation_name'],
                title="Operation Performance"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No performance data available. Run some operations first.")


if __name__ == "__main__":
    main()