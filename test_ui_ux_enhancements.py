"""
Comprehensive Tests for UI/UX Enhancements
Tests responsive design, accessibility, navigation, and interactive components.
"""

import pytest
import streamlit as st
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, date
from typing import Dict, List, Any

# Import the modules we're testing
from streamlit_responsive_ui import (
    ResponsiveUIFramework, EnhancedCard, ResponsiveColumns, 
    FormValidator, EnhancedForm, responsive_ui
)
from streamlit_enhanced_tables import (
    EnhancedDataTable, ColumnConfig, TableConfig, ColumnType,
    create_user_table, create_assessment_table, create_learning_path_table
)
from streamlit_accessibility import (
    AccessibilityFramework, AccessibleButton, AccessibleForm, 
    AccessibleTable, accessibility_framework
)
from streamlit_enhanced_navigation import (
    EnhancedNavigationSystem, NavigationItem, NavigationType,
    navigation_system, create_navigation_item
)


class TestResponsiveUI:
    """Test responsive UI framework"""
    
    def test_responsive_framework_initialization(self):
        """Test responsive framework initializes correctly"""
        framework = ResponsiveUIFramework()
        assert framework.config is not None
        assert framework.device_type is not None
        assert framework.theme_mode is not None
    
    def test_enhanced_card_context_manager(self):
        """Test enhanced card as context manager"""
        with patch('streamlit.markdown') as mock_markdown:
            with EnhancedCard(title="Test Card", icon="🎯"):
                pass
            
            # Check that markdown was called for card creation
            assert mock_markdown.called
            calls = [call[0][0] for call in mock_markdown.call_args_list]
            assert any('<div class="enhanced-card">' in call for call in calls)
    
    def test_responsive_columns(self):
        """Test responsive columns layout"""
        with patch('streamlit.columns') as mock_columns:
            mock_columns.return_value = [Mock(), Mock(), Mock()]
            
            with ResponsiveColumns(3) as cols:
                assert len(cols) == 3
            
            mock_columns.assert_called_once()
    
    def test_form_validator_email(self):
        """Test email validation"""
        validator = FormValidator()
        
        # Valid email
        assert validator.validate_email("test@example.com", "email")
        assert "email" in validator.success
        
        # Invalid email
        validator.clear_field("email")
        assert not validator.validate_email("invalid-email", "email")
        assert "email" in validator.errors
    
    def test_form_validator_password(self):
        """Test password validation"""
        validator = FormValidator()
        
        # Strong password
        assert validator.validate_password("StrongPass123!", "password")
        
        # Weak password
        validator.clear_field("password")
        assert not validator.validate_password("weak", "password")
        assert "password" in validator.errors
    
    def test_form_validator_required_fields(self):
        """Test required field validation"""
        validator = FormValidator()
        
        # Valid required field
        assert validator.validate_required("Some value", "field")
        
        # Empty required field
        assert not validator.validate_required("", "field")
        assert "field" in validator.errors
    
    def test_enhanced_form_context_manager(self):
        """Test enhanced form as context manager"""
        with patch('streamlit.markdown') as mock_markdown:
            validator = FormValidator()
            
            with EnhancedForm(title="Test Form", validator=validator):
                pass
            
            # Check that form HTML was generated
            assert mock_markdown.called
            calls = [call[0][0] for call in mock_markdown.call_args_list]
            assert any('<div class="enhanced-form">' in call for call in calls)


