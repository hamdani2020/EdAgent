# EdAgent Integration Test Suite

This directory contains comprehensive integration tests for the EdAgent conversational AI system. The test suite covers end-to-end user journeys, performance testing, load testing, and system integration validation.

## Test Structure

### Core Integration Tests
- `test_integration_suite.py` - Main integration test suite with end-to-end user journeys
- `test_ai_integration.py` - AI service integration with prompt engineering
- `test_auth_integration.py` - Authentication and authorization system tests
- `test_learning_path_integration.py` - Learning path generation workflow tests
- `test_conversation_manager.py` - Conversation management integration
- `test_content_recommender.py` - Content recommendation system tests
- `test_websocket_integration.py` - WebSocket real-time communication tests
- `test_privacy_integration.py` - Privacy controls and data protection tests
- `test_resume_integration.py` - Resume analysis integration tests
- `test_interview_integration.py` - Interview preparation system tests

### Performance and Load Testing
- `test_load_testing.py` - Load testing utilities and stress tests
- `test_integration_suite.py::TestPerformanceAndLoad` - Performance testing

### Test Infrastructure
- `test_data_management.py` - Test data factories, fixtures, and cleanup utilities
- `test_integration_validation.py` - Meta-tests that validate the testing infrastructure
- `run_integration_tests.py` - Comprehensive test runner with dependency resolution
- `integration_test_config.yaml` - Configuration for test environments and thresholds

## Quick Start

### Run All Integration Tests
```bash
# Run all tests (excluding load tests)
python tests/run_integration_tests.py

# Include load tests (slow)
python tests/run_integration_tests.py --include-load-tests

# Run specific test suites
python tests/run_integration_tests.py --suites ai_integration auth_integration

# List available test suites
python tests/run_integration_tests.py --list
```

### Run Individual Test Files
```bash
# Run specific test file
pytest tests/test_ai_integration.py -v

# Run with coverage
pytest tests/test_integration_suite.py --cov=edagent --cov-report=html

# Run performance tests only
pytest tests/test_integration_suite.py::TestPerformanceAndLoad -v
```

## Test Categories

### 1. End-to-End User Journeys
Tests complete user workflows from start to finish:
- **Beginner Onboarding**: New user registration → skill assessment → learning path creation → content recommendations
- **Career Change**: Experienced professional transitioning careers → tailored assessment → career-specific learning path
- **Interview Preparation**: User preparing for interviews → question generation → practice sessions → feedback

### 2. System Integration Tests
Tests integration between different system components:
- AI service ↔ Content recommender integration
- User context ↔ Learning path generation integration
- Authentication ↔ Authorization system integration

### 3. Performance Tests
Tests system performance under various conditions:
- Response time validation (< 3 seconds requirement)
- Concurrent user handling (10-100 users)
- Memory usage monitoring
- Database connection pooling

### 4. Load Tests
Tests system behavior under high load:
- **Constant Load**: Sustained traffic simulation
- **Spike Tests**: Sudden traffic increases
- **Stress Tests**: Gradually increasing load until breaking point
- **Memory Leak Detection**: Long-running tests to detect memory issues

## Test Data Management

The test suite includes comprehensive test data management:

### Test Data Factory
Creates realistic test objects:
```python
from tests.test_data_management import TestDataFactory

factory = TestDataFactory()

# Create user contexts
beginner_user = factory.create_user_context(skill_level="beginner")
intermediate_user = factory.create_user_context(skill_level="intermediate")

# Create learning paths
web_dev_path = factory.create_learning_path(goal="become a web developer")
data_sci_path = factory.create_learning_path(goal="become a data scientist")

# Create skill assessments
assessment = factory.create_skill_assessment(
    skill_area="Web Development",
    overall_level="beginner"
)
```

### Mock Services
Realistic mock services for testing:
```python
from tests.test_data_management import MockServiceManager

manager = MockServiceManager()
ai_mock = manager.setup_ai_service_mock()
content_mock = manager.setup_content_recommender_mock()
```

### Automatic Cleanup
All test data is automatically tracked and cleaned up:
```python
@pytest.fixture
def test_db_manager():
    manager = TestDatabaseManager()
    yield manager
    # Automatic cleanup after test
    asyncio.run(manager.cleanup_all())
```

