"""
Tests for Privacy Components and Data Management Features

This module tests:
- Privacy settings display and update functionality
- Data export interface with download capabilities
- Data deletion functionality with proper confirmation dialogs
- Privacy dashboard showing data summary and user control options
- Consent management and privacy preference updates
- Audit log display for privacy-related actions
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

import streamlit as st
import pandas as pd

# Import the modules to test
from streamlit_privacy_components import (
    PrivacyComponents, PrivacySettings, DataSummary, AuditLogEntry,
    DataType, ExportFormat
)
from streamlit_api_client import EnhancedEdAgentAPI
from streamlit_session_manager import SessionManager, UserInfo


class TestPrivacySettings:
    """Test PrivacySettings data class"""
    
    def test_privacy_settings_creation(self):
        """Test creating PrivacySettings with default values"""
        settings = PrivacySettings()
        
        assert settings.allow_analytics is True
        assert settings.allow_personalization is True
        assert settings.allow_marketing is False
        assert settings.conversation_retention_days == 365
        assert settings.data_processing_consent is True
    
    def test_privacy_settings_to_dict(self):
        """Test converting PrivacySettings to dictionary"""
        settings = PrivacySettings(
            allow_analytics=False,
            allow_marketing=True,
            conversation_retention_days=180
        )
        
        settings_dict = settings.to_dict()
        
        assert settings_dict["allow_analytics"] is False
        assert settings_dict["allow_marketing"] is True
        assert settings_dict["conversation_retention_days"] == 180
        assert "data_processing_consent" in settings_dict
    
    def test_privacy_settings_from_dict(self):
        """Test creating PrivacySettings from dictionary"""
        data = {
            "allow_analytics": False,
            "allow_personalization": True,
            "allow_marketing": True,
            "conversation_retention_days": 90
        }
        
        settings = PrivacySettings.from_dict(data)
        
        assert settings.allow_analytics is False
        assert settings.allow_personalization is True
        assert settings.allow_marketing is True
        assert settings.conversation_retention_days == 90


class TestDataSummary:
    """Test DataSummary data class"""
    
    def test_data_summary_creation(self):
        """Test creating DataSummary with default values"""
        summary = DataSummary()
        
        assert summary.total_conversations == 0
        assert summary.total_assessments == 0
        assert summary.total_learning_paths == 0
        assert summary.data_size_mb == 0.0
        assert summary.last_export_date is None
    
    def test_data_summary_with_values(self):
        """Test creating DataSummary with specific values"""
        created_date = datetime.now() - timedelta(days=30)
        export_date = datetime.now() - timedelta(days=7)
        
        summary = DataSummary(
            total_conversations=50,
            total_assessments=10,
            total_learning_paths=5,
            data_size_mb=2.5,
            account_created_date=created_date,
            last_export_date=export_date
        )
        
        assert summary.total_conversations == 50
        assert summary.total_assessments == 10
        assert summary.total_learning_paths == 5
        assert summary.data_size_mb == 2.5
        assert summary.account_created_date == created_date
        assert summary.last_export_date == export_date


class TestAuditLogEntry:
    """Test AuditLogEntry data class"""
    
    def test_audit_log_entry_creation(self):
        """Test creating AuditLogEntry"""
        timestamp = datetime.now()
        
        entry = AuditLogEntry(
            timestamp=timestamp,
            action="privacy_settings_updated",
            details="User updated privacy settings",
            ip_address="192.168.1.1",
            success=True
        )
        
        assert entry.timestamp == timestamp
        assert entry.action == "privacy_settings_updated"
        assert entry.details == "User updated privacy settings"
        assert entry.ip_address == "192.168.1.1"
        assert entry.success is True


class TestPrivacyComponents:
    """Test PrivacyComponents class"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        api = Mock(spec=EnhancedEdAgentAPI)
        
        # Mock privacy-related methods
        api.get_privacy_settings = AsyncMock(return_value={
            "settings": {
                "allow_analytics": True,
                "allow_personalization": True,
                "allow_marketing": False,
                "conversation_retention_days": 365
            }
        })
        
        api.update_privacy_settings = AsyncMock(return_value=True)
        api.export_user_data = AsyncMock(return_value={
            "conversations": [{"id": "1", "content": "test"}],
            "assessments": [{"id": "1", "score": 85}],
            "profile": {"name": "Test User"}
        })
        api.delete_user_data = AsyncMock(return_value={"success": True})
        api.get_privacy_audit_log = AsyncMock(return_value=[
            {
                "timestamp": datetime.now().isoformat(),
                "action": "privacy_settings_updated",
                "details": "Settings updated",
                "success": True
            }
        ])
        api.log_privacy_action = AsyncMock(return_value=True)
        api.request_data_export_email = AsyncMock(return_value=True)
        
        return api
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        session_manager = Mock(spec=SessionManager)
        
        user_info = UserInfo(
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now() - timedelta(days=30)
        )
        
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = user_info
        
        return session_manager
    
    @pytest.fixture
    def privacy_components(self, mock_api_client, mock_session_manager):
        """Create PrivacyComponents instance with mocks"""
        return PrivacyComponents(mock_api_client, mock_session_manager)
    
    def test_privacy_components_initialization(self, privacy_components):
        """Test PrivacyComponents initialization"""
        assert privacy_components.api is not None
        assert privacy_components.session_manager is not None
    
    @patch('streamlit_privacy_components.st')
    def test_get_current_privacy_settings(self, mock_st, privacy_components):
        """Test getting current privacy settings"""
        settings = privacy_components._get_current_privacy_settings()
        
        assert isinstance(settings, PrivacySettings)
        assert settings.allow_analytics is True
        assert settings.allow_personalization is True
        assert settings.allow_marketing is False
        assert settings.conversation_retention_days == 365
    
    @patch('streamlit_privacy_components.st')
    def test_update_privacy_settings(self, mock_st, privacy_components):
        """Test updating privacy settings"""
        new_settings = PrivacySettings(
            allow_analytics=False,
            allow_marketing=True,
            conversation_retention_days=180
        )
        
        result = privacy_components._update_privacy_settings(new_settings)
        
        assert result is True
        privacy_components.api.update_privacy_settings.assert_called_once()
    
    @patch('streamlit_privacy_components.st')
    def test_get_data_summary(self, mock_st, privacy_components):
        """Test getting data summary"""
        # Mock session state
        mock_st.session_state = {
            "chat_messages": [{"role": "user", "content": "test"}] * 10,
            "user_assessments": [{"id": "1"}] * 5,
            "learning_paths": [{"id": "1"}] * 3
        }
        
        summary = privacy_components._get_data_summary()
        
        assert isinstance(summary, DataSummary)
        assert summary.total_conversations == 10
        assert summary.total_assessments == 5
        assert summary.total_learning_paths == 3
        assert summary.data_size_mb > 0
    
    @patch('streamlit_privacy_components.st')
    def test_handle_data_export_json(self, mock_st, privacy_components):
        """Test handling JSON data export"""
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        privacy_components._handle_data_export(
            ExportFormat.JSON.value,
            [DataType.CONVERSATIONS.value],
            False
        )
        
        privacy_components.api.export_user_data.assert_called_once()
        mock_st.success.assert_called()
        mock_st.download_button.assert_called()
    
    @patch('streamlit_privacy_components.st')
    def test_handle_data_export_csv(self, mock_st, privacy_components):
        """Test handling CSV data export"""
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        privacy_components._handle_data_export(
            ExportFormat.CSV.value,
            [DataType.CONVERSATIONS.value],
            False
        )
        
        privacy_components.api.export_user_data.assert_called_once()
        mock_st.success.assert_called()
        mock_st.download_button.assert_called()
    
    @patch('streamlit_privacy_components.st')
    def test_handle_email_export(self, mock_st, privacy_components):
        """Test handling email export request"""
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        privacy_components._handle_email_export(
            ExportFormat.JSON.value,
            [DataType.CONVERSATIONS.value],
            False
        )
        
        privacy_components.api.request_data_export_email.assert_called_once()
        mock_st.success.assert_called()
    
    @patch('streamlit_privacy_components.st')
    def test_handle_data_deletion(self, mock_st, privacy_components):
        """Test handling data deletion"""
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        # Mock session state
        mock_st.session_state = {
            "chat_messages": [{"role": "user", "content": "test"}],
            "learning_paths": [{"id": "1"}]
        }
        
        privacy_components._handle_data_deletion([DataType.CONVERSATIONS.value])
        
        privacy_components.api.delete_user_data.assert_called_once()
        mock_st.success.assert_called()
    
    @patch('streamlit_privacy_components.st')
    def test_handle_account_deletion(self, mock_st, privacy_components):
        """Test handling complete account deletion"""
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        privacy_components._handle_data_deletion([DataType.ALL.value])
        
        privacy_components.api.delete_user_data.assert_called_once()
        privacy_components.session_manager.clear_session.assert_called_once()
        mock_st.success.assert_called()
        mock_st.rerun.assert_called()
    
    def test_convert_to_csv(self, privacy_components):
        """Test converting export data to CSV format"""
        export_data = {
            "conversations": [
                {"id": "1", "content": "Hello", "timestamp": "2024-01-01"},
                {"id": "2", "content": "Hi there", "timestamp": "2024-01-02"}
            ],
            "assessments": [
                {"id": "1", "score": 85, "skill": "Python"}
            ]
        }
        
        csv_result = privacy_components._convert_to_csv(export_data)
        
        assert isinstance(csv_result, str)
        assert "data_type" in csv_result
        assert "conversations" in csv_result
        assert "assessments" in csv_result
    
    @patch('streamlit_privacy_components.st')
    @patch('streamlit_privacy_components.asyncio.run')
    def test_log_privacy_action(self, mock_asyncio_run, mock_st, privacy_components):
        """Test logging privacy action"""
        # Create a proper mock session state that behaves like a dict
        session_state_dict = {}
        mock_st.session_state = session_state_dict
        
        # Mock asyncio.run to return True
        mock_asyncio_run.return_value = True
        
        privacy_components._log_privacy_action("test_action", "Test details")
        
        # Verify API was called
        mock_asyncio_run.assert_called()
        # Check that the session state was updated
        assert "privacy_audit_log" in session_state_dict
    
    @patch('streamlit_privacy_components.st')
    def test_get_audit_log(self, mock_st, privacy_components):
        """Test getting audit log"""
        audit_entries = privacy_components._get_audit_log()
        
        assert isinstance(audit_entries, list)
        assert len(audit_entries) > 0
        assert isinstance(audit_entries[0], AuditLogEntry)
        privacy_components.api.get_privacy_audit_log.assert_called_once()


