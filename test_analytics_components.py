"""
Tests for Analytics Components
Comprehensive tests for analytics calculations, chart rendering, and dashboard functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from streamlit_analytics_components import (
    AnalyticsData,
    Achievement,
    AnalyticsCalculator,
    AnalyticsChartRenderer,
    AnalyticsDataManager,
    AnalyticsDashboard,
    render_analytics_dashboard,
    ACHIEVEMENT_DEFINITIONS
)


class TestAnalyticsData:
    """Tests for AnalyticsData dataclass"""
    
    def test_analytics_data_initialization(self):
        """Test AnalyticsData initialization with defaults"""
        data = AnalyticsData(user_id="test_user")
        
        assert data.user_id == "test_user"
        assert data.total_assessments == 0
        assert data.total_learning_paths == 0
        assert data.completed_paths == 0
        assert data.skills_improved == 0
        assert data.study_hours == 0.0
        assert data.current_streak == 0
        assert data.longest_streak == 0
        assert data.achievements == []
        assert data.skill_levels == {}
        assert data.progress_timeline == []
        assert data.activity_data == {}
        assert data.learning_velocity == 0.0
    
    def test_analytics_data_with_values(self):
        """Test AnalyticsData initialization with custom values"""
        skill_levels = {"Python": 85.0, "JavaScript": 70.0}
        achievements = [Achievement("test", "Test", "Test achievement", "🏆", "test")]
        
        data = AnalyticsData(
            user_id="test_user",
            total_assessments=5,
            skill_levels=skill_levels,
            achievements=achievements
        )
        
        assert data.total_assessments == 5
        assert data.skill_levels == skill_levels
        assert data.achievements == achievements


class TestAchievement:
    """Tests for Achievement dataclass"""
    
    def test_achievement_initialization(self):
        """Test Achievement initialization"""
        achievement = Achievement(
            id="test_achievement",
            title="Test Achievement",
            description="A test achievement",
            icon="🏆",
            category="test"
        )
        
        assert achievement.id == "test_achievement"
        assert achievement.title == "Test Achievement"
        assert achievement.description == "A test achievement"
        assert achievement.icon == "🏆"
        assert achievement.category == "test"
        assert achievement.earned == False
        assert achievement.earned_date is None
        assert achievement.progress == 0.0
        assert achievement.target == 1
    
    def test_achievement_to_dict(self):
        """Test Achievement to_dict method"""
        achievement = Achievement(
            id="test",
            title="Test",
            description="Test achievement",
            icon="🏆",
            category="test",
            earned=True,
            progress=100.0
        )
        
        result = achievement.to_dict()
        
        assert isinstance(result, dict)
        assert result["id"] == "test"
        assert result["earned"] == True
        assert result["progress"] == 100.0


class TestAnalyticsCalculator:
    """Tests for AnalyticsCalculator class"""
    
    def test_calculate_learning_velocity_empty_data(self):
        """Test learning velocity calculation with empty data"""
        velocity = AnalyticsCalculator.calculate_learning_velocity([])
        assert velocity == 0.0
    
    def test_calculate_learning_velocity_single_point(self):
        """Test learning velocity calculation with single data point"""
        progress_data = [{"date": datetime.now(), "progress": 50}]
        velocity = AnalyticsCalculator.calculate_learning_velocity(progress_data)
        assert velocity == 0.0
    
    def test_calculate_learning_velocity_multiple_points(self):
        """Test learning velocity calculation with multiple data points"""
        base_date = datetime.now()
        progress_data = [
            {"date": base_date, "progress": 0},
            {"date": base_date + timedelta(days=1), "progress": 10},
            {"date": base_date + timedelta(days=2), "progress": 25},
            {"date": base_date + timedelta(days=3), "progress": 40}
        ]
        
        velocity = AnalyticsCalculator.calculate_learning_velocity(progress_data)
        assert velocity > 0
        assert isinstance(velocity, float)
    
    def test_calculate_skill_radar_data_empty(self):
        """Test skill radar data calculation with empty skills"""
        result = AnalyticsCalculator.calculate_skill_radar_data({})
        
        assert result == {"skills": [], "levels": []}
    
    def test_calculate_skill_radar_data_with_skills(self):
        """Test skill radar data calculation with skills"""
        skill_levels = {
            "Python": 85.0,
            "JavaScript": 70.0,
            "SQL": 90.0
        }
        
        result = AnalyticsCalculator.calculate_skill_radar_data(skill_levels)
        
        assert result["skills"] == ["Python", "JavaScript", "SQL"]
        assert result["levels"] == [85.0, 70.0, 90.0]
    
    def test_calculate_skill_radar_data_normalization(self):
        """Test skill radar data normalization"""
        skill_levels = {
            "Skill1": 150.0,  # Above 100
            "Skill2": -10.0,  # Below 0
            "Skill3": 50.0    # Normal
        }
        
        result = AnalyticsCalculator.calculate_skill_radar_data(skill_levels)
        
        assert result["levels"] == [100, 0, 50]  # Normalized values
    
    def test_generate_activity_heatmap_data(self):
        """Test activity heatmap data generation"""
        activity_data = {"day_0_hour_9": 5, "day_1_hour_14": 3}
        
        result = AnalyticsCalculator.generate_activity_heatmap_data(activity_data)
        
        assert result.shape == (7, 24)  # 7 days x 24 hours
        assert result[0][9] == 5  # Specific activity data
        assert result[1][14] == 3
        assert isinstance(result, np.ndarray)
    
    def test_calculate_achievement_progress(self):
        """Test achievement progress calculation"""
        analytics_data = AnalyticsData(
            user_id="test_user",
            total_assessments=5,
            total_learning_paths=2,
            completed_paths=1,
            current_streak=10,
            longest_streak=15,
            skill_levels={"Python": 85.0, "JavaScript": 70.0}
        )
        
        achievements = AnalyticsCalculator.calculate_achievement_progress(analytics_data)
        
        assert len(achievements) > 0
        assert all(isinstance(a, Achievement) for a in achievements)
        
        # Check specific achievements
        first_assessment = next((a for a in achievements if a.id == "first_assessment"), None)
        assert first_assessment is not None
        assert first_assessment.earned == True  # 5 assessments >= 1
        
        week_warrior = next((a for a in achievements if a.id == "week_warrior"), None)
        assert week_warrior is not None
        assert week_warrior.earned == True  # 10 day streak >= 7


class TestAnalyticsChartRenderer:
    """Tests for AnalyticsChartRenderer class"""
    
    def test_render_progress_timeline_chart_empty_data(self):
        """Test progress timeline chart with empty data"""
        fig = AnalyticsChartRenderer.render_progress_timeline_chart([])
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0  # Should generate sample data
    
    def test_render_progress_timeline_chart_with_data(self):
        """Test progress timeline chart with actual data"""
        progress_data = [
            {"date": datetime.now() - timedelta(days=2), "progress": 20},
            {"date": datetime.now() - timedelta(days=1), "progress": 40},
            {"date": datetime.now(), "progress": 60}
        ]
        
        fig = AnalyticsChartRenderer.render_progress_timeline_chart(progress_data)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_render_skill_radar_chart_empty_skills(self):
        """Test skill radar chart with empty skills"""
        fig = AnalyticsChartRenderer.render_skill_radar_chart({})
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0  # Should generate sample data
    
    def test_render_skill_radar_chart_with_skills(self):
        """Test skill radar chart with actual skills"""
        skill_levels = {
            "Python": 85.0,
            "JavaScript": 70.0,
            "SQL": 90.0
        }
        
        fig = AnalyticsChartRenderer.render_skill_radar_chart(skill_levels)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_render_activity_heatmap(self):
        """Test activity heatmap rendering"""
        activity_data = {"day_0_hour_9": 5}
        
        fig = AnalyticsChartRenderer.render_activity_heatmap(activity_data)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_render_skill_distribution_chart_empty_skills(self):
        """Test skill distribution chart with empty skills"""
        fig = AnalyticsChartRenderer.render_skill_distribution_chart({})
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0  # Should generate sample data
    
    def test_render_skill_distribution_chart_with_skills(self):
        """Test skill distribution chart with actual skills"""
        skill_levels = {
            "Python": 85.0,
            "JavaScript": 70.0,
            "SQL": 90.0
        }
        
        fig = AnalyticsChartRenderer.render_skill_distribution_chart(skill_levels)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_render_learning_velocity_gauge(self):
        """Test learning velocity gauge rendering"""
        fig = AnalyticsChartRenderer.render_learning_velocity_gauge(3.5)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0


class TestAnalyticsDataManager:
    """Tests for AnalyticsDataManager class"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API client"""
        api_client = Mock()
        api_client.get_user_assessments = AsyncMock(return_value=[
            {"id": "assessment_1", "skill_area": "Python", "completed": True},
            {"id": "assessment_2", "skill_area": "JavaScript", "completed": True}
        ])
        api_client.get_user_learning_paths = AsyncMock(return_value={
            "learning_paths": [
                {"id": "path_1", "title": "Python Basics", "status": "completed"},
                {"id": "path_2", "title": "Web Development", "status": "active"}
            ]
        })
        return api_client
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        session_manager = Mock()
        session_manager.get_current_user.return_value = Mock(user_id="test_user")
        return session_manager
    
    @pytest.fixture
    def data_manager(self, mock_api_client, mock_session_manager):
        """Analytics data manager instance"""
        return AnalyticsDataManager(mock_api_client, mock_session_manager)
    
    @pytest.mark.asyncio
    async def test_fetch_user_analytics(self, data_manager):
        """Test fetching user analytics data"""
        analytics_data = await data_manager.fetch_user_analytics("test_user")
        
        assert isinstance(analytics_data, AnalyticsData)
        assert analytics_data.user_id == "test_user"
        assert analytics_data.total_assessments >= 0
        assert analytics_data.total_learning_paths >= 0
        assert isinstance(analytics_data.skill_levels, dict)
        assert isinstance(analytics_data.achievements, list)
    
    @pytest.mark.asyncio
    async def test_fetch_user_assessments(self, data_manager):
        """Test fetching user assessments"""
        assessments = await data_manager._fetch_user_assessments("test_user")
        
        assert isinstance(assessments, list)
        assert len(assessments) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_user_learning_paths(self, data_manager):
        """Test fetching user learning paths"""
        paths = await data_manager._fetch_user_learning_paths("test_user")
        
        assert isinstance(paths, list)
        assert len(paths) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_user_skills(self, data_manager):
        """Test fetching user skills"""
        skills = await data_manager._fetch_user_skills("test_user")
        
        assert isinstance(skills, dict)
        assert len(skills) > 0
        assert all(isinstance(v, float) for v in skills.values())
    
    @pytest.mark.asyncio
    async def test_fetch_user_activity(self, data_manager):
        """Test fetching user activity"""
        activity = await data_manager._fetch_user_activity("test_user")
        
        assert isinstance(activity, dict)
    
    def test_generate_progress_timeline(self, data_manager):
        """Test progress timeline generation"""
        timeline = data_manager._generate_progress_timeline("test_user")
        
        assert isinstance(timeline, list)
        assert len(timeline) == 30  # 30 days
        assert all("date" in item and "progress" in item for item in timeline)
    
    def test_calculate_study_hours(self, data_manager):
        """Test study hours calculation"""
        activity_data = {"day_0_hour_9": 10, "day_1_hour_14": 5}
        
        hours = data_manager._calculate_study_hours(activity_data)
        
        assert isinstance(hours, float)
        assert hours >= 0
    
    def test_calculate_current_streak(self, data_manager):
        """Test current streak calculation"""
        activity_data = {}
        
        streak = data_manager._calculate_current_streak(activity_data)
        
        assert isinstance(streak, int)
        assert streak >= 0
    
    def test_calculate_longest_streak(self, data_manager):
        """Test longest streak calculation"""
        activity_data = {}
        
        streak = data_manager._calculate_longest_streak(activity_data)
        
        assert isinstance(streak, int)
        assert streak >= 0
    
    def test_get_default_analytics_data(self, data_manager):
        """Test default analytics data generation"""
        data = data_manager._get_default_analytics_data("test_user")
        
        assert isinstance(data, AnalyticsData)
        assert data.user_id == "test_user"
        assert data.total_assessments == 0
        assert data.skill_levels == {}


