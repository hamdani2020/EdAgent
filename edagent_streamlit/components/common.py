"""
Common UI Components for EdAgent Streamlit Application

This module provides reusable UI components that are used across
multiple features with consistent styling and behavior.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass

from ..core.config import get_config
from ..core.logger import get_logger
from ..core.error_handler import create_error_boundary


@dataclass
class CardConfig:
    """Configuration for enhanced cards"""
    title: str
    icon: Optional[str] = None
    elevated: bool = False
    compact: bool = False
    color: Optional[str] = None
    expandable: bool = False


@dataclass
class ButtonConfig:
    """Configuration for enhanced buttons"""
    text: str
    key: str
    type: str = "secondary"
    disabled: bool = False
    help: Optional[str] = None
    use_container_width: bool = False


class CommonComponents:
    """
    Common UI components with consistent styling and accessibility features
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("common_components")
    
    @create_error_boundary("enhanced_card")
    def render_enhanced_card(
        self, 
        config: CardConfig,
        content_func: Optional[Callable] = None
    ) -> None:
        """Render enhanced card with consistent styling"""
        
        # Card styling based on configuration
        card_style = self._get_card_style(config)
        
        # Create card container
        with st.container():
            st.markdown(f'<div class="enhanced-card" style="{card_style}">', unsafe_allow_html=True)
            
            # Card header
            if config.title:
                header_html = f"""
                <div class="card-header">
                    {config.icon + ' ' if config.icon else ''}<strong>{config.title}</strong>
                </div>
                """
                st.markdown(header_html, unsafe_allow_html=True)
            
            # Card content
            if content_func:
                content_func()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _get_card_style(self, config: CardConfig) -> str:
        """Generate CSS style for card"""
        base_style = """
            background-color: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            border: 1px solid #e0e0e0;
            transition: all 0.3s ease;
        """
        
        if config.elevated:
            base_style += "box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
        
        if config.compact:
            base_style += "padding: 1rem;"
        
        if config.color:
            base_style += f"border-left: 4px solid {config.color};"
        
        return base_style
    
    @create_error_boundary("enhanced_button")
    def render_enhanced_button(self, config: ButtonConfig) -> bool:
        """Render enhanced button with accessibility features"""
        
        # Add accessibility attributes
        button_kwargs = {
            "key": config.key,
            "type": config.type,
            "disabled": config.disabled,
            "use_container_width": config.use_container_width
        }
        
        if config.help:
            button_kwargs["help"] = config.help
        
        return st.button(config.text, **button_kwargs)
    
    @create_error_boundary("responsive_columns")
    def render_responsive_columns(self, ratios: List[Union[int, float]]) -> List:
        """Render responsive columns that adapt to screen size"""
        
        # For mobile, stack columns vertically
        if self._is_mobile_view():
            return [st.container() for _ in ratios]
        
        # For desktop, use specified ratios
        return st.columns(ratios)
    
    def _is_mobile_view(self) -> bool:
        """Detect if user is on mobile device (simplified)"""
        # This is a simplified check - in production, you might use
        # JavaScript injection to detect actual screen size
        return False  # Default to desktop layout
    
    @create_error_boundary("loading_spinner")
    def render_loading_spinner(
        self, 
        message: str = "Loading...",
        show_progress: bool = False,
        progress_value: Optional[float] = None
    ) -> None:
        """Render loading spinner with optional progress"""
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if show_progress and progress_value is not None:
                st.progress(progress_value)
                st.markdown(f"<div style='text-align: center; margin-top: 10px;'>{message}</div>", 
                           unsafe_allow_html=True)
            else:
                with st.spinner(message):
                    # Small delay to show spinner
                    import time
                    time.sleep(0.1)
    
    @create_error_boundary("status_indicator")
    def render_status_indicator(
        self, 
        status: str, 
        message: str,
        show_timestamp: bool = True
    ) -> None:
        """Render status indicator with consistent styling"""
        
        status_config = {
            "success": {"icon": "✅", "color": "#28a745"},
            "error": {"icon": "❌", "color": "#dc3545"},
            "warning": {"icon": "⚠️", "color": "#ffc107"},
            "info": {"icon": "ℹ️", "color": "#17a2b8"},
            "loading": {"icon": "⏳", "color": "#6c757d"}
        }
        
        config = status_config.get(status, status_config["info"])
        
        timestamp_str = ""
        if show_timestamp:
            timestamp_str = f" • {datetime.now().strftime('%H:%M:%S')}"
        
        status_html = f"""
        <div style="
            display: flex; 
            align-items: center; 
            padding: 0.5rem; 
            border-left: 3px solid {config['color']};
            background-color: {config['color']}10;
            margin: 0.5rem 0;
            border-radius: 4px;
        ">
            <span style="margin-right: 0.5rem; font-size: 1.2em;">{config['icon']}</span>
            <span>{message}{timestamp_str}</span>
        </div>
        """
        
        st.markdown(status_html, unsafe_allow_html=True)
    
    @create_error_boundary("data_table")
    def render_enhanced_data_table(
        self, 
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        sortable: bool = True,
        searchable: bool = True,
        paginated: bool = True,
        page_size: int = 10
    ) -> None:
        """Render enhanced data table with sorting, search, and pagination"""
        
        if not data:
            st.info("No data available")
            return
        
        # Convert to DataFrame for easier manipulation
        import pandas as pd
        df = pd.DataFrame(data)
        
        if columns:
            df = df[columns]
        
        # Search functionality
        if searchable:
            search_term = st.text_input("🔍 Search", key="table_search")
            if search_term:
                # Simple text search across all columns
                mask = df.astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                df = df[mask]
        
        # Sorting functionality
        if sortable and not df.empty:
            sort_column = st.selectbox("Sort by", options=df.columns.tolist(), key="table_sort")
            sort_order = st.radio("Order", ["Ascending", "Descending"], key="table_order")
            
            ascending = sort_order == "Ascending"
            df = df.sort_values(by=sort_column, ascending=ascending)
        
        # Pagination
        if paginated and len(df) > page_size:
            total_pages = (len(df) - 1) // page_size + 1
            page = st.selectbox(
                f"Page (showing {page_size} of {len(df)} items)", 
                options=list(range(1, total_pages + 1)),
                key="table_page"
            )
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            df = df.iloc[start_idx:end_idx]
        
        # Display table
        st.dataframe(df, use_container_width=True)
    
    @create_error_boundary("metric_cards")
    def render_metric_cards(self, metrics: List[Dict[str, Any]]) -> None:
        """Render metric cards in responsive grid"""
        
        if not metrics:
            return
        
        # Calculate number of columns based on metrics count
        num_metrics = len(metrics)
        if num_metrics <= 2:
            cols = st.columns(num_metrics)
        elif num_metrics <= 4:
            cols = st.columns(2)
        else:
            cols = st.columns(3)
        
        for i, metric in enumerate(metrics):
            col_idx = i % len(cols)
            
            with cols[col_idx]:
                # Metric card styling
                card_html = f"""
                <div class="metric-card" style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    text-align: center;
                    margin-bottom: 1rem;
                ">
                    <div style="font-size: 2rem; font-weight: bold; color: {self.config.ui.primary_color};">
                        {metric.get('value', 'N/A')}
                    </div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                        {metric.get('label', 'Metric')}
                    </div>
                    {f'<div style="font-size: 0.8rem; color: #28a745; margin-top: 0.25rem;">↗ {metric.get("delta", "")}</div>' if metric.get('delta') else ''}
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
    
    @create_error_boundary("progress_bar")
    def render_enhanced_progress_bar(
        self, 
        value: float, 
        max_value: float = 100.0,
        label: Optional[str] = None,
        show_percentage: bool = True,
        color: Optional[str] = None
    ) -> None:
        """Render enhanced progress bar with customization"""
        
        percentage = (value / max_value) * 100
        color = color or self.config.ui.primary_color
        
        progress_html = f"""
        <div style="margin: 1rem 0;">
            {f'<div style="margin-bottom: 0.5rem; font-weight: 500;">{label}</div>' if label else ''}
            <div style="
                background-color: #e9ecef;
                border-radius: 10px;
                height: 20px;
                overflow: hidden;
            ">
                <div style="
                    background-color: {color};
                    height: 100%;
                    width: {percentage}%;
                    border-radius: 10px;
                    transition: width 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">
                    {f'{percentage:.1f}%' if show_percentage and percentage > 20 else ''}
                </div>
            </div>
            {f'<div style="text-align: right; font-size: 0.8rem; color: #666; margin-top: 0.25rem;">{value:.1f} / {max_value:.1f}</div>' if not show_percentage else ''}
        </div>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)
    
    @create_error_boundary("notification_toast")
    def render_notification_toast(
        self, 
        message: str, 
        type: str = "info",
        duration: int = 5,
        dismissible: bool = True
    ) -> None:
        """Render notification toast"""
        
        toast_config = {
            "success": {"icon": "✅", "color": "#28a745", "bg": "#d4edda"},
            "error": {"icon": "❌", "color": "#dc3545", "bg": "#f8d7da"},
            "warning": {"icon": "⚠️", "color": "#856404", "bg": "#fff3cd"},
            "info": {"icon": "ℹ️", "color": "#0c5460", "bg": "#d1ecf1"}
        }
        
        config = toast_config.get(type, toast_config["info"])
        
        toast_html = f"""
        <div class="notification-toast" style="
            background-color: {config['bg']};
            color: {config['color']};
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid {config['color']}40;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div style="display: flex; align-items: center;">
                <span style="margin-right: 0.5rem; font-size: 1.2em;">{config['icon']}</span>
                <span>{message}</span>
            </div>
            {f'<button onclick="this.parentElement.style.display=\'none\'" style="background: none; border: none; font-size: 1.2em; cursor: pointer; color: {config["color"]};">×</button>' if dismissible else ''}
        </div>
        """
        
        st.markdown(toast_html, unsafe_allow_html=True)
    
    @create_error_boundary("chart_container")
    def render_chart_container(
        self, 
        chart_func: Callable,
        title: Optional[str] = None,
        description: Optional[str] = None,
        fullscreen: bool = True
    ) -> None:
        """Render chart in enhanced container"""
        
        with st.container():
            if title:
                st.subheader(title)
            
            if description:
                st.caption(description)
            
            # Chart container with styling
            chart_container = st.container()
            
            with chart_container:
                try:
                    chart = chart_func()
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                except Exception as e:
                    self.logger.error(f"Chart rendering error: {e}")
                    st.error("Unable to render chart. Please try again.")
    
    @create_error_boundary("form_validator")
    def render_form_with_validation(
        self, 
        form_key: str,
        fields: List[Dict[str, Any]],
        submit_text: str = "Submit",
        validation_rules: Optional[Dict[str, Callable]] = None
    ) -> Optional[Dict[str, Any]]:
        """Render form with built-in validation"""
        
        with st.form(form_key):
            form_data = {}
            validation_errors = {}
            
            # Render form fields
            for field in fields:
                field_type = field.get("type", "text")
                field_key = field["key"]
                field_label = field.get("label", field_key.title())
                field_required = field.get("required", False)
                
                # Render field based on type
                if field_type == "text":
                    value = st.text_input(
                        field_label,
                        value=field.get("default", ""),
                        placeholder=field.get("placeholder", ""),
                        help=field.get("help")
                    )
                elif field_type == "textarea":
                    value = st.text_area(
                        field_label,
                        value=field.get("default", ""),
                        placeholder=field.get("placeholder", ""),
                        help=field.get("help")
                    )
                elif field_type == "number":
                    value = st.number_input(
                        field_label,
                        value=field.get("default", 0),
                        min_value=field.get("min_value"),
                        max_value=field.get("max_value"),
                        help=field.get("help")
                    )
                elif field_type == "select":
                    value = st.selectbox(
                        field_label,
                        options=field.get("options", []),
                        index=field.get("default_index", 0),
                        help=field.get("help")
                    )
                elif field_type == "multiselect":
                    value = st.multiselect(
                        field_label,
                        options=field.get("options", []),
                        default=field.get("default", []),
                        help=field.get("help")
                    )
                elif field_type == "checkbox":
                    value = st.checkbox(
                        field_label,
                        value=field.get("default", False),
                        help=field.get("help")
                    )
                else:
                    value = st.text_input(field_label)
                
                form_data[field_key] = value
                
                # Validate field
                if field_required and not value:
                    validation_errors[field_key] = f"{field_label} is required"
                
                # Custom validation
                if validation_rules and field_key in validation_rules:
                    try:
                        validation_rules[field_key](value)
                    except ValueError as e:
                        validation_errors[field_key] = str(e)
            
            # Submit button
            submitted = st.form_submit_button(submit_text, type="primary")
            
            if submitted:
                if validation_errors:
                    for field, error in validation_errors.items():
                        st.error(f"❌ {error}")
                    return None
                else:
                    return form_data
        
        return None
    
    def inject_custom_css(self) -> None:
        """Inject custom CSS for enhanced components"""
        
        css = f"""
        <style>
        /* Enhanced Card Styles */
        .enhanced-card {{
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .enhanced-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
        }}
        
        .card-header {{
            font-size: 1.1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        /* Metric Card Styles */
        .metric-card {{
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
        }}
        
        /* Button Enhancements */
        .stButton > button {{
            border-radius: 8px;
            border: none;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            min-height: 44px;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        /* Form Enhancements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            padding: 0.75rem;
            transition: border-color 0.2s ease;
            min-height: 44px;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {{
            border-color: {self.config.ui.primary_color};
            box-shadow: 0 0 0 3px {self.config.ui.primary_color}20;
        }}
        
        /* Notification Toast Animation */
        .notification-toast {{
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .enhanced-card {{
                padding: 1rem;
                margin: 0.25rem 0;
            }}
            
            .metric-card {{
                padding: 1rem;
                margin-bottom: 0.5rem;
            }}
            
            .stButton > button {{
                width: 100%;
                padding: 1rem;
            }}
        }}
        
        /* Accessibility Enhancements */
        @media (prefers-contrast: high) {{
            .enhanced-card,
            .metric-card {{
                border: 2px solid #000;
            }}
        }}
        
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        
        /* Focus indicators for accessibility */
        .stButton > button:focus,
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {{
            outline: 2px solid {self.config.ui.primary_color};
            outline-offset: 2px;
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)