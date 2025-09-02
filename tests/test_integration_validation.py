"""
Integration test validation - ensures the integration test suite itself works correctly
Meta-tests that validate the testing infrastructure
"""

import pytest
import asyncio
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import subprocess
import sys

from tests.test_data_management import TestDataFactory, TestDatabaseManager, MockServiceManager
from tests.test_load_testing import LoadTestRunner, LoadTestMetrics
from tests.run_integration_tests import IntegrationTestRunner, TestSuite


class TestIntegrationTestInfrastructure:
    """Test the integration test infrastructure itself"""
    
    def test_test_data_factory_completeness(self):
        """Ensure test data factory can create all necessary test objects"""
        factory = TestDataFactory()
        
        # Test user context creation with various parameters
        beginner_context = factory.create_user_context(skill_level="beginner")
        intermediate_context = factory.create_user_context(skill_level="intermediate")
        advanced_context = factory.create_user_context(skill_level="advanced")
        
        assert beginner_context.user_id != intermediate_context.user_id
        assert len(beginner_context.current_skills) < len(advanced_context.current_skills)
        
        # Test learning path creation
        web_dev_path = factory.create_learning_path(goal="become a web developer")
        data_sci_path = factory.create_learning_path(goal="become a data scientist")
        
        assert web_dev_path.goal != data_sci_path.goal
        assert len(web_dev_path.milestones) > 0
        assert len(data_sci_path.milestones) > 0
        
        # Test skill assessment creation
        assessment = factory.create_skill_assessment(user_id="test_user_123")
        assert assessment.skill_area is not None
        assert assessment.user_id == "test_user_123"
        assert len(assessment.strengths) > 0
        assert len(assessment.weaknesses) > 0
        assert len(assessment.recommendations) > 0
        
        # Test conversation history creation
        history = factory.create_conversation_history("test_user", num_messages=3)
        assert len(history) == 6  # 3 user + 3 assistant messages
        
        # Test content recommendations
        recommendations = factory.create_content_recommendations()
        assert len(recommendations) > 0
        assert all(rec.title for rec in recommendations)
        assert all(rec.url for rec in recommendations)
    
    def test_database_manager_tracking(self):
        """Test database manager properly tracks test data for cleanup"""
        manager = TestDatabaseManager()
        
        # Track various types of test data
        manager.track_user("user_1")
        manager.track_user("user_2")
        manager.track_session("session_1")
        manager.track_conversation("conv_1")
        manager.track_learning_path("path_1")
        manager.track_assessment("assessment_1")
        
        # Verify tracking
        summary = manager.get_cleanup_summary()
        assert summary["users"] == 2
        assert summary["sessions"] == 1
        assert summary["conversations"] == 1
        assert summary["learning_paths"] == 1
        assert summary["assessments"] == 1
        
        # Test temp database creation
        temp_db = manager.create_temp_database()
        assert os.path.exists(temp_db)
        assert temp_db.endswith('.db')
        
        # Cleanup should remove temp files
        asyncio.run(manager.cleanup_all())
        assert not os.path.exists(temp_db)
    
    def test_mock_service_manager_setup(self):
        """Test mock service manager creates realistic mocks"""
        manager = MockServiceManager()
        
        # Set up AI service mock
        ai_mock = manager.setup_ai_service_mock(response_delay=0.01)
        assert ai_mock is not None
        
        # Test AI mock behavior
        async def test_ai_mock():
            response = await ai_mock.generate_response("Hello", None)
            assert isinstance(response, str)
            assert len(response) > 0
            
            assessment = await ai_mock.assess_skills(["I know Python"])
            assert assessment is not None
            assert hasattr(assessment, 'skill_area')
            
            path = await ai_mock.create_learning_path("learn programming", {})
            assert path is not None
            assert hasattr(path, 'title')
        
        asyncio.run(test_ai_mock())
        
        # Set up content recommender mock
        content_mock = manager.setup_content_recommender_mock()
        assert content_mock is not None
        
        # Test content mock behavior
        async def test_content_mock():
            recommendations = await content_mock.get_recommendations("python", "beginner")
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
        
        asyncio.run(test_content_mock())
        
        # Set up user context manager mock
        context_mock = manager.setup_user_context_manager_mock()
        assert context_mock is not None
        
        # Test context mock behavior
        async def test_context_mock():
            context = await context_mock.get_user_context("test_user")
            assert context is not None
            assert hasattr(context, 'user_id')
        
        asyncio.run(test_context_mock())
    
    def test_load_test_metrics_collection(self):
        """Test load test metrics collection and analysis"""
        metrics = LoadTestMetrics()
        
        # Record some test data
        metrics.start_test()
        time.sleep(0.01)  # Small delay
        
        # Simulate various response times and status codes
        test_data = [
            (0.1, 200),
            (0.2, 200),
            (0.15, 200),
            (0.3, 200),
            (1.0, 500),  # Slow error
            (0.12, 200),
            (0.18, 200),
            (2.0, 503),  # Very slow error
            (0.14, 200),
            (0.16, 200)
        ]
        
        for response_time, status_code in test_data:
            error = "Server error" if status_code >= 500 else None
            metrics.record_request(response_time, status_code, error)
        
        metrics.end_test()
        
        # Analyze metrics
        summary = metrics.get_summary()
        
        assert summary["total_requests"] == 10
        assert summary["success_count"] == 8  # 200 status codes
        assert summary["error_count"] == 2   # 500+ status codes
        assert summary["success_rate"] == 0.8
        assert summary["total_errors"] == 2
        
        # Check response time statistics
        response_times = summary["response_times"]
        assert response_times["min"] == 0.1
        assert response_times["max"] == 2.0
        assert 0.1 < response_times["average"] < 0.5  # Should be reasonable
        assert response_times["p95"] > response_times["median"]
        
        # Check status code distribution
        status_dist = summary["status_code_distribution"]
        assert status_dist[200] == 8
        assert status_dist[500] == 1
        assert status_dist[503] == 1
    
    def test_integration_test_runner_dependency_resolution(self):
        """Test that the integration test runner properly resolves dependencies"""
        runner = IntegrationTestRunner()
        
        # Create test suites with dependencies
        test_suites = [
            TestSuite("suite_a", "test_a.py", "Test A", 30, []),
            TestSuite("suite_b", "test_b.py", "Test B", 30, ["suite_a"]),
            TestSuite("suite_c", "test_c.py", "Test C", 30, ["suite_a", "suite_b"]),
            TestSuite("suite_d", "test_d.py", "Test D", 30, ["suite_a"]),
        ]
        
        # Resolve dependencies
        execution_order = runner._resolve_dependencies(test_suites)
        
        # Verify order respects dependencies
        suite_names = [suite.name for suite in execution_order]
        
        # suite_a should come first (no dependencies)
        assert suite_names.index("suite_a") == 0
        
        # suite_b should come after suite_a
        assert suite_names.index("suite_b") > suite_names.index("suite_a")
        
        # suite_c should come after both suite_a and suite_b
        assert suite_names.index("suite_c") > suite_names.index("suite_a")
        assert suite_names.index("suite_c") > suite_names.index("suite_b")
        
        # suite_d should come after suite_a
        assert suite_names.index("suite_d") > suite_names.index("suite_a")
    
    def test_integration_test_runner_circular_dependency_detection(self):
        """Test that circular dependencies are detected"""
        runner = IntegrationTestRunner()
        
        # Create test suites with circular dependency
        test_suites = [
            TestSuite("suite_a", "test_a.py", "Test A", 30, ["suite_b"]),
            TestSuite("suite_b", "test_b.py", "Test B", 30, ["suite_a"]),
        ]
        
        # Should raise ValueError for circular dependency
        with pytest.raises(ValueError, match="Circular dependency"):
            runner._resolve_dependencies(test_suites)
    
    def test_performance_threshold_validation(self):
        """Test that performance thresholds are properly validated"""
        from fastapi.testclient import TestClient
        from edagent.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        runner = LoadTestRunner(client)
        
        # Test health endpoint performance
        metrics = runner.run_constant_load_test(
            endpoint="/health",
            method="GET",
            concurrent_users=5,
            requests_per_user=10
        )
        
        summary = metrics.get_summary()
        
        # Health endpoint should meet performance thresholds
        assert summary["success_rate"] > 0.95, "Health endpoint success rate below threshold"
        assert summary["response_times"]["average"] < 1.0, "Health endpoint too slow"
        assert summary["requests_per_second"] > 10, "Health endpoint throughput too low"
    
    def test_test_isolation_and_cleanup(self):
        """Test that tests are properly isolated and cleaned up"""
        manager = TestDatabaseManager()
        
        # Simulate test execution with data creation
        user_ids = []
        for i in range(5):
            user_id = f"test_user_{i}"
            manager.track_user(user_id)
            user_ids.append(user_id)
        
        # Verify data is tracked
        assert len(manager.created_users) == 5
        
        # Simulate cleanup
        asyncio.run(manager.cleanup_all())
        
        # Verify cleanup
        assert len(manager.created_users) == 0
    
    def test_mock_service_realistic_behavior(self):
        """Test that mock services behave realistically"""
        manager = MockServiceManager()
        ai_mock = manager.setup_ai_service_mock(response_delay=0.01)
        
        async def test_realistic_behavior():
            # Test contextual responses
            hello_response = await ai_mock.generate_response("Hello", None)
            python_response = await ai_mock.generate_response("I want to learn Python", None)
            
            assert "hello" in hello_response.lower() or "hi" in hello_response.lower()
            assert "python" in python_response.lower()
            
            # Test skill assessment logic
            beginner_responses = ["No", "I don't know", "Never tried"]
            intermediate_responses = ["Yes", "I know some", "I have experience"]
            
            beginner_assessment = await ai_mock.assess_skills(beginner_responses)
            intermediate_assessment = await ai_mock.assess_skills(intermediate_responses)
            
            # Beginner should have lower confidence than intermediate
            assert beginner_assessment.confidence_score < intermediate_assessment.confidence_score
            
            # Test learning path adaptation
            beginner_path = await ai_mock.create_learning_path("learn programming", {})
            experienced_path = await ai_mock.create_learning_path("learn programming", {"Python": "intermediate"})
            
            # Paths should be different based on existing skills
            assert beginner_path.difficulty_level != experienced_path.difficulty_level or \
                   len(beginner_path.milestones) != len(experienced_path.milestones)
        
        asyncio.run(test_realistic_behavior())
    
    def test_error_handling_in_test_infrastructure(self):
        """Test error handling in the test infrastructure"""
        
        # Test load test runner error handling
        from fastapi.testclient import TestClient
        from edagent.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        runner = LoadTestRunner(client)
        
        # Test with invalid endpoint
        metrics = runner.run_constant_load_test(
            endpoint="/nonexistent-endpoint",
            method="GET",
            concurrent_users=2,
            requests_per_user=3
        )
        
        summary = metrics.get_summary()
        
        # Should handle errors gracefully
        assert summary["total_requests"] == 6  # 2 users * 3 requests
        assert summary["error_count"] > 0     # Should have errors
        assert summary["success_rate"] < 1.0  # Not all successful
        
        # Test database manager error handling
        manager = TestDatabaseManager()
        
        # Test cleanup with non-existent temp file
        manager.temp_files.append("/nonexistent/file.db")
        
        # Should not raise exception
        asyncio.run(manager.cleanup_all())
    
    def test_configuration_loading_and_validation(self):
        """Test that test configuration is properly loaded and validated"""
        import yaml
        
        config_path = Path(__file__).parent / "integration_test_config.yaml"
        
        # Verify config file exists and is valid YAML
        assert config_path.exists(), "Integration test config file not found"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify required sections exist
        required_sections = [
            "test_environments",
            "performance_thresholds",
            "load_test_scenarios",
            "test_data_settings",
            "test_execution"
        ]
        
        for section in required_sections:
            assert section in config, f"Missing required config section: {section}"
        
        # Verify performance thresholds are reasonable
        thresholds = config["performance_thresholds"]
        assert thresholds["response_times"]["health_endpoint"] < 2.0
        assert thresholds["success_rates"]["minimum_success_rate"] > 0.5
        assert thresholds["concurrent_users"]["light_load"] > 0
        
        # Verify load test scenarios are configured
        scenarios = config["load_test_scenarios"]
        assert "smoke_test" in scenarios
        assert "load_test" in scenarios
        assert scenarios["smoke_test"]["duration"] > 0
        assert scenarios["load_test"]["concurrent_users"] > 0


