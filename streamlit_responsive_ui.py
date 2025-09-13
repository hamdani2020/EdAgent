"""
Responsive UI Framework for EdAgent Streamlit App
Provides responsive design, consistent theming, and enhanced user experience components.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime


class DeviceType(Enum):
    """Device type detection"""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


class ThemeMode(Enum):
    """Theme modes"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class ResponsiveConfig:
    """Configuration for responsive behavior"""
    mobile_breakpoint: int = 768
    tablet_breakpoint: int = 1024
    sidebar_collapse_mobile: bool = True
    compact_mode_mobile: bool = True
    touch_friendly_mobile: bool = True


class ResponsiveUIFramework:
    """Main responsive UI framework"""
    
    def __init__(self, config: Optional[ResponsiveConfig] = None):
        self.config = config or ResponsiveConfig()
        self.device_type = self._detect_device_type()
        self.theme_mode = self._get_theme_mode()
        self._inject_responsive_css()
    
    def _detect_device_type(self) -> DeviceType:
        """Detect device type based on viewport"""
        # In Streamlit, we use CSS media queries for responsive behavior
        # This is a placeholder for device detection logic
        return DeviceType.DESKTOP
    
    def _get_theme_mode(self) -> ThemeMode:
        """Get current theme mode"""
        return st.session_state.get("theme_mode", ThemeMode.LIGHT)
    
    def _inject_responsive_css(self):
        """Inject responsive CSS styles"""
        css = self._generate_responsive_css()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    def _generate_responsive_css(self) -> str:
        """Generate comprehensive responsive CSS"""
        return """
        /* Responsive Framework CSS */
        
        /* Base responsive grid */
        .responsive-container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        .responsive-grid {
            display: grid;
            gap: 1rem;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .responsive-flex {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: stretch;
        }
        
        .responsive-flex > * {
            flex: 1;
            min-width: 250px;
        }
        
        /* Mobile-first responsive design */
        @media (max-width: 768px) {
            .responsive-container {
                padding: 0 0.5rem;
            }
            
            .responsive-grid {
                grid-template-columns: 1fr;
                gap: 0.5rem;
            }
            
            .responsive-flex {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .responsive-flex > * {
                min-width: unset;
            }
            
            /* Mobile-specific styles */
            .mobile-hidden {
                display: none !important;
            }
            
            .mobile-full-width {
                width: 100% !important;
            }
            
            .mobile-compact {
                padding: 0.5rem !important;
                margin: 0.25rem 0 !important;
            }
            
            /* Touch-friendly buttons */
            .stButton > button {
                min-height: 44px !important;
                padding: 0.75rem 1rem !important;
                font-size: 1rem !important;
            }
            
            /* Larger form inputs */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                min-height: 44px !important;
                font-size: 1rem !important;
                padding: 0.75rem !important;
            }
        }
        
        @media (min-width: 769px) and (max-width: 1024px) {
            /* Tablet styles */
            .responsive-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .tablet-hidden {
                display: none !important;
            }
        }
        
        @media (min-width: 1025px) {
            /* Desktop styles */
            .desktop-only {
                display: block !important;
            }
            
            .mobile-only,
            .tablet-only {
                display: none !important;
            }
        }
        
        /* Enhanced card components */
        .enhanced-card {
            background: var(--background-color, #ffffff);
            border: 1px solid var(--border-color, #e0e0e0);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            margin-bottom: 1rem;
        }
        
        .enhanced-card:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }
        
        .enhanced-card.compact {
            padding: 1rem;
            border-radius: 8px;
        }
        
        .enhanced-card.elevated {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        /* Form enhancements */
        .enhanced-form {
            background: var(--background-color, #ffffff);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid var(--border-color, #e0e0e0);
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: block;
            color: var(--text-color, #333);
        }
        
        .form-help {
            font-size: 0.875rem;
            color: var(--secondary-text-color, #666);
            margin-top: 0.25rem;
        }
        
        .form-error {
            color: var(--error-color, #dc3545);
            font-size: 0.875rem;
            margin-top: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .form-success {
            color: var(--success-color, #28a745);
            font-size: 0.875rem;
            margin-top: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        /* Interactive data tables */
        .enhanced-table {
            width: 100%;
            border-collapse: collapse;
            background: var(--background-color, #ffffff);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .enhanced-table th {
            background: var(--primary-color, #1f77b4);
            color: white;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            transition: background-color 0.2s ease;
        }
        
        .enhanced-table th:hover {
            background: var(--primary-dark, #1565c0);
        }
        
        .enhanced-table td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color, #e0e0e0);
            transition: background-color 0.2s ease;
        }
        
        .enhanced-table tr:hover td {
            background: var(--hover-color, #f5f5f5);
        }
        
        .enhanced-table .sortable::after {
            content: " ↕️";
            font-size: 0.8em;
        }
        
        .enhanced-table .sorted-asc::after {
            content: " ↑";
            color: var(--success-color, #28a745);
        }
        
        .enhanced-table .sorted-desc::after {
            content: " ↓";
            color: var(--error-color, #dc3545);
        }
        
        /* Navigation enhancements */
        .enhanced-nav {
            background: var(--background-color, #ffffff);
            border-bottom: 1px solid var(--border-color, #e0e0e0);
            padding: 1rem 0;
            margin-bottom: 2rem;
        }
        
        .nav-tabs {
            display: flex;
            gap: 0.5rem;
            border-bottom: 2px solid var(--border-color, #e0e0e0);
            margin-bottom: 1rem;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }
        
        .nav-tabs::-webkit-scrollbar {
            display: none;
        }
        
        .nav-tab {
            padding: 0.75rem 1.5rem;
            border: none;
            background: transparent;
            color: var(--secondary-text-color, #666);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            white-space: nowrap;
            font-weight: 500;
        }
        
        .nav-tab:hover {
            color: var(--primary-color, #1f77b4);
            background: var(--hover-color, #f5f5f5);
        }
        
        .nav-tab.active {
            color: var(--primary-color, #1f77b4);
            border-bottom-color: var(--primary-color, #1f77b4);
            background: var(--active-color, #e3f2fd);
        }
        
        /* Loading animations */
        .loading-shimmer {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 4px;
        }
        
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        .fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .slide-in {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Accessibility enhancements */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        .focus-visible {
            outline: 2px solid var(--primary-color, #1f77b4);
            outline-offset: 2px;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            .enhanced-card {
                border: 2px solid var(--text-color, #000);
            }
            
            .enhanced-table th {
                border: 1px solid var(--text-color, #000);
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Dark theme support */
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #1e1e1e;
                --text-color: #ffffff;
                --secondary-text-color: #cccccc;
                --border-color: #404040;
                --hover-color: #2a2a2a;
                --active-color: #0d47a1;
                --primary-color: #42a5f5;
                --primary-dark: #1976d2;
                --success-color: #4caf50;
                --error-color: #f44336;
            }
        }
        
        /* Print styles */
        @media print {
            .no-print {
                display: none !important;
            }
            
            .enhanced-card {
                box-shadow: none;
                border: 1px solid #000;
            }
        }
        """
    
    def set_theme_mode(self, mode: ThemeMode):
        """Set theme mode"""
        st.session_state.theme_mode = mode
        self.theme_mode = mode
        self._inject_responsive_css()


