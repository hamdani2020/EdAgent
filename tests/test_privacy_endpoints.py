"""
Tests for privacy API endpoints
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from edagent.api.endpoints.privacy import router
from edagent.models.privacy import DataExportResult, DataDeletionResult


# Create test app
app = FastAPI()
app.include_router(router)


class TestPrivacyEndpoints:
    """Test cases for privacy API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authentication"""
        return {"user_id": str(uuid.uuid4())}
    
    @pytest.fixture
    def mock_privacy_service(self):
        """Mock privacy service"""
        return AsyncMock()
    
    def test_get_data_summary_success(self, client, mock_current_user):
        """Test successful data summary retrieval"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_user_data_summary.return_value = {
                    "user_profile": 1,
                    "skills": 5,
                    "conversations": 10,
                    "learning_paths": 2
                }
                
                response = client.get("/data-summary")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["user_id"] == mock_current_user["user_id"]
                assert "data_summary" in data
    
    def test_export_user_data_success(self, client, mock_current_user):
        """Test successful user data export"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                export_result = DataExportResult(
                    success=True,
                    user_id=mock_current_user["user_id"],
                    export_data={"test": "data"},
                    exported_at=datetime.utcnow()
                )
                mock_service.export_user_data.return_value = export_result
                
                response = client.post("/export", json={
                    "include_sensitive": False,
                    "format": "json"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["user_id"] == mock_current_user["user_id"]
                assert "export_data" in data
    
    def test_export_user_data_failure(self, client, mock_current_user):
        """Test failed user data export"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                export_result = DataExportResult(
                    success=False,
                    error_message="Export failed"
                )
                mock_service.export_user_data.return_value = export_result
                
                response = client.post("/export", json={
                    "include_sensitive": False,
                    "format": "json"
                })
                
                assert response.status_code == 400
                data = response.json()
                assert "Export failed" in data["detail"]
    
    def test_delete_user_data_success(self, client, mock_current_user):
        """Test successful user data deletion"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                deletion_result = DataDeletionResult(
                    success=True,
                    user_id=mock_current_user["user_id"],
                    deleted_data_types=["conversations"],
                    deleted_counts={"conversations": 5},
                    deleted_at=datetime.utcnow()
                )
                mock_service.delete_user_data.return_value = deletion_result
                
                response = client.delete("/data", json={
                    "data_types": ["conversations"],
                    "confirm_deletion": True,
                    "reason": "User request"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["user_id"] == mock_current_user["user_id"]
                assert data["deleted_data_types"] == ["conversations"]
                assert data["deleted_counts"] == {"conversations": 5}
    
    def test_delete_user_data_not_confirmed(self, client, mock_current_user):
        """Test data deletion without confirmation"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            response = client.delete("/data", json={
                "data_types": ["conversations"],
                "confirm_deletion": False
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "confirm_deletion=true" in data["detail"]
    
    def test_delete_user_data_failure(self, client, mock_current_user):
        """Test failed user data deletion"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                deletion_result = DataDeletionResult(
                    success=False,
                    error_message="Deletion failed"
                )
                mock_service.delete_user_data.return_value = deletion_result
                
                response = client.delete("/data", json={
                    "data_types": ["conversations"],
                    "confirm_deletion": True
                })
                
                assert response.status_code == 400
                data = response.json()
                assert "Deletion failed" in data["detail"]
    
    def test_get_privacy_settings_success(self, client, mock_current_user):
        """Test successful privacy settings retrieval"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            response = client.get("/settings")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "settings" in data
            assert "data_retention_days" in data["settings"]
            assert "allow_analytics" in data["settings"]
    
    def test_update_privacy_settings_success(self, client, mock_current_user):
        """Test successful privacy settings update"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            settings_data = {
                "data_retention_days": 365,
                "allow_analytics": False,
                "allow_personalization": True,
                "allow_marketing": False,
                "auto_delete_conversations": True,
                "conversation_retention_days": 90
            }
            
            response = client.put("/settings", json=settings_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["settings"]["data_retention_days"] == 365
            assert data["settings"]["allow_analytics"] is False
            assert data["settings"]["auto_delete_conversations"] is True
    
    def test_get_audit_log_success(self, client, mock_current_user):
        """Test successful audit log retrieval"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            response = client.get("/audit-log?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user_id"] == mock_current_user["user_id"]
            assert "audit_entries" in data
            assert "total_entries" in data
    
    def test_update_consent_success(self, client, mock_current_user):
        """Test successful consent update"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            consent_data = {
                "data_processing": True,
                "analytics": False,
                "marketing": False,
                "personalization": True
            }
            
            response = client.post("/consent", json=consent_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["consent_data"] == consent_data
    
    def test_update_consent_invalid_type(self, client, mock_current_user):
        """Test consent update with invalid consent type"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            consent_data = {
                "invalid_consent_type": True
            }
            
            response = client.post("/consent", json=consent_data)
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid consent type" in data["detail"]
    
    def test_export_data_headers(self, client, mock_current_user):
        """Test export data response headers"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                export_result = DataExportResult(
                    success=True,
                    user_id=mock_current_user["user_id"],
                    export_data={"test": "data"},
                    exported_at=datetime.utcnow()
                )
                mock_service.export_user_data.return_value = export_result
                
                response = client.post("/export", json={
                    "include_sensitive": False,
                    "format": "json"
                })
                
                assert response.status_code == 200
                assert "Content-Disposition" in response.headers
                assert "attachment" in response.headers["Content-Disposition"]
                assert "edagent_data_export" in response.headers["Content-Disposition"]
    
    def test_data_summary_exception_handling(self, client, mock_current_user):
        """Test exception handling in data summary endpoint"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_user_data_summary.side_effect = Exception("Database error")
                
                response = client.get("/data-summary")
                
                assert response.status_code == 500
                data = response.json()
                assert "Failed to retrieve data summary" in data["detail"]
    
    def test_export_exception_handling(self, client, mock_current_user):
        """Test exception handling in export endpoint"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.export_user_data.side_effect = Exception("Service error")
                
                response = client.post("/export", json={
                    "include_sensitive": False,
                    "format": "json"
                })
                
                assert response.status_code == 500
                data = response.json()
                assert "Data export failed" in data["detail"]
    
    def test_delete_exception_handling(self, client, mock_current_user):
        """Test exception handling in delete endpoint"""
        with patch('edagent.api.endpoints.privacy.get_current_user', return_value=mock_current_user):
            with patch('edagent.api.endpoints.privacy.PrivacyService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.delete_user_data.side_effect = Exception("Service error")
                
                response = client.delete("/data", json={
                    "confirm_deletion": True
                })
                
                assert response.status_code == 500
                data = response.json()
                assert "Data deletion failed" in data["detail"]