class TestPrivacyIntegration:
    """Integration tests for privacy functionality"""
    
    @pytest.fixture
    def setup_streamlit_session(self):
        """Setup Streamlit session state for testing"""
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        st.session_state.clear()
        
        # Initialize with test data
        st.session_state.update({
            "chat_messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "user_assessments": [
                {"id": "1", "skill": "Python", "score": 85}
            ],
            "learning_paths": [
                {"id": "1", "title": "Learn Python", "progress": 0.5}
            ]
        })
    
    @patch('streamlit_privacy_components.st')
    @patch('streamlit_privacy_components.asyncio.run')
    def test_privacy_settings_workflow(self, mock_asyncio_run, mock_st, setup_streamlit_session):
        """Test complete privacy settings workflow"""
        # Mock API responses
        mock_asyncio_run.side_effect = [
            {"settings": {"allow_analytics": True}},  # get_privacy_settings
            True  # update_privacy_settings
        ]
        
        # Create components
        api = Mock(spec=EnhancedEdAgentAPI)
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user",
            email="test@example.com"
        )
        
        privacy_components = PrivacyComponents(api, session_manager)
        
        # Test getting settings
        settings = privacy_components._get_current_privacy_settings()
        assert isinstance(settings, PrivacySettings)
        
        # Test updating settings
        new_settings = PrivacySettings(allow_analytics=False)
        result = privacy_components._update_privacy_settings(new_settings)
        assert result is True
    
    @patch('streamlit_privacy_components.st')
    @patch('streamlit_privacy_components.asyncio.run')
    def test_data_export_workflow(self, mock_asyncio_run, mock_st, setup_streamlit_session):
        """Test complete data export workflow"""
        # Mock API response
        export_data = {
            "conversations": [{"id": "1", "content": "test"}],
            "profile": {"name": "Test User"}
        }
        mock_asyncio_run.return_value = export_data
        
        # Create components
        api = Mock(spec=EnhancedEdAgentAPI)
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user",
            email="test@example.com"
        )
        
        privacy_components = PrivacyComponents(api, session_manager)
        
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        # Test export
        privacy_components._handle_data_export(
            ExportFormat.JSON.value,
            [DataType.CONVERSATIONS.value],
            False
        )
        
        mock_st.success.assert_called()
        mock_st.download_button.assert_called()
    
    @patch('streamlit_privacy_components.st')
    @patch('streamlit_privacy_components.asyncio.run')
    def test_data_deletion_workflow(self, mock_asyncio_run, mock_st, setup_streamlit_session):
        """Test complete data deletion workflow"""
        # Mock API response
        mock_asyncio_run.return_value = {"success": True}
        
        # Create components
        api = Mock(spec=EnhancedEdAgentAPI)
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user",
            email="test@example.com"
        )
        
        privacy_components = PrivacyComponents(api, session_manager)
        
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        # Mock session state
        mock_st.session_state = {
            "chat_messages": [{"role": "user", "content": "test"}],
            "learning_paths": [{"id": "1"}]
        }
        
        # Test deletion
        privacy_components._handle_data_deletion([DataType.CONVERSATIONS.value])
        
        mock_st.success.assert_called()