class EnhancedCard:
    """Enhanced card component with responsive design"""
    
    def __init__(self, title: Optional[str] = None, 
                 subtitle: Optional[str] = None,
                 compact: bool = False,
                 elevated: bool = False,
                 icon: Optional[str] = None):
        self.title = title
        self.subtitle = subtitle
        self.compact = compact
        self.elevated = elevated
        self.icon = icon
    
    def __enter__(self):
        classes = ["enhanced-card"]
        if self.compact:
            classes.append("compact")
        if self.elevated:
            classes.append("elevated")
        
        st.markdown(f'<div class="{" ".join(classes)}">', unsafe_allow_html=True)
        
        if self.title:
            title_html = f"{self.icon} {self.title}" if self.icon else self.title
            if self.compact:
                st.markdown(f"**{title_html}**")
            else:
                st.markdown(f"### {title_html}")
        
        if self.subtitle:
            st.markdown(f"*{self.subtitle}*")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        st.markdown('</div>', unsafe_allow_html=True)


class ResponsiveColumns:
    """Responsive column layout"""
    
    def __init__(self, columns: Union[int, List[Union[int, float]]], 
                 gap: str = "1rem",
                 mobile_stack: bool = True):
        self.columns = columns
        self.gap = gap
        self.mobile_stack = mobile_stack
        self.cols = None
    
    def __enter__(self):
        if isinstance(self.columns, int):
            self.cols = st.columns(self.columns, gap=self.gap)
        else:
            self.cols = st.columns(self.columns, gap=self.gap)
        
        # Add responsive classes
        if self.mobile_stack:
            st.markdown('<div class="responsive-flex">', unsafe_allow_html=True)
        
        return self.cols
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mobile_stack:
            st.markdown('</div>', unsafe_allow_html=True)