class TestAnalyticsDashboard:
    """Tests for AnalyticsDashboard class"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock API client"""
        return Mock()
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        session_manager = Mock()
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = Mock(user_id="test_user")
        return session_manager
    
    @pytest.fixture
    def dashboard(self, mock_api_client, mock_session_manager):
        """Analytics dashboard instance"""
        return AnalyticsDashboard(mock_api_client, mock_session_manager)
    
    def test_dashboard_initialization(self, dashboard):
        """Test dashboard initialization"""
        assert dashboard.api_client is not None
        assert dashboard.session_manager is not None
        assert dashboard.data_manager is not None
        assert dashboard.chart_renderer is not None
    
    def test_render_analytics_dashboard_authenticated_basic(self, dashboard):
        """Test basic dashboard functionality for authenticated user"""
        # Test that dashboard can be initialized and has required components
        assert dashboard.api_client is not None
        assert dashboard.session_manager is not None
        assert dashboard.data_manager is not None
        assert dashboard.chart_renderer is not None
    
    @patch('streamlit_analytics_components.st')
    def test_render_analytics_dashboard_unauthenticated(self, mock_st, dashboard):
        """Test rendering dashboard for unauthenticated user"""
        dashboard.session_manager.is_authenticated.return_value = False
        
        dashboard.render_analytics_dashboard()
        
        mock_st.warning.assert_called_once_with("🔐 Please log in to view your analytics.")
    
    def test_generate_export_data_basic(self, dashboard):
        """Test basic export data generation"""
        analytics_data = AnalyticsData(
            user_id="test_user",
            total_assessments=5,
            study_hours=25.5
        )
        
        export_data = dashboard._generate_export_data(
            analytics_data, 
            "Basic Analytics", 
            "JSON",
            include_personal=True,
            include_timestamps=True,
            anonymize=False
        )
        
        assert "export_info" in export_data
        assert "user_id" in export_data
        assert "total_assessments" in export_data
        assert export_data["total_assessments"] == 5
        assert export_data["study_hours"] == 25.5
    
    def test_generate_export_data_anonymized(self, dashboard):
        """Test anonymized export data generation"""
        analytics_data = AnalyticsData(user_id="test_user")
        
        export_data = dashboard._generate_export_data(
            analytics_data,
            "Basic Analytics",
            "JSON",
            include_personal=False,
            include_timestamps=True,
            anonymize=True
        )
        
        assert export_data["user_id"] == "user_anonymous"
    
    def test_convert_to_csv(self, dashboard):
        """Test CSV conversion"""
        data = {
            "user_id": "test_user",
            "total_assessments": 5,
            "nested": {"key": "value"}
        }
        
        csv_result = dashboard._convert_to_csv(data)
        
        assert isinstance(csv_result, str)
        assert "Key,Value" in csv_result
        assert "user_id" in csv_result
        assert "test_user" in csv_result


