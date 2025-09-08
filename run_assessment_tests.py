#!/usr/bin/env python3
"""
Test runner for the assessment system integration
Runs comprehensive tests for the assessment workflow and data persistence.
"""

import sys
import os
import subprocess
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run all assessment integration tests"""
    print("🧪 Running Assessment System Integration Tests")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test files to run
    test_files = [
        "test_assessment_integration.py"
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            continue
            
        print(f"📋 Running tests from {test_file}")
        print("-" * 40)
        
        try:
            # Run pytest with verbose output
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short",
                "--color=yes"
            ], capture_output=True, text=True, timeout=300)
            
            # Parse results
            output_lines = result.stdout.split('\n')
            test_results = [line for line in output_lines if '::' in line and ('PASSED' in line or 'FAILED' in line)]
            
            file_passed = len([line for line in test_results if 'PASSED' in line])
            file_failed = len([line for line in test_results if 'FAILED' in line])
            file_total = file_passed + file_failed
            
            total_tests += file_total
            passed_tests += file_passed
            failed_tests += file_failed
            
            if result.returncode == 0:
                print(f"✅ All tests passed ({file_passed}/{file_total})")
            else:
                print(f"❌ Some tests failed ({file_passed}/{file_total} passed)")
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
            
            # Show detailed results
            if test_results:
                print("\nDetailed Results:")
                for line in test_results:
                    if 'PASSED' in line:
                        print(f"  ✅ {line.split('::')[-1].split(' ')[0]}")
                    elif 'FAILED' in line:
                        print(f"  ❌ {line.split('::')[-1].split(' ')[0]}")
            
            print()
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Tests timed out after 5 minutes")
            failed_tests += 1
        except Exception as e:
            print(f"💥 Error running tests: {str(e)}")
            failed_tests += 1
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    
    if failed_tests == 0:
        print("\n🎉 All assessment integration tests passed!")
        success_rate = 100.0
    else:
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n⚠️  Some tests failed. Success rate: {success_rate:.1f}%")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return failed_tests == 0


def run_specific_test_category(category):
    """Run tests for a specific category"""
    category_tests = {
        "manager": "TestAssessmentManager",
        "workflow": "TestAssessmentWorkflow", 
        "ui": "TestAssessmentUI",
        "persistence": "TestAssessmentDataPersistence",
        "errors": "TestAssessmentErrorHandling"
    }
    
    if category not in category_tests:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(category_tests.keys())}")
        return False
    
    test_class = category_tests[category]
    print(f"🧪 Running {category} tests ({test_class})")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "test_assessment_integration.py",
            f"-k", test_class,
            "-v",
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, timeout=120)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"💥 Error running {category} tests: {str(e)}")
        return False


def run_integration_validation():
    """Run integration validation tests"""
    print("🔍 Running Assessment Integration Validation")
    print("=" * 50)
    
    validation_tests = [
        "test_assessment_manager_initialization",
        "test_start_assessment_session_success",
        "test_submit_assessment_response_success", 
        "test_complete_assessment_session_success",
        "test_assessment_state_persistence"
    ]
    
    for test_name in validation_tests:
        print(f"Running: {test_name}")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "test_assessment_integration.py",
                f"-k", test_name,
                "-v"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  ✅ {test_name}")
            else:
                print(f"  ❌ {test_name}")
                print(f"     Error: {result.stdout.split('FAILED')[-1].strip() if 'FAILED' in result.stdout else 'Unknown error'}")
                
        except Exception as e:
            print(f"  💥 {test_name}: {str(e)}")
    
    print("\n✅ Integration validation completed")


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            success = run_tests()
            sys.exit(0 if success else 1)
        elif command == "validate":
            run_integration_validation()
        elif command in ["manager", "workflow", "ui", "persistence", "errors"]:
            success = run_specific_test_category(command)
            sys.exit(0 if success else 1)
        else:
            print("Usage: python run_assessment_tests.py [all|validate|manager|workflow|ui|persistence|errors]")
            sys.exit(1)
    else:
        # Default: run all tests
        success = run_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()