class TestPrivacyErrorHandling:
    """Test error handling in privacy components"""
    
    @pytest.fixture
    def failing_api_client(self):
        """Create API client that fails"""
        api = Mock(spec=EnhancedEdAgentAPI)
        
        # Make all methods raise exceptions
        api.get_privacy_settings = AsyncMock(side_effect=Exception("API Error"))
        api.update_privacy_settings = AsyncMock(side_effect=Exception("API Error"))
        api.export_user_data = AsyncMock(side_effect=Exception("API Error"))
        api.delete_user_data = AsyncMock(side_effect=Exception("API Error"))
        
        return api
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        session_manager = Mock(spec=SessionManager)
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = UserInfo(
            user_id="test_user",
            email="test@example.com"
        )
        return session_manager
    
    @patch('streamlit_privacy_components.st')
    def test_privacy_settings_error_handling(self, mock_st, failing_api_client, mock_session_manager):
        """Test error handling when getting privacy settings fails"""
        privacy_components = PrivacyComponents(failing_api_client, mock_session_manager)
        
        settings = privacy_components._get_current_privacy_settings()
        
        # Should return default settings on error
        assert isinstance(settings, PrivacySettings)
        mock_st.error.assert_called()
    
    @patch('streamlit_privacy_components.st')
    def test_data_export_error_handling(self, mock_st, failing_api_client, mock_session_manager):
        """Test error handling when data export fails"""
        privacy_components = PrivacyComponents(failing_api_client, mock_session_manager)
        
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        privacy_components._handle_data_export(
            ExportFormat.JSON.value,
            [DataType.CONVERSATIONS.value],
            False
        )
        
        mock_st.error.assert_called()
    
    @patch('streamlit_privacy_components.st')
    def test_data_deletion_error_handling(self, mock_st, failing_api_client, mock_session_manager):
        """Test error handling when data deletion fails"""
        privacy_components = PrivacyComponents(failing_api_client, mock_session_manager)
        
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        privacy_components._handle_data_deletion([DataType.CONVERSATIONS.value])
        
        mock_st.error.assert_called()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])