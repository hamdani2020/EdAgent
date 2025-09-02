"""
Load testing utilities for EdAgent API endpoints
Tests system behavior under high load conditions
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
from unittest.mock import patch, AsyncMock, MagicMock
import uuid
import json

from fastapi.testclient import TestClient
from edagent.api.app import create_app


class LoadTestMetrics:
    """Collect and analyze load test metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.status_codes: List[int] = []
        self.errors: List[str] = []
        self.throughput_data: List[Tuple[float, int]] = []  # (timestamp, requests_completed)
        self.start_time: float = None
        self.end_time: float = None
    
    def start_test(self):
        """Mark the start of the load test"""
        self.start_time = time.time()
    
    def end_test(self):
        """Mark the end of the load test"""
        self.end_time = time.time()
    
    def record_request(self, response_time: float, status_code: int, error: str = None):
        """Record metrics for a single request"""
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        if error:
            self.errors.append(error)
        
        # Record throughput data point
        current_time = time.time()
        completed_requests = len(self.response_times)
        self.throughput_data.append((current_time, completed_requests))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        if not self.response_times:
            return {"error": "No data collected"}
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        total_requests = len(self.response_times)
        
        # Response time statistics
        avg_response_time = statistics.mean(self.response_times)
        median_response_time = statistics.median(self.response_times)
        p95_response_time = self._percentile(self.response_times, 95)
        p99_response_time = self._percentile(self.response_times, 99)
        max_response_time = max(self.response_times)
        min_response_time = min(self.response_times)
        
        # Status code analysis
        success_count = sum(1 for code in self.status_codes if 200 <= code < 300)
        error_count = sum(1 for code in self.status_codes if code >= 400)
        success_rate = success_count / total_requests if total_requests > 0 else 0
        
        # Throughput calculation
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        return {
            "total_requests": total_requests,
            "total_duration_seconds": total_duration,
            "requests_per_second": requests_per_second,
            "success_rate": success_rate,
            "success_count": success_count,
            "error_count": error_count,
            "total_errors": len(self.errors),
            "response_times": {
                "average": avg_response_time,
                "median": median_response_time,
                "min": min_response_time,
                "max": max_response_time,
                "p95": p95_response_time,
                "p99": p99_response_time
            },
            "status_code_distribution": self._get_status_code_distribution(),
            "error_types": self._get_error_distribution()
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_status_code_distribution(self) -> Dict[int, int]:
        """Get distribution of status codes"""
        distribution = {}
        for code in self.status_codes:
            distribution[code] = distribution.get(code, 0) + 1
        return distribution
    
    def _get_error_distribution(self) -> Dict[str, int]:
        """Get distribution of error types"""
        distribution = {}
        for error in self.errors:
            error_type = error.split(':')[0] if ':' in error else error
            distribution[error_type] = distribution.get(error_type, 0) + 1
        return distribution


class LoadTestRunner:
    """Run various load test scenarios"""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def run_constant_load_test(self, 
                              endpoint: str, 
                              method: str = "GET",
                              payload: Dict = None,
                              headers: Dict = None,
                              concurrent_users: int = 10,
                              requests_per_user: int = 10,
                              ramp_up_time: float = 0) -> LoadTestMetrics:
        """Run a constant load test with specified parameters"""
        
        metrics = LoadTestMetrics()
        metrics.start_test()
        
        def make_request(user_id: int, request_id: int) -> Tuple[float, int, str]:
            """Make a single request and return metrics"""
            start_time = time.time()
            error_msg = None
            
            try:
                # Add user identification to payload if provided
                test_payload = payload.copy() if payload else {}
                if payload:
                    test_payload["test_user_id"] = f"load_test_user_{user_id}"
                    test_payload["test_request_id"] = request_id
                
                test_headers = headers.copy() if headers else {}
                
                if method.upper() == "GET":
                    response = self.client.get(endpoint, headers=test_headers)
                elif method.upper() == "POST":
                    response = self.client.post(endpoint, json=test_payload, headers=test_headers)
                elif method.upper() == "PUT":
                    response = self.client.put(endpoint, json=test_payload, headers=test_headers)
                elif method.upper() == "DELETE":
                    response = self.client.delete(endpoint, headers=test_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                status_code = response.status_code
                
            except Exception as e:
                status_code = 500
                error_msg = str(e)
            
            duration = time.time() - start_time
            return duration, status_code, error_msg
        
        # Execute load test with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Submit all requests
            for user_id in range(concurrent_users):
                # Implement ramp-up delay
                if ramp_up_time > 0:
                    delay = (ramp_up_time / concurrent_users) * user_id
                    time.sleep(delay)
                
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    duration, status_code, error_msg = future.result()
                    metrics.record_request(duration, status_code, error_msg)
                except Exception as e:
                    metrics.record_request(0, 500, str(e))
        
        metrics.end_test()
        return metrics
    
    def run_spike_test(self,
                      endpoint: str,
                      method: str = "GET", 
                      payload: Dict = None,
                      headers: Dict = None,
                      baseline_users: int = 5,
                      spike_users: int = 50,
                      spike_duration: float = 10) -> LoadTestMetrics:
        """Run a spike test - sudden increase in load"""
        
        metrics = LoadTestMetrics()
        metrics.start_test()
        
        def make_request_batch(num_users: int, batch_id: str):
            """Make a batch of concurrent requests"""
            batch_futures = []
            
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                for user_id in range(num_users):
                    future = executor.submit(self._single_request, endpoint, method, payload, headers, f"{batch_id}_{user_id}")
                    batch_futures.append(future)
                
                for future in as_completed(batch_futures):
                    try:
                        duration, status_code, error_msg = future.result()
                        metrics.record_request(duration, status_code, error_msg)
                    except Exception as e:
                        metrics.record_request(0, 500, str(e))
        
        # Phase 1: Baseline load
        make_request_batch(baseline_users, "baseline")
        
        # Phase 2: Spike load
        spike_start = time.time()
        while time.time() - spike_start < spike_duration:
            make_request_batch(spike_users, "spike")
            time.sleep(0.1)  # Small delay between spike batches
        
        # Phase 3: Return to baseline
        make_request_batch(baseline_users, "recovery")
        
        metrics.end_test()
        return metrics
    
    def run_stress_test(self,
                       endpoint: str,
                       method: str = "GET",
                       payload: Dict = None,
                       headers: Dict = None,
                       max_users: int = 100,
                       step_size: int = 10,
                       step_duration: float = 30) -> Dict[int, LoadTestMetrics]:
        """Run a stress test - gradually increase load until system breaks"""
        
        results = {}
        
        for num_users in range(step_size, max_users + 1, step_size):
            print(f"Testing with {num_users} concurrent users...")
            
            metrics = self.run_constant_load_test(
                endpoint=endpoint,
                method=method,
                payload=payload,
                headers=headers,
                concurrent_users=num_users,
                requests_per_user=int(step_duration),  # Approximate requests based on duration
                ramp_up_time=2
            )
            
            results[num_users] = metrics
            summary = metrics.get_summary()
            
            print(f"  - Success rate: {summary['success_rate']:.2%}")
            print(f"  - Avg response time: {summary['response_times']['average']:.2f}s")
            print(f"  - Requests/sec: {summary['requests_per_second']:.1f}")
            
            # Stop if system is clearly failing
            if summary['success_rate'] < 0.5 or summary['response_times']['average'] > 10:
                print(f"System breaking point reached at {num_users} users")
                break
            
            time.sleep(1)  # Brief pause between test phases
        
        return results
    
    def _single_request(self, endpoint: str, method: str, payload: Dict, headers: Dict, user_id: str) -> Tuple[float, int, str]:
        """Make a single request (helper method)"""
        start_time = time.time()
        error_msg = None
        
        try:
            test_payload = payload.copy() if payload else {}
            if payload:
                test_payload["test_user_id"] = user_id
            
            test_headers = headers.copy() if headers else {}
            
            if method.upper() == "GET":
                response = self.client.get(endpoint, headers=test_headers)
            elif method.upper() == "POST":
                response = self.client.post(endpoint, json=test_payload, headers=test_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            status_code = response.status_code
            
        except Exception as e:
            status_code = 500
            error_msg = str(e)
        
        duration = time.time() - start_time
        return duration, status_code, error_msg


class TestAPILoadTesting:
    """Load tests for API endpoints"""
    
    @pytest.fixture
    def app(self):
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        return TestClient(app)
    
    @pytest.fixture
    def load_runner(self, client):
        return LoadTestRunner(client)
    
    def test_health_endpoint_load(self, load_runner):
        """Test health endpoint under load"""
        metrics = load_runner.run_constant_load_test(
            endpoint="/health",
            method="GET",
            concurrent_users=20,
            requests_per_user=10
        )
        
        summary = metrics.get_summary()
        
        # Health endpoint should handle load well
        assert summary["success_rate"] > 0.95, f"Health endpoint success rate too low: {summary['success_rate']:.2%}"
        assert summary["response_times"]["average"] < 1.0, f"Health endpoint too slow: {summary['response_times']['average']:.2f}s"
        assert summary["requests_per_second"] > 50, f"Health endpoint throughput too low: {summary['requests_per_second']:.1f} req/s"
        
        print(f"✅ Health endpoint load test: {summary['success_rate']:.2%} success, "
              f"{summary['response_times']['average']:.2f}s avg, {summary['requests_per_second']:.1f} req/s")
    
    def test_conversation_endpoint_load(self, load_runner):
        """Test conversation endpoint under load"""
        # Mock the conversation manager to avoid external dependencies
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
            mock_manager = MagicMock()
            
            async def mock_handle_message(user_id: str, message: str):
                from edagent.models.conversation import ConversationResponse
                # Simulate some processing time
                await asyncio.sleep(0.1)
                return ConversationResponse(
                    message=f"Load test response to: {message[:50]}...",
                    conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    timestamp=time.time(),
                    message_type="response"
                )
            
            mock_manager.handle_message = mock_handle_message
            mock_cm.return_value = mock_manager
            
            metrics = load_runner.run_constant_load_test(
                endpoint="/api/v1/conversations/message",
                method="POST",
                payload={"message": "Load test message"},
                concurrent_users=10,
                requests_per_user=5
            )
            
            summary = metrics.get_summary()
            
            # Conversation endpoint should handle moderate load
            assert summary["success_rate"] > 0.8, f"Conversation endpoint success rate too low: {summary['success_rate']:.2%}"
            assert summary["response_times"]["average"] < 3.0, f"Conversation endpoint too slow: {summary['response_times']['average']:.2f}s"
            
            print(f"✅ Conversation endpoint load test: {summary['success_rate']:.2%} success, "
                  f"{summary['response_times']['average']:.2f}s avg, {summary['requests_per_second']:.1f} req/s")
    
    def test_authentication_endpoint_load(self, load_runner):
        """Test authentication endpoint under load"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            from edagent.database.models import User
            mock_user = User(id="load_test_user")
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            metrics = load_runner.run_constant_load_test(
                endpoint="/api/v1/auth/session",
                method="POST",
                payload={"user_id": "load_test_user", "session_duration_minutes": 60},
                concurrent_users=15,
                requests_per_user=8
            )
            
            summary = metrics.get_summary()
            
            # Auth endpoint should handle load reasonably well
            assert summary["success_rate"] > 0.85, f"Auth endpoint success rate too low: {summary['success_rate']:.2%}"
            assert summary["response_times"]["average"] < 2.0, f"Auth endpoint too slow: {summary['response_times']['average']:.2f}s"
            
            print(f"✅ Authentication endpoint load test: {summary['success_rate']:.2%} success, "
                  f"{summary['response_times']['average']:.2f}s avg, {summary['requests_per_second']:.1f} req/s")
    
    def test_learning_path_endpoint_spike(self, load_runner):
        """Test learning path endpoint with spike load"""
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
            mock_manager = MagicMock()
            
            from edagent.models.learning import LearningPath, Milestone, DifficultyLevel
            mock_milestone = Milestone(
                title="Test Milestone",
                description="Load test milestone",
                skills_to_learn=["test_skill"],
                estimated_duration=time.timedelta(days=7),
                difficulty_level=DifficultyLevel.BEGINNER,
                order_index=0
            )
            
            mock_path = LearningPath(
                title="Load Test Path",
                description="Generated during load test",
                goal="test goal",
                milestones=[mock_milestone],
                estimated_duration=time.timedelta(days=30),
                difficulty_level=DifficultyLevel.BEGINNER,
                target_skills=["test"]
            )
            
            async def mock_generate_path(user_id: str, goal: str):
                # Simulate processing time
                await asyncio.sleep(0.2)
                return mock_path
            
            mock_manager.generate_learning_path = mock_generate_path
            mock_cm.return_value = mock_manager
            
            metrics = load_runner.run_spike_test(
                endpoint="/api/v1/learning/path",
                method="POST",
                payload={"goal": "learn programming"},
                baseline_users=3,
                spike_users=15,
                spike_duration=5
            )
            
            summary = metrics.get_summary()
            
            # Learning path endpoint should survive spike
            assert summary["success_rate"] > 0.7, f"Learning path spike test success rate too low: {summary['success_rate']:.2%}"
            assert summary["response_times"]["p95"] < 5.0, f"Learning path P95 response time too high: {summary['response_times']['p95']:.2f}s"
            
            print(f"✅ Learning path spike test: {summary['success_rate']:.2%} success, "
                  f"P95: {summary['response_times']['p95']:.2f}s, Max: {summary['response_times']['max']:.2f}s")
    
    def test_database_operations_stress(self, load_runner):
        """Test database operations under stress"""
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            from edagent.database.models import User
            mock_user = User(id="stress_test_user")
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Simulate database latency
            async def slow_commit():
                await asyncio.sleep(0.05)  # 50ms database latency
            
            mock_session.commit = slow_commit
            
            results = load_runner.run_stress_test(
                endpoint="/api/v1/auth/session",
                method="POST",
                payload={"user_id": "stress_test_user", "session_duration_minutes": 60},
                max_users=30,
                step_size=5,
                step_duration=10
            )
            
            # Analyze stress test results
            breaking_point = None
            for num_users, metrics in results.items():
                summary = metrics.get_summary()
                if summary["success_rate"] < 0.8 or summary["response_times"]["average"] > 3.0:
                    breaking_point = num_users
                    break
            
            if breaking_point:
                print(f"✅ Database stress test: Breaking point at {breaking_point} concurrent users")
            else:
                print(f"✅ Database stress test: System stable up to {max(results.keys())} users")
            
            # System should handle at least 10 concurrent users
            assert 10 in results, "System should handle at least 10 concurrent users"
            ten_user_summary = results[10].get_summary()
            assert ten_user_summary["success_rate"] > 0.9, "System should be stable with 10 users"
    
    def test_memory_leak_detection(self, load_runner):
        """Test for memory leaks under sustained load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run sustained load test
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
            mock_manager = MagicMock()
            
            async def mock_handle_message(user_id: str, message: str):
                from edagent.models.conversation import ConversationResponse
                return ConversationResponse(
                    message="Memory test response",
                    conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    timestamp=time.time(),
                    message_type="response"
                )
            
            mock_manager.handle_message = mock_handle_message
            mock_cm.return_value = mock_manager
            
            # Run multiple rounds of load testing
            for round_num in range(3):
                metrics = load_runner.run_constant_load_test(
                    endpoint="/api/v1/conversations/message",
                    method="POST",
                    payload={"message": f"Memory test round {round_num}"},
                    concurrent_users=10,
                    requests_per_user=20
                )
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                print(f"Round {round_num + 1}: Memory usage: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # Memory shouldn't grow excessively
                assert memory_increase < 200, f"Excessive memory growth: {memory_increase:.1f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"✅ Memory leak test: Total increase {total_increase:.1f}MB over sustained load")
        
        # Total memory increase should be reasonable
        assert total_increase < 150, f"Possible memory leak detected: {total_increase:.1f}MB increase"


if __name__ == "__main__":
    # Run load tests
    pytest.main([__file__, "-v", "--tb=short"])