class TestIntegrationTestExecution:
    """Test actual execution of integration tests"""
    
    def test_integration_test_runner_execution(self):
        """Test that the integration test runner can execute tests"""
        runner = IntegrationTestRunner()
        
        # Create a simple test suite that should pass
        simple_suite = TestSuite(
            name="simple_test",
            file_path="tests/test_data_management.py::TestTestDataManagement::test_user_context_factory",
            description="Simple test that should pass",
            estimated_duration=10,
            dependencies=[]
        )
        
        # Run the test
        success = runner._run_single_suite(simple_suite, verbose=False)
        
        # Verify execution
        assert simple_suite.result is not None
        assert simple_suite.duration > 0
        
        # If the test infrastructure is working, this should pass
        if success:
            assert simple_suite.result == "passed"
        else:
            # If it failed, we should have error output
            assert simple_suite.error_output is not None
    
    def test_test_report_generation(self):
        """Test that test reports are properly generated"""
        runner = IntegrationTestRunner()
        
        # Simulate some test results
        runner.start_time = time.time() - 100  # 100 seconds ago
        runner.end_time = time.time()
        
        # Create mock test suites with results
        runner.test_suites = [
            TestSuite("test_1", "test1.py", "Test 1", 30),
            TestSuite("test_2", "test2.py", "Test 2", 45),
            TestSuite("test_3", "test3.py", "Test 3", 60),
        ]
        
        # Set results
        runner.test_suites[0].result = "passed"
        runner.test_suites[0].duration = 25
        runner.test_suites[1].result = "failed"
        runner.test_suites[1].duration = 50
        runner.test_suites[2].result = "passed"
        runner.test_suites[2].duration = 55
        
        # Generate report
        report = runner._generate_report()
        
        # Verify report structure
        assert "timestamp" in report
        assert "total_duration" in report
        assert "summary" in report
        assert "suite_results" in report
        
        # Verify summary
        summary = report["summary"]
        assert summary["total_suites"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == 2/3
        
        # Verify suite results
        suite_results = report["suite_results"]
        assert len(suite_results) == 3
        
        for result in suite_results:
            assert "name" in result
            assert "result" in result
            assert "duration" in result
            assert "efficiency" in result
    
    def test_end_to_end_test_runner_functionality(self):
        """Test the complete test runner functionality"""
        # This is a meta-test that verifies the test runner itself works
        
        # Test listing available suites
        runner = IntegrationTestRunner()
        
        # Should have test suites defined
        assert len(runner.test_suites) > 0
        
        # Should be able to resolve dependencies
        execution_order = runner._resolve_dependencies(runner.test_suites[:3])
        assert len(execution_order) >= 3
        
        # Test report generation with empty results
        runner.start_time = time.time()
        runner.end_time = time.time() + 1
        
        report = runner._generate_report()
        assert report is not None
        assert "summary" in report


if __name__ == "__main__":
    # Run the validation tests
    pytest.main([__file__, "-v", "--tb=short"])