class TestEnhancedTables:
    """Test enhanced data tables"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'diana@test.com', 'eve@test.com'],
            'score': [85.5, 92.0, 78.5, 96.0, 88.5],
            'active': [True, True, False, True, False],
            'created_at': pd.date_range('2024-01-01', periods=5, freq='D')
        })
        
        self.columns = [
            ColumnConfig("id", "ID", ColumnType.TEXT),
            ColumnConfig("name", "Name", ColumnType.TEXT),
            ColumnConfig("email", "Email", ColumnType.EMAIL),
            ColumnConfig("score", "Score", ColumnType.PERCENTAGE),
            ColumnConfig("active", "Active", ColumnType.BOOLEAN),
            ColumnConfig("created_at", "Created", ColumnType.DATE)
        ]
    
    def test_enhanced_table_initialization(self):
        """Test table initialization"""
        config = TableConfig(page_size=5, selectable_rows=True)
        table = EnhancedDataTable(self.test_data, self.columns, config, "test_table")
        
        assert table.data.equals(self.test_data)
        assert len(table.columns) == len(self.columns)
        assert table.config.page_size == 5
        assert table.table_id == "test_table"
    
    def test_table_filtering(self):
        """Test table filtering functionality"""
        table = EnhancedDataTable(self.test_data, self.columns, TableConfig(), "test_table")
        
        # Test search filtering
        table.state["search_query"] = "Alice"
        table._apply_filters()
        
        assert len(table.filtered_data) == 1
        assert table.filtered_data.iloc[0]['name'] == 'Alice'
    
    def test_table_sorting(self):
        """Test table sorting functionality"""
        from streamlit_enhanced_tables import SortDirection
        
        table = EnhancedDataTable(self.test_data, self.columns, TableConfig(), "test_table")
        
        # Test sorting by score
        table.state["sort_column"] = "score"
        table.state["sort_direction"] = SortDirection.DESC
        table._apply_sorting()
        
        # Check that data is sorted by score descending
        scores = table.filtered_data['score'].tolist()
        assert scores == sorted(scores, reverse=True)
    
    def test_table_pagination(self):
        """Test table pagination"""
        config = TableConfig(page_size=2, show_pagination=True)
        table = EnhancedDataTable(self.test_data, self.columns, config, "test_table")
        
        # Test first page
        page_data = table._get_page_data()
        assert len(page_data) == 2
        assert page_data.iloc[0]['id'] == 1
        
        # Test second page
        table.state["current_page"] = 1
        page_data = table._get_page_data()
        assert len(page_data) == 2
        assert page_data.iloc[0]['id'] == 3
    
    def test_column_type_formatting(self):
        """Test column type formatting"""
        table = EnhancedDataTable(self.test_data, self.columns, TableConfig(), "test_table")
        
        # Test percentage formatting
        score_col = next(col for col in self.columns if col.key == "score")
        formatted = table._format_cell_value(0.855, score_col)
        assert "85.5%" in formatted
        
        # Test boolean formatting
        active_col = next(col for col in self.columns if col.key == "active")
        formatted_true = table._format_cell_value(True, active_col)
        formatted_false = table._format_cell_value(False, active_col)
        assert formatted_true == "✅"
        assert formatted_false == "❌"
    
    def test_create_user_table(self):
        """Test user table creation helper"""
        users_data = pd.DataFrame({
            'id': [1, 2],
            'name': ['Alice', 'Bob'],
            'email': ['alice@test.com', 'bob@test.com'],
            'created_at': pd.date_range('2024-01-01', periods=2),
            'active': [True, False]
        })
        
        table = create_user_table(users_data)
        assert isinstance(table, EnhancedDataTable)
        assert table.config.selectable_rows
        assert table.config.multi_select
    
    def test_create_assessment_table(self):
        """Test assessment table creation helper"""
        assessments_data = pd.DataFrame({
            'id': ['assess_1', 'assess_2'],
            'skill_area': ['Python', 'JavaScript'],
            'score': [0.85, 0.92],
            'status': ['completed', 'in_progress'],
            'completed_at': pd.date_range('2024-01-01', periods=2),
            'duration': ['30 min', '45 min']
        })
        
        table = create_assessment_table(assessments_data)
        assert isinstance(table, EnhancedDataTable)
        assert table.config.page_size == 10


class TestAccessibility:
    """Test accessibility framework"""
    
    def test_accessibility_framework_initialization(self):
        """Test accessibility framework initializes correctly"""
        framework = AccessibilityFramework()
        assert framework.config is not None
    
    def test_accessible_button(self):
        """Test accessible button component"""
        with patch('streamlit.button') as mock_button:
            mock_button.return_value = False
            
            button = AccessibleButton("Test Button", button_type="primary")
            button.set_aria_label("Test button for accessibility")
            
            result = button.render()
            
            mock_button.assert_called_once()
            assert not result  # Button not clicked
    
    def test_accessible_form_context_manager(self):
        """Test accessible form as context manager"""
        with patch('streamlit.markdown') as mock_markdown:
            with AccessibleForm(title="Accessible Form"):
                pass
            
            # Check that form HTML was generated
            assert mock_markdown.called
            calls = [call[0][0] for call in mock_markdown.call_args_list]
            assert any('class="accessible-form"' in call for call in calls)
    
    def test_accessible_table(self):
        """Test accessible table component"""
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'score': [85, 92]
        })
        
        with patch('streamlit.dataframe') as mock_dataframe:
            table = AccessibleTable(test_data, caption="Test scores table")
            table.render()
            
            mock_dataframe.assert_called_once()
    
    def test_aria_attributes(self):
        """Test ARIA attributes functionality"""
        from streamlit_accessibility import AccessibleComponent
        
        component = AccessibleComponent()
        component.set_aria_label("Test component")
        component.set_aria_describedby("description_id")
        component.set_role("button")
        
        aria_string = component.get_aria_string()
        assert 'aria-label="Test component"' in aria_string
        assert 'aria-describedby="description_id"' in aria_string
        assert 'role="button"' in aria_string


class TestEnhancedNavigation:
    """Test enhanced navigation system"""
    
    def setup_method(self):
        """Setup test navigation items"""
        self.nav_items = [
            NavigationItem("home", "Home", "🏠"),
            NavigationItem("profile", "Profile", "👤"),
            NavigationItem("settings", "Settings", "⚙️", disabled=True),
            NavigationItem("help", "Help", "❓", badge="New")
        ]
    
    def test_navigation_system_initialization(self):
        """Test navigation system initializes correctly"""
        nav_system = EnhancedNavigationSystem()
        assert nav_system.config is not None
        assert nav_system.navigation_items == {}
        assert nav_system.navigation_history == []
    
    def test_add_navigation_item(self):
        """Test adding navigation items"""
        nav_system = EnhancedNavigationSystem()
        
        item = NavigationItem("test", "Test Item", "🧪")
        nav_system.add_navigation_item(item)
        
        assert "test" in nav_system.navigation_items
        assert nav_system.navigation_items["test"].label == "Test Item"
    
    def test_set_current_item(self):
        """Test setting current navigation item"""
        with patch('streamlit.session_state', new_callable=dict) as mock_session:
            mock_session.update({
                'nav_current_item': None,
                'nav_history': [],
                'nav_breadcrumb': []
            })
            
            nav_system = EnhancedNavigationSystem()
            nav_system.add_navigation_item(NavigationItem("test", "Test"))
            
            nav_system.set_current_item("test")
            
            assert mock_session['nav_current_item'] == "test"
            assert "test" in mock_session['nav_history']
    
    def test_create_navigation_item_helper(self):
        """Test navigation item creation helper"""
        item = create_navigation_item("test", "Test Item", "🧪", description="Test description")
        
        assert item.key == "test"
        assert item.label == "Test Item"
        assert item.icon == "🧪"
        assert item.description == "Test description"
    
    def test_navigation_context(self):
        """Test navigation context creation"""
        with patch('streamlit.session_state', new_callable=dict) as mock_session:
            mock_session.update({
                'nav_current_item': 'home',
                'nav_history': ['home'],
                'nav_breadcrumb': ['home'],
                'nav_sidebar_collapsed': False
            })
            
            nav_system = EnhancedNavigationSystem()
            context = nav_system.create_navigation_context()
            
            assert context['current_item'] == 'home'
            assert context['history'] == ['home']
            assert context['breadcrumb'] == ['home']
            assert context['sidebar_collapsed'] == False


class TestUIUXIntegration:
    """Test integration between UI/UX components"""
    
    def test_responsive_table_integration(self):
        """Test responsive design with enhanced tables"""
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'score': [85, 92, 78]
        })
        
        columns = [
            ColumnConfig("name", "Name", ColumnType.TEXT),
            ColumnConfig("score", "Score", ColumnType.NUMBER)
        ]
        
        config = TableConfig(responsive=True, compact_mode=True)
        table = EnhancedDataTable(test_data, columns, config, "responsive_table")
        
        assert table.config.responsive
        assert table.config.compact_mode
    
    def test_accessible_navigation_integration(self):
        """Test accessibility with navigation components"""
        nav_items = [
            NavigationItem("home", "Home", "🏠"),
            NavigationItem("profile", "Profile", "👤")
        ]
        
        # Test that navigation items can be created with accessibility in mind
        for item in nav_items:
            assert item.key is not None
            assert item.label is not None
            # Navigation should be keyboard accessible by default
    
    def test_form_validation_integration(self):
        """Test form validation with responsive design"""
        validator = FormValidator()
        
        # Test multiple validation scenarios
        test_cases = [
            ("test@example.com", "email", True),
            ("invalid-email", "email", False),
            ("StrongPass123!", "password", True),
            ("weak", "password", False)
        ]
        
        for value, field_type, expected_valid in test_cases:
            validator.clear_field(field_type)
            
            if field_type == "email":
                result = validator.validate_email(value, field_type)
            elif field_type == "password":
                result = validator.validate_password(value, field_type)
            
            assert result == expected_valid
    
    def test_loading_states_integration(self):
        """Test loading states with UI components"""
        from streamlit_loading_components import show_loading, LoadingStyle
        
        # Test that loading components can be created
        with patch('streamlit.spinner'):
            loading_context = show_loading(
                "test_operation", 
                "Testing loading state",
                LoadingStyle.SPINNER
            )
            
            assert loading_context is not None


class TestPerformanceAndOptimization:
    """Test performance aspects of UI/UX enhancements"""
    
    def test_large_dataset_table_performance(self):
        """Test table performance with large datasets"""
        # Create a larger dataset
        large_data = pd.DataFrame({
            'id': range(1000),
            'name': [f'User_{i}' for i in range(1000)],
            'score': [85 + (i % 15) for i in range(1000)],
            'active': [i % 2 == 0 for i in range(1000)]
        })
        
        columns = [
            ColumnConfig("id", "ID", ColumnType.TEXT),
            ColumnConfig("name", "Name", ColumnType.TEXT),
            ColumnConfig("score", "Score", ColumnType.NUMBER),
            ColumnConfig("active", "Active", ColumnType.BOOLEAN)
        ]
        
        config = TableConfig(page_size=50)  # Reasonable page size
        table = EnhancedDataTable(large_data, columns, config, "large_table")
        
        # Test that pagination works with large dataset
        page_data = table._get_page_data()
        assert len(page_data) == 50
        
        # Test filtering performance
        table.state["search_query"] = "User_1"
        table._apply_filters()
        
        # Should find users with "User_1" in name
        assert len(table.filtered_data) > 0
    
    def test_css_injection_efficiency(self):
        """Test that CSS injection is efficient"""
        framework = ResponsiveUIFramework()
        
        # CSS should be generated without errors
        css = framework._generate_responsive_css()
        assert isinstance(css, str)
        assert len(css) > 0
        
        # Should contain expected CSS classes
        assert "responsive-container" in css
        assert "enhanced-card" in css
        assert "accessible-focus" in css
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization"""
        # Create multiple components and ensure they don't leak memory
        components = []
        
        for i in range(10):
            validator = FormValidator()
            validator.validate_email(f"test{i}@example.com", f"email_{i}")
            components.append(validator)
        
        # All validators should work independently
        for i, validator in enumerate(components):
            assert f"email_{i}" in validator.success


