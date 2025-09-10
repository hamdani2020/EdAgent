"""
UI/UX Enhancement Demo Script
Demonstrates the key features of the enhanced UI/UX components.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# Import our enhanced UI components
from streamlit_responsive_ui import (
    ResponsiveUIFramework, EnhancedCard, ResponsiveColumns, 
    EnhancedForm, FormValidator
)
from streamlit_enhanced_tables import (
    EnhancedDataTable, ColumnConfig, TableConfig, ColumnType,
    create_user_table, create_assessment_table
)
from streamlit_accessibility import (
    AccessibilityFramework, make_accessible_button, 
    add_skip_links, announce_to_screen_reader
)
from streamlit_enhanced_navigation import (
    EnhancedNavigationSystem, NavigationItem, create_navigation_item,
    render_enhanced_tabs, set_current_navigation_item
)

# Page configuration
st.set_page_config(
    page_title="UI/UX Enhancement Demo",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main demo function"""
    
    # Initialize frameworks
    responsive_ui = ResponsiveUIFramework()
    accessibility_framework = AccessibilityFramework()
    
    # Add skip links
    add_skip_links([
        {"target": "main-content", "text": "Skip to main content"},
        {"target": "demo-sections", "text": "Skip to demo sections"}
    ])
    
    # Main header
    st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)
    st.title("🎨 UI/UX Enhancement Demo")
    st.markdown("Demonstrating responsive design, accessibility, and enhanced user experience components.")
    
    # Demo navigation
    demo_sections = [
        create_navigation_item("responsive", "Responsive Design", "📱"),
        create_navigation_item("forms", "Enhanced Forms", "📝"),
        create_navigation_item("tables", "Interactive Tables", "📊"),
        create_navigation_item("accessibility", "Accessibility", "♿"),
        create_navigation_item("navigation", "Navigation", "🧭")
    ]
    
    st.markdown('<div id="demo-sections"></div>', unsafe_allow_html=True)
    
    # Create tabs for different demos
    tab_labels = [f"{item.icon} {item.label}" for item in demo_sections]
    tabs = st.tabs(tab_labels)
    
    with tabs[0]:
        demo_responsive_design()
    
    with tabs[1]:
        demo_enhanced_forms()
    
    with tabs[2]:
        demo_interactive_tables()
    
    with tabs[3]:
        demo_accessibility_features()
    
    with tabs[4]:
        demo_navigation_features()


def demo_responsive_design():
    """Demonstrate responsive design features"""
    
    with EnhancedCard(title="Responsive Design Demo", icon="📱", elevated=True):
        st.markdown("""
        This demo shows how components adapt to different screen sizes and provide 
        a consistent experience across devices.
        """)
        
        # Responsive columns demo
        st.subheader("Responsive Columns")
        
        with ResponsiveColumns([2, 1, 1]) as cols:
            with cols[0]:
                with EnhancedCard(title="Main Content", compact=True):
                    st.write("This is the main content area that takes up more space on larger screens.")
                    st.write("On mobile devices, this will stack vertically with the sidebar content.")
            
            with cols[1]:
                with EnhancedCard(title="Sidebar 1", compact=True):
                    st.write("Sidebar content that adapts to screen size.")
            
            with cols[2]:
                with EnhancedCard(title="Sidebar 2", compact=True):
                    st.write("Additional sidebar content.")
        
        # Responsive metrics
        st.subheader("Responsive Metrics")
        
        with ResponsiveColumns(4) as cols:
            metrics_data = [
                ("Users", "1,234", "+12%"),
                ("Sessions", "5,678", "+8%"),
                ("Bounce Rate", "23%", "-5%"),
                ("Conversion", "3.4%", "+15%")
            ]
            
            for i, (label, value, delta) in enumerate(metrics_data):
                with cols[i]:
                    with EnhancedCard(compact=True):
                        st.metric(label, value, delta)