class TestRenderAnalyticsDashboard:
    """Tests for the main render function"""
    
    @patch('streamlit_analytics_components.AnalyticsDashboard')
    def test_render_analytics_dashboard(self, mock_dashboard_class):
        """Test main render function"""
        mock_api_client = Mock()
        mock_session_manager = Mock()
        mock_dashboard_instance = Mock()
        mock_dashboard_class.return_value = mock_dashboard_instance
        
        render_analytics_dashboard(mock_api_client, mock_session_manager)
        
        mock_dashboard_class.assert_called_once_with(mock_api_client, mock_session_manager)
        mock_dashboard_instance.render_analytics_dashboard.assert_called_once()


class TestAchievementDefinitions:
    """Tests for achievement definitions"""
    
    def test_achievement_definitions_structure(self):
        """Test that achievement definitions have required fields"""
        required_fields = ["id", "title", "description", "icon", "category", "target"]
        
        for achievement_def in ACHIEVEMENT_DEFINITIONS:
            for field in required_fields:
                assert field in achievement_def, f"Missing field {field} in achievement {achievement_def.get('id', 'unknown')}"
    
    def test_achievement_definitions_unique_ids(self):
        """Test that achievement IDs are unique"""
        ids = [achievement["id"] for achievement in ACHIEVEMENT_DEFINITIONS]
        assert len(ids) == len(set(ids)), "Achievement IDs must be unique"
    
    def test_achievement_definitions_valid_categories(self):
        """Test that achievement categories are valid"""
        valid_categories = ["assessment", "learning", "streak", "skill", "time", "velocity"]
        
        for achievement_def in ACHIEVEMENT_DEFINITIONS:
            category = achievement_def["category"]
            assert category in valid_categories, f"Invalid category {category} for achievement {achievement_def['id']}"
    
    def test_achievement_definitions_positive_targets(self):
        """Test that achievement targets are positive"""
        for achievement_def in ACHIEVEMENT_DEFINITIONS:
            target = achievement_def["target"]
            assert target > 0, f"Target must be positive for achievement {achievement_def['id']}"