## Performance Thresholds

The test suite validates against these performance requirements:

### Response Times
- Health endpoint: < 0.5 seconds
- Conversation endpoint: < 3.0 seconds
- Learning path generation: < 5.0 seconds
- Authentication: < 2.0 seconds

### Success Rates
- Minimum success rate: 85%
- Critical endpoints: 95%

### Concurrent Users
- Light load: 10 users
- Moderate load: 50 users
- Heavy load: 100 users

### Memory Usage
- Max memory increase: 150MB during tests
- Memory leak threshold: 200MB

## Configuration

Test configuration is managed in `integration_test_config.yaml`:

```yaml
performance_thresholds:
  response_times:
    conversation_endpoint: 3.0
  success_rates:
    minimum_success_rate: 0.85
  concurrent_users:
    moderate_load: 50

load_test_scenarios:
  smoke_test:
    duration: 30
    concurrent_users: 5
  load_test:
    duration: 300
    concurrent_users: 25
```

## Test Execution Options

### Test Runner Features
- **Dependency Resolution**: Automatically runs tests in correct order based on dependencies
- **Parallel Execution**: Option to run independent tests in parallel
- **Failure Handling**: Continue on failure or stop at first failure
- **Comprehensive Reporting**: JSON, HTML, and JUnit report formats
- **Performance Metrics**: Detailed performance analysis and trending

### Command Line Options
```bash
# Verbose output with detailed logging
python tests/run_integration_tests.py --verbose

# Stop on first failure
python tests/run_integration_tests.py --stop-on-failure

# Save detailed report
python tests/run_integration_tests.py --save-report integration_report.json

# Quiet mode for CI/CD
python tests/run_integration_tests.py --quiet
```

## Continuous Integration

The test suite is designed for CI/CD integration:

### GitHub Actions Example
```yaml
- name: Run Integration Tests
  run: |
    python tests/run_integration_tests.py \
      --suites data_management ai_integration auth_integration \
      --save-report ci_report.json \
      --quiet
  
- name: Run Performance Tests
  run: |
    python tests/run_integration_tests.py \
      --suites performance_tests \
      --save-report performance_report.json
```

### Docker Support
```dockerfile
# Run tests in Docker container
RUN python tests/run_integration_tests.py --include-load-tests
```

## Troubleshooting

### Common Issues

1. **Test Timeouts**
   - Increase timeout values in `integration_test_config.yaml`
   - Check for slow external API calls
   - Verify database connection performance

2. **Memory Issues**
   - Monitor memory usage during tests
   - Check for proper cleanup in test fixtures
   - Verify mock services are properly disposed

3. **Flaky Tests**
   - Enable test retries in configuration
   - Check for race conditions in async tests
   - Verify proper test isolation

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=. python -m pytest tests/test_integration_suite.py -v -s --log-cli-level=DEBUG

# Run single test with detailed output
python tests/run_integration_tests.py --suites ai_integration --verbose
```

## Contributing

When adding new integration tests:

1. **Follow Naming Convention**: `test_[component]_integration.py`
2. **Use Test Data Factory**: Create test data using provided factories
3. **Add Cleanup**: Ensure proper cleanup of test data
4. **Update Dependencies**: Add test suite to `run_integration_tests.py`
5. **Document Performance**: Add performance expectations to config
6. **Test the Test**: Add validation in `test_integration_validation.py`

### Example New Test Suite
```python
class TestNewFeatureIntegration:
    @pytest.fixture
    def test_data_manager(self):
        manager = TestDatabaseManager()
        yield manager
        asyncio.run(manager.cleanup_all())
    
    @pytest.mark.asyncio
    async def test_new_feature_workflow(self, test_data_manager):
        # Test implementation
        pass
```

## Metrics and Reporting

The test suite provides comprehensive metrics:

- **Execution Time**: Total and per-test execution times
- **Success Rates**: Overall and per-component success rates
- **Performance Metrics**: Response times, throughput, resource usage
- **Coverage Reports**: Code coverage analysis
- **Trend Analysis**: Performance trends over time

Reports are generated in multiple formats for different audiences:
- **JSON**: Machine-readable for CI/CD integration
- **HTML**: Human-readable with charts and graphs
- **JUnit**: Compatible with most CI/CD systems