def demo_enhanced_forms():
    """Demonstrate enhanced form features"""
    
    with EnhancedCard(title="Enhanced Forms Demo", icon="📝", elevated=True):
        st.markdown("""
        Enhanced forms provide real-time validation, accessibility features, 
        and improved user experience.
        """)
        
        # Form validation demo
        with EnhancedForm(title="User Registration Form", description="Complete the form below to see validation in action") as form:
            
            # Email input with validation
            email = form.email_input(
                "Email Address",
                "demo_email",
                required=True
            )
            
            # Password input with strength validation
            password = form.password_input(
                "Password",
                "demo_password",
                required=True
            )
            
            # Text input with custom validation
            name = form.text_input(
                "Full Name",
                "demo_name",
                placeholder="Enter your full name",
                required=True,
                help_text="This will be displayed on your profile"
            )
            
            # Additional fields
            col1, col2 = st.columns(2)
            
            with col1:
                age = st.number_input(
                    "Age",
                    min_value=13,
                    max_value=120,
                    value=25,
                    key="demo_age"
                )
            
            with col2:
                country = st.selectbox(
                    "Country",
                    ["United States", "Canada", "United Kingdom", "Australia", "Other"],
                    key="demo_country"
                )
            
            # Terms and conditions
            terms_accepted = st.checkbox(
                "I accept the terms and conditions",
                key="demo_terms"
            )
            
            # Submit button with validation
            if form.submit_button("Create Account"):
                if form.is_valid() and terms_accepted:
                    st.success("✅ Account created successfully!")
                    announce_to_screen_reader("Account created successfully", "assertive")
                    
                    # Show form data
                    with st.expander("Form Data"):
                        st.json({
                            "email": email,
                            "name": name,
                            "age": age,
                            "country": country,
                            "terms_accepted": terms_accepted
                        })
                else:
                    if not terms_accepted:
                        st.error("Please accept the terms and conditions")
                    else:
                        st.error("Please fix the validation errors above")


def demo_interactive_tables():
    """Demonstrate interactive table features"""
    
    with EnhancedCard(title="Interactive Tables Demo", icon="📊", elevated=True):
        st.markdown("""
        Enhanced tables provide sorting, filtering, pagination, and accessibility features.
        """)
        
        # Create sample data
        sample_data = pd.DataFrame({
            'id': range(1, 51),
            'name': [f'User {i}' for i in range(1, 51)],
            'email': [f'user{i}@example.com' for i in range(1, 51)],
            'score': [85 + (i % 15) for i in range(1, 51)],
            'active': [i % 3 != 0 for i in range(1, 51)],
            'created_at': pd.date_range('2024-01-01', periods=50, freq='D'),
            'department': [['Engineering', 'Marketing', 'Sales', 'HR'][i % 4] for i in range(50)]
        })
        
        # Create enhanced table
        columns = [
            ColumnConfig("id", "ID", ColumnType.TEXT, width="80px"),
            ColumnConfig("name", "Name", ColumnType.TEXT),
            ColumnConfig("email", "Email", ColumnType.EMAIL),
            ColumnConfig("score", "Score", ColumnType.NUMBER),
            ColumnConfig("active", "Active", ColumnType.BOOLEAN, width="80px"),
            ColumnConfig("created_at", "Created", ColumnType.DATE),
            ColumnConfig("department", "Department", ColumnType.TEXT)
        ]
        
        config = TableConfig(
            page_size=10,
            selectable_rows=True,
            multi_select=True,
            show_search=True,
            show_filters=True,
            show_export=True
        )
        
        table = EnhancedDataTable(sample_data, columns, config, "demo_table")
        
        # Render table
        result = table.render()
        
        # Show selection info
        if result["selected_rows"]:
            selected_data = table.get_selected_data()
            st.info(f"Selected {len(selected_data)} rows")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if make_accessible_button("📊 Analyze Selection", key="analyze_selection"):
                    st.success("Analysis would be performed on selected data")
            
            with col2:
                if make_accessible_button("📥 Export Selection", key="export_selection"):
                    csv = selected_data.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        "selected_data.csv",
                        "text/csv"
                    )
            
            with col3:
                if make_accessible_button("🗑️ Delete Selection", key="delete_selection"):
                    st.warning("Delete operation would be performed")