class FormValidator:
    """Enhanced form validation with real-time feedback"""
    
    def __init__(self):
        self.errors: Dict[str, str] = {}
        self.warnings: Dict[str, str] = {}
        self.success: Dict[str, str] = {}
    
    def validate_email(self, email: str, field_name: str = "email") -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email:
            self.errors[field_name] = "Email is required"
            return False
        elif not re.match(pattern, email):
            self.errors[field_name] = "Please enter a valid email address"
            return False
        else:
            self.success[field_name] = "Valid email format"
            return True
    
    def validate_password(self, password: str, field_name: str = "password") -> bool:
        """Validate password strength"""
        if not password:
            self.errors[field_name] = "Password is required"
            return False
        elif len(password) < 8:
            self.errors[field_name] = "Password must be at least 8 characters"
            return False
        elif not re.search(r'[A-Z]', password):
            self.warnings[field_name] = "Consider adding uppercase letters for stronger security"
            return True
        elif not re.search(r'[0-9]', password):
            self.warnings[field_name] = "Consider adding numbers for stronger security"
            return True
        else:
            self.success[field_name] = "Strong password"
            return True
    
    def validate_required(self, value: Any, field_name: str, min_length: int = 1) -> bool:
        """Validate required field"""
        if not value or (isinstance(value, str) and len(value.strip()) < min_length):
            self.errors[field_name] = f"{field_name.replace('_', ' ').title()} is required"
            return False
        else:
            return True
    
    def validate_length(self, value: str, field_name: str, 
                       min_length: int = 0, max_length: int = None) -> bool:
        """Validate string length"""
        if len(value) < min_length:
            self.errors[field_name] = f"Must be at least {min_length} characters"
            return False
        elif max_length and len(value) > max_length:
            self.errors[field_name] = f"Must be no more than {max_length} characters"
            return False
        else:
            return True
    
    def validate_number(self, value: Union[int, float], field_name: str,
                       min_val: Optional[Union[int, float]] = None,
                       max_val: Optional[Union[int, float]] = None) -> bool:
        """Validate numeric value"""
        try:
            num_val = float(value)
            if min_val is not None and num_val < min_val:
                self.errors[field_name] = f"Must be at least {min_val}"
                return False
            elif max_val is not None and num_val > max_val:
                self.errors[field_name] = f"Must be no more than {max_val}"
                return False
            else:
                return True
        except (ValueError, TypeError):
            self.errors[field_name] = "Must be a valid number"
            return False
    
    def show_field_feedback(self, field_name: str):
        """Show validation feedback for a field"""
        if field_name in self.errors:
            st.markdown(
                f'<div class="form-error">❌ {self.errors[field_name]}</div>',
                unsafe_allow_html=True
            )
        elif field_name in self.warnings:
            st.markdown(
                f'<div class="form-warning">⚠️ {self.warnings[field_name]}</div>',
                unsafe_allow_html=True
            )
        elif field_name in self.success:
            st.markdown(
                f'<div class="form-success">✅ {self.success[field_name]}</div>',
                unsafe_allow_html=True
            )
    
    def clear_field(self, field_name: str):
        """Clear validation state for a field"""
        self.errors.pop(field_name, None)
        self.warnings.pop(field_name, None)
        self.success.pop(field_name, None)
    
    def is_valid(self) -> bool:
        """Check if form is valid (no errors)"""
        return len(self.errors) == 0
    
    def get_summary(self) -> Dict[str, int]:
        """Get validation summary"""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "success": len(self.success)
        }


