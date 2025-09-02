#!/usr/bin/env python3
"""
Comprehensive integration test runner for EdAgent
Orchestrates all integration tests with proper setup, execution, and reporting
"""

import sys
import os
import time
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSuite:
    """Represents a test suite with metadata"""
    
    def __init__(self, name: str, file_path: str, description: str, 
                 estimated_duration: int, dependencies: List[str] = None):
        self.name = name
        self.file_path = file_path
        self.description = description
        self.estimated_duration = estimated_duration  # in seconds
        self.dependencies = dependencies or []
        self.result = None
        self.duration = 0
        self.output = ""
        self.error_output = ""


class IntegrationTestRunner:
    """Main test runner for integration tests"""
    
    def __init__(self):
        self.test_suites = self._define_test_suites()
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def _define_test_suites(self) -> List[TestSuite]:
        """Define all available test suites"""
        return [
            TestSuite(
                name="data_management",
                file_path="tests/test_data_management.py",
                description="Test data factories, fixtures, and cleanup utilities",
                estimated_duration=30,
                dependencies=[]
            ),
            TestSuite(
                name="ai_integration",
                file_path="tests/test_ai_integration.py",
                description="AI service integration with prompt engineering and response processing",
                estimated_duration=60,
                dependencies=["data_management"]
            ),
            TestSuite(
                name="auth_integration",
                file_path="tests/test_auth_integration.py",
                description="Authentication and authorization system integration",
                estimated_duration=45,
                dependencies=["data_management"]
            ),
            TestSuite(
                name="learning_path_integration",
                file_path="tests/test_learning_path_integration.py",
                description="Learning path generation workflow integration",
                estimated_duration=90,
                dependencies=["data_management", "ai_integration"]
            ),
            TestSuite(
                name="conversation_integration",
                file_path="tests/test_conversation_manager.py",
                description="Conversation management and flow integration",
                estimated_duration=75,
                dependencies=["data_management", "ai_integration"]
            ),
            TestSuite(
                name="content_integration",
                file_path="tests/test_content_recommender.py",
                description="Content recommendation system integration",
                estimated_duration=60,
                dependencies=["data_management"]
            ),
            TestSuite(
                name="websocket_integration",
                file_path="tests/test_websocket_integration.py",
                description="WebSocket real-time communication integration",
                estimated_duration=45,
                dependencies=["data_management", "auth_integration"]
            ),
            TestSuite(
                name="privacy_integration",
                file_path="tests/test_privacy_integration.py",
                description="Privacy controls and data protection integration",
                estimated_duration=40,
                dependencies=["data_management", "auth_integration"]
            ),
            TestSuite(
                name="resume_integration",
                file_path="tests/test_resume_integration.py",
                description="Resume analysis and career coaching integration",
                estimated_duration=50,
                dependencies=["data_management", "ai_integration"]
            ),
            TestSuite(
                name="interview_integration",
                file_path="tests/test_interview_integration.py",
                description="Interview preparation system integration",
                estimated_duration=55,
                dependencies=["data_management", "ai_integration"]
            ),
            TestSuite(
                name="end_to_end_journeys",
                file_path="tests/test_integration_suite.py::TestEndToEndUserJourneys",
                description="Complete user journey integration tests",
                estimated_duration=180,
                dependencies=["ai_integration", "auth_integration", "learning_path_integration"]
            ),
            TestSuite(
                name="system_integration",
                file_path="tests/test_integration_suite.py::TestSystemIntegration",
                description="Cross-component system integration tests",
                estimated_duration=120,
                dependencies=["ai_integration", "content_integration", "auth_integration"]
            ),
            TestSuite(
                name="performance_tests",
                file_path="tests/test_integration_suite.py::TestPerformanceAndLoad",
                description="Performance and concurrent user handling tests",
                estimated_duration=300,
                dependencies=["auth_integration", "conversation_integration"]
            ),
            TestSuite(
                name="load_tests",
                file_path="tests/test_load_testing.py",
                description="Load testing and stress testing",
                estimated_duration=600,
                dependencies=["performance_tests"]
            )
        ]
    
    def run_all_tests(self, 
                     include_load_tests: bool = False,
                     parallel: bool = False,
                     verbose: bool = True,
                     stop_on_failure: bool = False) -> Dict[str, Any]:
        """Run all integration tests"""
        
        print("🚀 Starting EdAgent Integration Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Filter test suites based on options
        suites_to_run = self.test_suites.copy()
        if not include_load_tests:
            suites_to_run = [s for s in suites_to_run if s.name != "load_tests"]
        
        # Calculate total estimated duration
        total_estimated = sum(suite.estimated_duration for suite in suites_to_run)
        print(f"📊 Running {len(suites_to_run)} test suites")
        print(f"⏱️  Estimated duration: {total_estimated // 60}m {total_estimated % 60}s")
        print()
        
        # Run tests in dependency order
        execution_order = self._resolve_dependencies(suites_to_run)
        
        for i, suite in enumerate(execution_order, 1):
            print(f"[{i}/{len(execution_order)}] Running {suite.name}")
            print(f"📝 {suite.description}")
            
            if verbose:
                print(f"⏱️  Estimated: {suite.estimated_duration}s")
            
            # Run the test suite
            success = self._run_single_suite(suite, verbose)
            
            if success:
                print(f"✅ {suite.name} passed ({suite.duration:.1f}s)")
            else:
                print(f"❌ {suite.name} failed ({suite.duration:.1f}s)")
                if verbose and suite.error_output:
                    print(f"Error output:\n{suite.error_output}")
                
                if stop_on_failure:
                    print("🛑 Stopping on failure")
                    break
            
            print()
        
        self.end_time = time.time()
        
        # Generate final report
        return self._generate_report()
    
    def run_specific_suites(self, suite_names: List[str], verbose: bool = True) -> Dict[str, Any]:
        """Run specific test suites"""
        
        print(f"🎯 Running specific test suites: {', '.join(suite_names)}")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Find requested suites
        suites_to_run = []
        for name in suite_names:
            suite = next((s for s in self.test_suites if s.name == name), None)
            if suite:
                suites_to_run.append(suite)
            else:
                print(f"⚠️  Warning: Test suite '{name}' not found")
        
        if not suites_to_run:
            print("❌ No valid test suites found")
            return {"error": "No valid test suites"}
        
        # Resolve dependencies
        execution_order = self._resolve_dependencies(suites_to_run)
        
        for i, suite in enumerate(execution_order, 1):
            print(f"[{i}/{len(execution_order)}] Running {suite.name}")
            success = self._run_single_suite(suite, verbose)
            
            if success:
                print(f"✅ {suite.name} passed ({suite.duration:.1f}s)")
            else:
                print(f"❌ {suite.name} failed ({suite.duration:.1f}s)")
            print()
        
        self.end_time = time.time()
        return self._generate_report()
    
    def _resolve_dependencies(self, suites: List[TestSuite]) -> List[TestSuite]:
        """Resolve test suite dependencies and return execution order"""
        
        # Create a map of suite names to suites
        suite_map = {suite.name: suite for suite in suites}
        
        # Add dependencies that aren't already included
        all_needed = set(suite.name for suite in suites)
        for suite in suites:
            all_needed.update(suite.dependencies)
        
        # Add missing dependencies
        for needed in all_needed:
            if needed not in suite_map:
                dep_suite = next((s for s in self.test_suites if s.name == needed), None)
                if dep_suite:
                    suite_map[needed] = dep_suite
        
        # Topological sort to resolve dependencies
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(suite_name: str):
            if suite_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {suite_name}")
            if suite_name in visited:
                return
            
            temp_visited.add(suite_name)
            
            if suite_name in suite_map:
                suite = suite_map[suite_name]
                for dep in suite.dependencies:
                    visit(dep)
            
            temp_visited.remove(suite_name)
            visited.add(suite_name)
            
            if suite_name in suite_map:
                result.append(suite_map[suite_name])
        
        # Visit all suites
        for suite in suites:
            visit(suite.name)
        
        return result
    
    def _run_single_suite(self, suite: TestSuite, verbose: bool = True) -> bool:
        """Run a single test suite"""
        
        start_time = time.time()
        
        try:
            # Prepare pytest command
            cmd = [
                sys.executable, "-m", "pytest",
                suite.file_path,
                "-v" if verbose else "-q",
                "--tb=short",
                "--disable-warnings",
                "--no-header"
            ]
            
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=suite.estimated_duration * 3  # 3x timeout buffer
            )
            
            suite.duration = time.time() - start_time
            suite.output = result.stdout
            suite.error_output = result.stderr
            suite.result = "passed" if result.returncode == 0 else "failed"
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            suite.duration = time.time() - start_time
            suite.result = "timeout"
            suite.error_output = f"Test suite timed out after {suite.duration:.1f}s"
            return False
            
        except Exception as e:
            suite.duration = time.time() - start_time
            suite.result = "error"
            suite.error_output = str(e)
            return False
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Count results
        passed = sum(1 for suite in self.test_suites if suite.result == "passed")
        failed = sum(1 for suite in self.test_suites if suite.result == "failed")
        timeout = sum(1 for suite in self.test_suites if suite.result == "timeout")
        error = sum(1 for suite in self.test_suites if suite.result == "error")
        not_run = sum(1 for suite in self.test_suites if suite.result is None)
        
        # Calculate success rate
        total_run = passed + failed + timeout + error
        success_rate = passed / total_run if total_run > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "summary": {
                "total_suites": len(self.test_suites),
                "passed": passed,
                "failed": failed,
                "timeout": timeout,
                "error": error,
                "not_run": not_run,
                "success_rate": success_rate
            },
            "suite_results": []
        }
        
        # Add individual suite results
        for suite in self.test_suites:
            if suite.result is not None:
                report["suite_results"].append({
                    "name": suite.name,
                    "description": suite.description,
                    "result": suite.result,
                    "duration": suite.duration,
                    "estimated_duration": suite.estimated_duration,
                    "efficiency": suite.duration / suite.estimated_duration if suite.estimated_duration > 0 else 0
                })
        
        # Print summary
        print("📊 Integration Test Results Summary")
        print("=" * 60)
        print(f"Total Duration: {total_duration:.1f}s ({total_duration // 60:.0f}m {total_duration % 60:.0f}s)")
        print(f"Success Rate: {success_rate:.1%}")
        print()
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏰ Timeout: {timeout}")
        print(f"🚫 Error: {error}")
        print(f"⏸️  Not Run: {not_run}")
        print()
        
        # Show failed tests
        if failed > 0 or timeout > 0 or error > 0:
            print("❌ Failed Test Suites:")
            for suite in self.test_suites:
                if suite.result in ["failed", "timeout", "error"]:
                    print(f"  - {suite.name}: {suite.result}")
                    if suite.error_output:
                        # Show first few lines of error
                        error_lines = suite.error_output.split('\n')[:3]
                        for line in error_lines:
                            if line.strip():
                                print(f"    {line}")
            print()
        
        # Performance insights
        if total_run > 0:
            avg_efficiency = sum(
                suite.duration / suite.estimated_duration 
                for suite in self.test_suites 
                if suite.result is not None and suite.estimated_duration > 0
            ) / total_run
            
            print(f"⚡ Average Efficiency: {avg_efficiency:.1f}x (actual/estimated time)")
            
            # Find slowest tests
            slow_tests = [
                suite for suite in self.test_suites 
                if suite.result is not None and suite.duration > suite.estimated_duration * 1.5
            ]
            
            if slow_tests:
                print("🐌 Slower than expected:")
                for suite in sorted(slow_tests, key=lambda s: s.duration, reverse=True)[:3]:
                    print(f"  - {suite.name}: {suite.duration:.1f}s (expected {suite.estimated_duration}s)")
        
        return report
    
    def list_available_suites(self):
        """List all available test suites"""
        print("📋 Available Integration Test Suites")
        print("=" * 60)
        
        for suite in self.test_suites:
            print(f"🧪 {suite.name}")
            print(f"   {suite.description}")
            print(f"   Estimated duration: {suite.estimated_duration}s")
            if suite.dependencies:
                print(f"   Dependencies: {', '.join(suite.dependencies)}")
            print()
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integration_test_report_{timestamp}.json"
        
        report_path = project_root / "test_reports" / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {report_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="EdAgent Integration Test Runner")
    
    parser.add_argument(
        "--suites", "-s",
        nargs="+",
        help="Specific test suites to run"
    )
    
    parser.add_argument(
        "--include-load-tests", "-l",
        action="store_true",
        help="Include load tests (slow)"
    )
    
    parser.add_argument(
        "--list", "-ls",
        action="store_true",
        help="List available test suites"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet output"
    )
    
    parser.add_argument(
        "--stop-on-failure", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--save-report", "-r",
        help="Save report to specified file"
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    if args.list:
        runner.list_available_suites()
        return
    
    verbose = args.verbose and not args.quiet
    
    try:
        if args.suites:
            report = runner.run_specific_suites(args.suites, verbose=verbose)
        else:
            report = runner.run_all_tests(
                include_load_tests=args.include_load_tests,
                verbose=verbose,
                stop_on_failure=args.stop_on_failure
            )
        
        if args.save_report:
            runner.save_report(report, args.save_report)
        
        # Exit with appropriate code
        if report.get("summary", {}).get("failed", 0) > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()