def demo_accessibility_features():
    """Demonstrate accessibility features"""
    
    with EnhancedCard(title="Accessibility Features Demo", icon="♿", elevated=True):
        st.markdown("""
        Accessibility features ensure the application is usable by everyone, 
        including users with disabilities.
        """)
        
        # Accessible buttons demo
        st.subheader("Accessible Buttons")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if make_accessible_button("Primary Action", key="accessible_primary"):
                st.success("Primary action executed")
                announce_to_screen_reader("Primary action completed", "assertive")
        
        with col2:
            if make_accessible_button("Secondary Action", key="accessible_secondary"):
                st.info("Secondary action executed")
                announce_to_screen_reader("Secondary action completed", "polite")
        
        with col3:
            if make_accessible_button("Disabled Action", key="accessible_disabled", disabled=True):
                pass  # This won't execute
        
        # Screen reader announcements
        st.subheader("Screen Reader Support")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Announce Success", key="announce_success"):
                announce_to_screen_reader("This is a success message", "assertive")
                st.success("Success message announced to screen readers")
        
        with col2:
            if st.button("Announce Info", key="announce_info"):
                announce_to_screen_reader("This is an informational message", "polite")
                st.info("Info message announced to screen readers")
        
        # Keyboard navigation info
        st.subheader("Keyboard Navigation")
        
        with EnhancedCard(compact=True):
            st.markdown("""
            **Keyboard shortcuts supported:**
            - `Tab` / `Shift+Tab`: Navigate between interactive elements
            - `Enter` / `Space`: Activate buttons and links
            - `Arrow keys`: Navigate within components (tables, tabs)
            - `Escape`: Close modals and dropdowns
            - `Home` / `End`: Jump to first/last item in lists
            """)
        
        # Color contrast and visual accessibility
        st.subheader("Visual Accessibility")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**High Contrast Mode Support**")
            st.markdown("Components automatically adapt to high contrast preferences")
            
            # Demo high contrast elements
            st.success("✅ Success message with high contrast support")
            st.error("❌ Error message with high contrast support")
            st.warning("⚠️ Warning message with high contrast support")
        
        with col2:
            st.markdown("**Reduced Motion Support**")
            st.markdown("Animations respect user's motion preferences")
            
            if st.button("Test Animation", key="test_animation"):
                st.balloons()  # This will be reduced if user prefers reduced motion


def demo_navigation_features():
    """Demonstrate navigation features"""
    
    with EnhancedCard(title="Enhanced Navigation Demo", icon="🧭", elevated=True):
        st.markdown("""
        Enhanced navigation provides smooth transitions, breadcrumbs, 
        and improved user experience.
        """)
        
        # Navigation items demo
        st.subheader("Navigation Components")
        
        # Create sample navigation items
        nav_items = [
            create_navigation_item("home", "Home", "🏠", description="Main dashboard"),
            create_navigation_item("profile", "Profile", "👤", description="User settings"),
            create_navigation_item("settings", "Settings", "⚙️", description="App configuration"),
            create_navigation_item("help", "Help", "❓", description="Support and documentation", badge="New")
        ]
        
        # Simulate tab selection
        selected_tab = st.radio(
            "Select a navigation item:",
            options=[item.key for item in nav_items],
            format_func=lambda x: next(item.label for item in nav_items if item.key == x),
            key="nav_demo_selection"
        )
        
        # Show selected item info
        selected_item = next(item for item in nav_items if item.key == selected_tab)
        
        with EnhancedCard(title=f"Selected: {selected_item.label}", icon=selected_item.icon, compact=True):
            st.write(f"**Description:** {selected_item.description}")
            if selected_item.badge:
                st.write(f"**Badge:** {selected_item.badge}")
        
        # Breadcrumb simulation
        st.subheader("Breadcrumb Navigation")
        
        breadcrumb_path = ["Home", "User Management", "Profile Settings"]
        breadcrumb_html = " / ".join([f'<a href="#" style="color: #1f77b4; text-decoration: none;">{item}</a>' if i < len(breadcrumb_path) - 1 else f'<strong>{item}</strong>' for i, item in enumerate(breadcrumb_path)])
        
        st.markdown(f'<div style="padding: 0.5rem; background: #f8f9fa; border-radius: 4px; font-size: 0.875rem;">{breadcrumb_html}</div>', unsafe_allow_html=True)
        
        # Navigation history
        st.subheader("Navigation History")
        
        if "nav_history" not in st.session_state:
            st.session_state.nav_history = ["Home"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Visit Dashboard", key="visit_dashboard"):
                st.session_state.nav_history.append("Dashboard")
                st.rerun()
        
        with col2:
            if st.button("Visit Profile", key="visit_profile"):
                st.session_state.nav_history.append("Profile")
                st.rerun()
        
        with col3:
            if st.button("Go Back", key="go_back"):
                if len(st.session_state.nav_history) > 1:
                    st.session_state.nav_history.pop()
                    st.rerun()
        
        # Show navigation history
        st.write("**Navigation History:**")
        st.write(" → ".join(st.session_state.nav_history))


if __name__ == "__main__":
    main()