class EnhancedForm:
    """Enhanced form component with validation and accessibility"""
    
    def __init__(self, title: Optional[str] = None, 
                 description: Optional[str] = None,
                 validator: Optional[FormValidator] = None):
        self.title = title
        self.description = description
        self.validator = validator or FormValidator()
        self.fields: Dict[str, Any] = {}
    
    def __enter__(self):
        st.markdown('<div class="enhanced-form">', unsafe_allow_html=True)
        
        if self.title:
            st.markdown(f"### {self.title}")
        
        if self.description:
            st.markdown(self.description)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        st.markdown('</div>', unsafe_allow_html=True)
    
    def text_input(self, label: str, key: str, 
                   placeholder: str = "", 
                   help_text: str = "",
                   required: bool = False,
                   validate_func: Optional[Callable] = None,
                   **kwargs) -> str:
        """Enhanced text input with validation"""
        
        st.markdown(f'<div class="form-group">', unsafe_allow_html=True)
        
        # Label with required indicator
        label_html = f'<label class="form-label">{label}'
        if required:
            label_html += ' <span style="color: red;">*</span>'
        label_html += '</label>'
        st.markdown(label_html, unsafe_allow_html=True)
        
        # Input field
        value = st.text_input(
            label="",  # Empty label since we're using custom HTML
            key=key,
            placeholder=placeholder,
            label_visibility="collapsed",
            **kwargs
        )
        
        # Help text
        if help_text:
            st.markdown(f'<div class="form-help">{help_text}</div>', unsafe_allow_html=True)
        
        # Validation
        if value and validate_func:
            validate_func(value, key)
        elif required:
            self.validator.validate_required(value, key)
        
        # Show feedback
        self.validator.show_field_feedback(key)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        self.fields[key] = value
        return value
    
    def email_input(self, label: str = "Email", key: str = "email",
                    required: bool = True, **kwargs) -> str:
        """Email input with validation"""
        return self.text_input(
            label=label,
            key=key,
            placeholder="Enter your email address",
            help_text="We'll never share your email with anyone else",
            required=required,
            validate_func=self.validator.validate_email,
            **kwargs
        )
    
    def password_input(self, label: str = "Password", key: str = "password",
                       required: bool = True, **kwargs) -> str:
        """Password input with strength validation"""
        
        st.markdown(f'<div class="form-group">', unsafe_allow_html=True)
        
        # Label with required indicator
        label_html = f'<label class="form-label">{label}'
        if required:
            label_html += ' <span style="color: red;">*</span>'
        label_html += '</label>'
        st.markdown(label_html, unsafe_allow_html=True)
        
        # Password input
        value = st.text_input(
            label="",
            key=key,
            type="password",
            placeholder="Enter a strong password",
            label_visibility="collapsed",
            **kwargs
        )
        
        # Password strength indicator
        if value:
            strength = self._calculate_password_strength(value)
            strength_colors = {
                "weak": "#dc3545",
                "fair": "#ffc107", 
                "good": "#17a2b8",
                "strong": "#28a745"
            }
            
            st.markdown(f"""
            <div style="margin: 0.5rem 0;">
                <div style="font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Password strength: <span style="color: {strength_colors[strength['level']]}; font-weight: bold;">
                    {strength['level'].title()}</span>
                </div>
                <div style="background: #e0e0e0; height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: {strength_colors[strength['level']]}; height: 100%; width: {strength['score']}%; transition: width 0.3s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Help text
        st.markdown('<div class="form-help">Use at least 8 characters with a mix of letters, numbers, and symbols</div>', unsafe_allow_html=True)
        
        # Validation
        if value:
            self.validator.validate_password(value, key)
        elif required:
            self.validator.validate_required(value, key)
        
        # Show feedback
        self.validator.show_field_feedback(key)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        self.fields[key] = value
        return value
    
    def _calculate_password_strength(self, password: str) -> Dict[str, Any]:
        """Calculate password strength"""
        score = 0
        
        # Length
        if len(password) >= 8:
            score += 25
        if len(password) >= 12:
            score += 25
        
        # Character types
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'[0-9]', password):
            score += 15
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 10
        
        # Determine level
        if score < 30:
            level = "weak"
        elif score < 60:
            level = "fair"
        elif score < 80:
            level = "good"
        else:
            level = "strong"
        
        return {"score": min(100, score), "level": level}
    
    def submit_button(self, label: str = "Submit", 
                     validate_on_submit: bool = True,
                     **kwargs) -> bool:
        """Enhanced submit button with validation"""
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            submitted = st.button(label, type="primary", use_container_width=True, **kwargs)
        
        if submitted and validate_on_submit:
            if not self.validator.is_valid():
                st.error("Please fix the errors above before submitting")
                return False
        
        return submitted
    
    def get_values(self) -> Dict[str, Any]:
        """Get all form field values"""
        return self.fields.copy()
    
    def is_valid(self) -> bool:
        """Check if form is valid"""
        return self.validator.is_valid()


# Global responsive UI instance
responsive_ui = ResponsiveUIFramework()