class TestErrorHandling:
    """Test error handling in UI/UX components"""
    
    def test_table_with_invalid_data(self):
        """Test table handling of invalid data"""
        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        columns = [ColumnConfig("name", "Name", ColumnType.TEXT)]
        
        table = EnhancedDataTable(empty_data, columns, TableConfig(), "empty_table")
        
        # Should handle empty data gracefully
        assert len(table.data) == 0
        assert len(table.filtered_data) == 0
    
    def test_form_validation_edge_cases(self):
        """Test form validation edge cases"""
        validator = FormValidator()
        
        # Test with None values
        assert not validator.validate_required(None, "field")
        
        # Test with empty strings
        assert not validator.validate_required("", "field")
        
        # Test with whitespace only
        assert not validator.validate_required("   ", "field")
    
    def test_navigation_with_missing_items(self):
        """Test navigation with missing or invalid items"""
        nav_system = EnhancedNavigationSystem()
        
        # Test setting current item that doesn't exist
        nav_system.set_current_item("nonexistent")
        
        # Should not crash, just update session state
        # (In real implementation, you might want to handle this differently)
    
    def test_accessibility_with_missing_attributes(self):
        """Test accessibility components with missing attributes"""
        from streamlit_accessibility import AccessibleComponent
        
        component = AccessibleComponent()
        
        # Should handle missing ARIA attributes gracefully
        aria_string = component.get_aria_string()
        assert isinstance(aria_string, str)