class TestIntegration:
    """Integration tests for analytics components"""
    
    @pytest.fixture
    def mock_components(self):
        """Mock all required components"""
        api_client = Mock()
        session_manager = Mock()
        session_manager.is_authenticated.return_value = True
        session_manager.get_current_user.return_value = Mock(user_id="test_user")
        
        # Mock API responses
        api_client.get_user_assessments = AsyncMock(return_value=[])
        api_client.get_user_learning_paths = AsyncMock(return_value={"learning_paths": []})
        
        return api_client, session_manager
    
    @pytest.mark.asyncio
    async def test_full_analytics_pipeline(self, mock_components):
        """Test complete analytics data pipeline"""
        api_client, session_manager = mock_components
        
        # Create data manager and fetch analytics
        data_manager = AnalyticsDataManager(api_client, session_manager)
        analytics_data = await data_manager.fetch_user_analytics("test_user")
        
        # Verify data structure
        assert isinstance(analytics_data, AnalyticsData)
        assert analytics_data.user_id == "test_user"
        
        # Test chart rendering
        chart_renderer = AnalyticsChartRenderer()
        
        # Test all chart types
        progress_fig = chart_renderer.render_progress_timeline_chart(analytics_data.progress_timeline)
        assert progress_fig is not None
        
        radar_fig = chart_renderer.render_skill_radar_chart(analytics_data.skill_levels)
        assert radar_fig is not None
        
        heatmap_fig = chart_renderer.render_activity_heatmap(analytics_data.activity_data)
        assert heatmap_fig is not None
        
        distribution_fig = chart_renderer.render_skill_distribution_chart(analytics_data.skill_levels)
        assert distribution_fig is not None
        
        velocity_fig = chart_renderer.render_learning_velocity_gauge(analytics_data.learning_velocity)
        assert velocity_fig is not None
    
    def test_dashboard_integration_basic(self, mock_components):
        """Test basic dashboard integration"""
        api_client, session_manager = mock_components
        
        # Create dashboard
        dashboard = AnalyticsDashboard(api_client, session_manager)
        
        # Test that all components are properly initialized
        assert dashboard.api_client == api_client
        assert dashboard.session_manager == session_manager
        assert isinstance(dashboard.data_manager, AnalyticsDataManager)
        assert isinstance(dashboard.chart_renderer, AnalyticsChartRenderer)


if __name__ == "__main__":
    pytest.main([__file__])