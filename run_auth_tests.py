#!/usr/bin/env python3
"""
Authentication Integration Test Runner

This script runs comprehensive tests for the EdAgent authentication system
to verify all components work correctly together.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all authentication modules can be imported"""
    logger.info("Testing module imports...")
    
    try:
        from streamlit_api_client import EnhancedEdAgentAPI, AuthResult, APIError
        from streamlit_session_manager import SessionManager, UserInfo, UserPreferences
        from streamlit_auth_components import AuthenticationComponents, PasswordValidation
        logger.info("✅ All modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False


def test_component_initialization():
    """Test that authentication components can be initialized"""
    logger.info("Testing component initialization...")
    
    try:
        from streamlit_api_client import EnhancedEdAgentAPI
        from streamlit_session_manager import SessionManager
        from streamlit_auth_components import AuthenticationComponents
        
        # Initialize components
        session_manager = SessionManager()
        api_client = EnhancedEdAgentAPI("http://localhost:8000/api/v1", session_manager)
        auth_components = AuthenticationComponents(api_client, session_manager)
        
        logger.info("✅ Components initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Component initialization error: {e}")
        return False


def test_password_validation():
    """Test password validation functionality"""
    logger.info("Testing password validation...")
    
    try:
        from streamlit_api_client import EnhancedEdAgentAPI
        from streamlit_session_manager import SessionManager
        from streamlit_auth_components import AuthenticationComponents, PasswordStrength
        
        session_manager = SessionManager()
        api_client = EnhancedEdAgentAPI("http://localhost:8000/api/v1", session_manager)
        auth_components = AuthenticationComponents(api_client, session_manager)
        
        # Test weak password
        weak_result = auth_components.validate_password("weak")
        assert weak_result.strength in [PasswordStrength.VERY_WEAK, PasswordStrength.WEAK]
        assert not weak_result.is_valid
        
        # Test strong password
        strong_result = auth_components.validate_password("StrongPassword123!")
        assert strong_result.is_valid
        assert strong_result.strength.value >= PasswordStrength.GOOD.value
        
        logger.info("✅ Password validation tests passed")
        return True
    except Exception as e:
        logger.error(f"❌ Password validation test error: {e}")
        return False


def test_email_validation():
    """Test email validation functionality"""
    logger.info("Testing email validation...")
    
    try:
        from streamlit_api_client import EnhancedEdAgentAPI
        from streamlit_session_manager import SessionManager
        from streamlit_auth_components import AuthenticationComponents
        
        session_manager = SessionManager()
        api_client = EnhancedEdAgentAPI("http://localhost:8000/api/v1", session_manager)
        auth_components = AuthenticationComponents(api_client, session_manager)
        
        # Test valid email
        valid, error = auth_components.validate_email("test@example.com")
        assert valid
        assert error == ""
        
        # Test invalid email
        invalid, error = auth_components.validate_email("invalid-email")
        assert not invalid
        assert error != ""
        
        logger.info("✅ Email validation tests passed")
        return True
    except Exception as e:
        logger.error(f"❌ Email validation test error: {e}")
        return False


def test_session_management():
    """Test session management functionality"""
    logger.info("Testing session management...")
    
    try:
        from streamlit_session_manager import SessionManager, UserInfo
        from datetime import datetime, timedelta
        
        session_manager = SessionManager()
        
        # Test initial state
        assert not session_manager.is_authenticated()
        assert session_manager.get_current_user() is None
        
        # Test setting auth data
        user_info = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        session_manager.set_auth_data(
            user_info=user_info,
            access_token="test_token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Test authenticated state
        assert session_manager.is_authenticated()
        current_user = session_manager.get_current_user()
        assert current_user is not None
        assert current_user.user_id == "test_user_123"
        
        # Test clearing session
        session_manager.clear_session()
        assert not session_manager.is_authenticated()
        
        logger.info("✅ Session management tests passed")
        return True
    except Exception as e:
        logger.error(f"❌ Session management test error: {e}")
        return False


def test_authentication_workflow():
    """Test complete authentication workflow structure"""
    logger.info("Testing authentication workflow structure...")
    
    try:
        from streamlit_api_client import EnhancedEdAgentAPI
        from streamlit_session_manager import SessionManager
        from streamlit_auth_components import AuthenticationComponents
        
        session_manager = SessionManager()
        api_client = EnhancedEdAgentAPI("http://localhost:8000/api/v1", session_manager)
        auth_components = AuthenticationComponents(api_client, session_manager)
        
        # Test authentication status
        status = auth_components.get_authentication_status()
        assert isinstance(status, dict)
        assert "is_authenticated" in status
        assert "session_state" in status
        
        logger.info("✅ Authentication workflow structure tests passed")
        return True
    except Exception as e:
        logger.error(f"❌ Authentication workflow test error: {e}")
        return False


def run_all_tests() -> Dict[str, bool]:
    """Run all authentication tests"""
    logger.info("🚀 Starting EdAgent Authentication Integration Tests")
    logger.info("=" * 60)
    
    test_results = {
        "imports": test_imports(),
        "initialization": test_component_initialization(),
        "password_validation": test_password_validation(),
        "email_validation": test_email_validation(),
        "session_management": test_session_management(),
        "workflow_structure": test_authentication_workflow()
    }
    
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"📈 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All authentication integration tests passed!")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed!")
        return False


def main():
    """Main test runner"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()