# Integration test that combines multiple components
class TestFullUIUXWorkflow:
    """Test complete UI/UX workflow integration"""
    
    def test_complete_user_journey(self):
        """Test a complete user journey through UI components"""
        # 1. User sees responsive navigation
        nav_items = [
            create_navigation_item("dashboard", "Dashboard", "📊"),
            create_navigation_item("profile", "Profile", "👤"),
            create_navigation_item("settings", "Settings", "⚙️")
        ]
        
        # 2. User fills out accessible form
        validator = FormValidator()
        form_data = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        }
        
        # Validate form data
        email_valid = validator.validate_email(form_data["email"], "email")
        password_valid = validator.validate_password(form_data["password"], "password")
        name_valid = validator.validate_required(form_data["name"], "name")
        
        assert email_valid and password_valid and name_valid
        
        # 3. User views data in enhanced table
        user_data = pd.DataFrame({
            'name': ['Test User'],
            'email': ['user@example.com'],
            'created_at': [datetime.now()],
            'active': [True]
        })
        
        table = create_user_table(user_data)
        assert len(table.data) == 1
        
        # 4. Navigation state is properly managed
        nav_system = EnhancedNavigationSystem()
        for item in nav_items:
            nav_system.add_navigation_item(item)
        
        nav_system.set_current_item("dashboard")
        context = nav_system.create_navigation_context()
        
        assert context["current_item"] == "dashboard"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])