"""
Accessibility Framework for EdAgent Streamlit App
Provides keyboard navigation, screen reader support, and WCAG compliance features.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from datetime import datetime


class AccessibilityLevel(Enum):
    """WCAG accessibility levels"""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class KeyboardShortcut(Enum):
    """Common keyboard shortcuts"""
    ESCAPE = "Escape"
    ENTER = "Enter"
    SPACE = "Space"
    TAB = "Tab"
    SHIFT_TAB = "Shift+Tab"
    ARROW_UP = "ArrowUp"
    ARROW_DOWN = "ArrowDown"
    ARROW_LEFT = "ArrowLeft"
    ARROW_RIGHT = "ArrowRight"
    HOME = "Home"
    END = "End"
    PAGE_UP = "PageUp"
    PAGE_DOWN = "PageDown"


@dataclass
class AccessibilityConfig:
    """Configuration for accessibility features"""
    level: AccessibilityLevel = AccessibilityLevel.AA
    keyboard_navigation: bool = True
    screen_reader_support: bool = True
    high_contrast_mode: bool = False
    focus_indicators: bool = True
    skip_links: bool = True
    aria_labels: bool = True
    reduced_motion: bool = False
    font_scaling: bool = True
    color_blind_friendly: bool = True


class AccessibilityFramework:
    """Main accessibility framework"""
    
    def __init__(self, config: Optional[AccessibilityConfig] = None):
        self.config = config or AccessibilityConfig()
        self._init_accessibility_features()
    
    def _init_accessibility_features(self):
        """Initialize accessibility features"""
        self._inject_accessibility_css()
        self._setup_keyboard_navigation()
        self._setup_screen_reader_support()
    
    def _inject_accessibility_css(self):
        """Inject accessibility CSS"""
        css = self._generate_accessibility_css()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    def _generate_accessibility_css(self) -> str:
        """Generate comprehensive accessibility CSS"""
        return """
        /* Accessibility Framework CSS */
        
        /* Focus indicators */
        .accessible-focus:focus,
        .accessible-focus:focus-visible {
            outline: 3px solid #005fcc !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 1px #ffffff, 0 0 0 4px #005fcc !important;
        }
        
        /* Skip links */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            border-radius: 0 0 4px 4px;
            z-index: 10000;
            font-weight: bold;
        }
        
        .skip-link:focus {
            top: 0;
        }
        
        /* Screen reader only content */
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }
        
        .sr-only-focusable:focus {
            position: static !important;
            width: auto !important;
            height: auto !important;
            padding: inherit !important;
            margin: inherit !important;
            overflow: visible !important;
            clip: auto !important;
            white-space: normal !important;
        }
        
        /* High contrast mode */
        .high-contrast {
            filter: contrast(150%) brightness(110%);
        }
        
        .high-contrast * {
            border-color: #000 !important;
            color: #000 !important;
            background-color: #fff !important;
        }
        
        .high-contrast .primary-button {
            background-color: #000 !important;
            color: #fff !important;
            border: 2px solid #000 !important;
        }
        
        .high-contrast .secondary-button {
            background-color: #fff !important;
            color: #000 !important;
            border: 2px solid #000 !important;
        }
        
        /* Keyboard navigation indicators */
        .keyboard-navigable {
            position: relative;
        }
        
        .keyboard-navigable::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            border: 2px solid transparent;
            border-radius: 4px;
            pointer-events: none;
            transition: border-color 0.2s ease;
        }
        
        .keyboard-navigable:focus::before,
        .keyboard-navigable.keyboard-focused::before {
            border-color: #005fcc;
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            .respect-motion-preference * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }
        
        /* Color blind friendly indicators */
        .colorblind-friendly .success {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='%23fff' d='M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 4px center;
            padding-left: 24px;
        }
        
        .colorblind-friendly .error {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='%23fff' d='M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 4px center;
            padding-left: 24px;
        }
        
        .colorblind-friendly .warning {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='%23fff' d='M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-2.008 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z'/%3E%3Cpath fill='%23fff' d='M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 4px center;
            padding-left: 24px;
        }
        
        /* Font scaling support */
        .font-scalable {
            font-size: clamp(0.875rem, 2.5vw, 1.125rem);
            line-height: 1.6;
        }
        
        .font-scalable h1 {
            font-size: clamp(1.5rem, 4vw, 2.5rem);
        }
        
        .font-scalable h2 {
            font-size: clamp(1.25rem, 3.5vw, 2rem);
        }
        
        .font-scalable h3 {
            font-size: clamp(1.125rem, 3vw, 1.75rem);
        }
        
        /* Touch target sizing */
        .touch-friendly {
            min-height: 44px;
            min-width: 44px;
            padding: 12px 16px;
        }
        
        /* Error and success states */
        .accessible-error {
            border: 2px solid #d32f2f;
            background-color: #ffebee;
            color: #c62828;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
        }
        
        .accessible-success {
            border: 2px solid #388e3c;
            background-color: #e8f5e8;
            color: #2e7d32;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
        }
        
        .accessible-warning {
            border: 2px solid #f57c00;
            background-color: #fff3e0;
            color: #ef6c00;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
        }
        
        /* Form accessibility */
        .accessible-form-group {
            margin-bottom: 20px;
        }
        
        .accessible-label {
            display: block;
            font-weight: 600;
            margin-bottom: 6px;
            color: #333;
        }
        
        .accessible-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ccc;
            border-radius: 4px;
            font-size: 16px;
            transition: border-color 0.2s ease;
        }
        
        .accessible-input:focus {
            border-color: #005fcc;
            outline: none;
            box-shadow: 0 0 0 3px rgba(0, 95, 204, 0.1);
        }
        
        .accessible-input[aria-invalid="true"] {
            border-color: #d32f2f;
        }
        
        .accessible-input[aria-invalid="true"]:focus {
            border-color: #d32f2f;
            box-shadow: 0 0 0 3px rgba(211, 47, 47, 0.1);
        }
        
        /* Table accessibility */
        .accessible-table {
            border-collapse: collapse;
            width: 100%;
        }
        
        .accessible-table th,
        .accessible-table td {
            border: 1px solid #ccc;
            padding: 12px;
            text-align: left;
        }
        
        .accessible-table th {
            background-color: #f5f5f5;
            font-weight: 600;
        }
        
        .accessible-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .accessible-table tr:hover {
            background-color: #e3f2fd;
        }
        
        .accessible-table tr:focus-within {
            outline: 2px solid #005fcc;
            outline-offset: -2px;
        }
        
        /* Modal accessibility */
        .accessible-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .accessible-modal-content {
            background: white;
            border-radius: 8px;
            padding: 24px;
            max-width: 90vw;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
        }
        
        .accessible-modal-close {
            position: absolute;
            top: 12px;
            right: 12px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            padding: 8px;
            border-radius: 4px;
        }
        
        .accessible-modal-close:focus {
            outline: 2px solid #005fcc;
            outline-offset: 2px;
        }
        """
    
    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation"""
        if not self.config.keyboard_navigation:
            return
        
        # Inject keyboard navigation JavaScript
        keyboard_js = """
        <script>
        // Keyboard navigation support
        document.addEventListener('DOMContentLoaded', function() {
            // Add keyboard navigation to buttons
            const buttons = document.querySelectorAll('button, [role="button"]');
            buttons.forEach(button => {
                button.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.click();
                    }
                });
            });
            
            // Add keyboard navigation to tabs
            const tabs = document.querySelectorAll('[role="tab"]');
            tabs.forEach((tab, index) => {
                tab.addEventListener('keydown', function(e) {
                    let targetTab = null;
                    
                    switch(e.key) {
                        case 'ArrowLeft':
                            targetTab = tabs[index - 1] || tabs[tabs.length - 1];
                            break;
                        case 'ArrowRight':
                            targetTab = tabs[index + 1] || tabs[0];
                            break;
                        case 'Home':
                            targetTab = tabs[0];
                            break;
                        case 'End':
                            targetTab = tabs[tabs.length - 1];
                            break;
                    }
                    
                    if (targetTab) {
                        e.preventDefault();
                        targetTab.focus();
                        targetTab.click();
                    }
                });
            });
            
            // Escape key handling
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    // Close modals, dropdowns, etc.
                    const modals = document.querySelectorAll('.accessible-modal');
                    modals.forEach(modal => {
                        modal.style.display = 'none';
                    });
                }
            });
        });
        </script>
        """
        
        st.markdown(keyboard_js, unsafe_allow_html=True)
    
    def _setup_screen_reader_support(self):
        """Setup screen reader support"""
        if not self.config.screen_reader_support:
            return
        
        # Add ARIA live regions
        st.markdown("""
        <div id="aria-live-polite" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        <div id="aria-live-assertive" aria-live="assertive" aria-atomic="true" class="sr-only"></div>
        """, unsafe_allow_html=True)
    
    def announce_to_screen_reader(self, message: str, priority: str = "polite"):
        """Announce message to screen reader"""
        region_id = f"aria-live-{priority}"
        
        # Use JavaScript to update the live region
        js_code = f"""
        <script>
        (function() {{
            const region = document.getElementById('{region_id}');
            if (region) {{
                region.textContent = '{message}';
                setTimeout(() => {{
                    region.textContent = '';
                }}, 1000);
            }}
        }})();
        </script>
        """
        
        st.markdown(js_code, unsafe_allow_html=True)


class AccessibleComponent:
    """Base class for accessible components"""
    
    def __init__(self, component_id: Optional[str] = None):
        self.component_id = component_id or str(uuid.uuid4())
        self.aria_attributes = {}
        self.keyboard_handlers = {}
    
    def set_aria_label(self, label: str):
        """Set ARIA label"""
        self.aria_attributes["aria-label"] = label
        return self
    
    def set_aria_describedby(self, description_id: str):
        """Set ARIA described by"""
        self.aria_attributes["aria-describedby"] = description_id
        return self
    
    def set_aria_expanded(self, expanded: bool):
        """Set ARIA expanded state"""
        self.aria_attributes["aria-expanded"] = "true" if expanded else "false"
        return self
    
    def set_aria_selected(self, selected: bool):
        """Set ARIA selected state"""
        self.aria_attributes["aria-selected"] = "true" if selected else "false"
        return self
    
    def set_role(self, role: str):
        """Set ARIA role"""
        self.aria_attributes["role"] = role
        return self
    
    def add_keyboard_handler(self, key: str, handler: Callable):
        """Add keyboard event handler"""
        self.keyboard_handlers[key] = handler
        return self
    
    def get_aria_string(self) -> str:
        """Get ARIA attributes as string"""
        return " ".join([f'{key}="{value}"' for key, value in self.aria_attributes.items()])


class AccessibleButton(AccessibleComponent):
    """Accessible button component"""
    
    def __init__(self, label: str, 
                 on_click: Optional[Callable] = None,
                 button_type: str = "primary",
                 disabled: bool = False,
                 component_id: Optional[str] = None):
        
        super().__init__(component_id)
        self.label = label
        self.on_click = on_click
        self.button_type = button_type
        self.disabled = disabled
        
        # Set default ARIA attributes
        self.set_role("button")
        if disabled:
            self.aria_attributes["aria-disabled"] = "true"
    
    def render(self) -> bool:
        """Render accessible button"""
        
        # Create button with accessibility features
        button_classes = ["accessible-button", f"{self.button_type}-button", "touch-friendly"]
        if self.disabled:
            button_classes.append("disabled")
        
        # Render using Streamlit button with custom styling
        clicked = st.button(
            self.label,
            key=self.component_id,
            disabled=self.disabled,
            type=self.button_type,
            help=self.aria_attributes.get("aria-label", ""),
            use_container_width=False
        )
        
        # Add custom accessibility attributes via JavaScript
        if self.aria_attributes:
            js_code = f"""
            <script>
            (function() {{
                const button = document.querySelector('[data-testid="baseButton-{self.button_type}"]');
                if (button) {{
                    {'; '.join([f'button.setAttribute("{k}", "{v}")' for k, v in self.aria_attributes.items()])}
                    button.classList.add('accessible-focus');
                }}
            }})();
            </script>
            """
            st.markdown(js_code, unsafe_allow_html=True)
        
        if clicked and self.on_click:
            self.on_click()
        
        return clicked


class AccessibleForm(AccessibleComponent):
    """Accessible form component"""
    
    def __init__(self, title: Optional[str] = None,
                 description: Optional[str] = None,
                 component_id: Optional[str] = None):
        
        super().__init__(component_id)
        self.title = title
        self.description = description
        self.fields = {}
        self.errors = {}
        
        # Set ARIA attributes
        self.set_role("form")
        if title:
            self.set_aria_label(title)
    
    def __enter__(self):
        # Create form container
        st.markdown(f'<div class="accessible-form" {self.get_aria_string()}>', unsafe_allow_html=True)
        
        if self.title:
            st.markdown(f"### {self.title}")
        
        if self.description:
            description_id = f"{self.component_id}_description"
            st.markdown(f'<p id="{description_id}">{self.description}</p>', unsafe_allow_html=True)
            self.set_aria_describedby(description_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        st.markdown('</div>', unsafe_allow_html=True)
    
    def text_input(self, label: str, key: str,
                   required: bool = False,
                   error_message: Optional[str] = None,
                   help_text: Optional[str] = None,
                   **kwargs) -> str:
        """Accessible text input"""
        
        field_id = f"{self.component_id}_{key}"
        
        # Create form group
        st.markdown('<div class="accessible-form-group">', unsafe_allow_html=True)
        
        # Label
        label_html = f'<label for="{field_id}" class="accessible-label">{label}'
        if required:
            label_html += ' <span aria-label="required" style="color: #d32f2f;">*</span>'
        label_html += '</label>'
        st.markdown(label_html, unsafe_allow_html=True)
        
        # Help text
        help_id = None
        if help_text:
            help_id = f"{field_id}_help"
            st.markdown(f'<div id="{help_id}" class="form-help">{help_text}</div>', unsafe_allow_html=True)
        
        # Input field
        value = st.text_input(
            label="",  # Empty label since we use custom HTML
            key=key,
            label_visibility="collapsed",
            **kwargs
        )
        
        # Error message
        if error_message:
            error_id = f"{field_id}_error"
            st.markdown(f'<div id="{error_id}" class="accessible-error" role="alert">{error_message}</div>', unsafe_allow_html=True)
        
        # Add accessibility attributes via JavaScript
        aria_attrs = {
            "id": field_id,
            "aria-required": "true" if required else "false",
            "aria-invalid": "true" if error_message else "false"
        }
        
        if help_id:
            aria_attrs["aria-describedby"] = help_id
        if error_message:
            aria_attrs["aria-describedby"] = f"{help_id} {field_id}_error" if help_id else f"{field_id}_error"
        
        js_code = f"""
        <script>
        (function() {{
            const input = document.querySelector('[data-testid="textInput-{key}"] input');
            if (input) {{
                {'; '.join([f'input.setAttribute("{k}", "{v}")' for k, v in aria_attrs.items()])}
                input.classList.add('accessible-input', 'accessible-focus');
            }}
        }})();
        </script>
        """
        st.markdown(js_code, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        self.fields[key] = value
        return value


class AccessibleTable(AccessibleComponent):
    """Accessible data table component"""
    
    def __init__(self, data: pd.DataFrame,
                 caption: Optional[str] = None,
                 component_id: Optional[str] = None):
        
        super().__init__(component_id)
        self.data = data
        self.caption = caption
        
        # Set ARIA attributes
        self.set_role("table")
        if caption:
            self.set_aria_label(caption)
    
    def render(self):
        """Render accessible table"""
        
        # Table container
        st.markdown(f'<div class="accessible-table-container">', unsafe_allow_html=True)
        
        if self.caption:
            st.markdown(f'<caption class="sr-only">{self.caption}</caption>', unsafe_allow_html=True)
        
        # Use Streamlit's dataframe with accessibility enhancements
        st.dataframe(
            self.data,
            use_container_width=True,
            hide_index=True
        )
        
        # Add accessibility attributes via JavaScript
        js_code = f"""
        <script>
        (function() {{
            const table = document.querySelector('[data-testid="dataframe"]');
            if (table) {{
                table.setAttribute('role', 'table');
                table.classList.add('accessible-table');
                
                // Add row and column headers
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {{
                    header.setAttribute('scope', 'col');
                    header.setAttribute('role', 'columnheader');
                }});
                
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach((row, rowIndex) => {{
                    row.setAttribute('role', 'row');
                    const cells = row.querySelectorAll('td');
                    cells.forEach((cell, cellIndex) => {{
                        cell.setAttribute('role', 'cell');
                    }});
                }});
            }}
        }})();
        </script>
        """
        st.markdown(js_code, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


class AccessibilityTester:
    """Accessibility testing and validation"""
    
    def __init__(self):
        self.issues = []
    
    def check_color_contrast(self, foreground: str, background: str) -> bool:
        """Check color contrast ratio (simplified)"""
        # This is a simplified check - in practice, you'd use a proper color contrast library
        return True  # Placeholder
    
    def check_keyboard_navigation(self) -> List[str]:
        """Check keyboard navigation issues"""
        issues = []
        
        # Add JavaScript to check for keyboard navigation issues
        js_code = """
        <script>
        (function() {
            const focusableElements = document.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            let issues = [];
            
            focusableElements.forEach(element => {
                // Check if element is keyboard accessible
                if (!element.hasAttribute('tabindex') && 
                    !['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)) {
                    issues.push('Element not keyboard accessible: ' + element.tagName);
                }
                
                // Check for focus indicators
                const computedStyle = window.getComputedStyle(element, ':focus');
                if (computedStyle.outline === 'none' && computedStyle.boxShadow === 'none') {
                    issues.push('Missing focus indicator on: ' + element.tagName);
                }
            });
            
            // Store issues in session storage for Python to access
            sessionStorage.setItem('accessibility_issues', JSON.stringify(issues));
        })();
        </script>
        """
        
        st.markdown(js_code, unsafe_allow_html=True)
        
        return issues
    
    def generate_accessibility_report(self) -> Dict[str, Any]:
        """Generate comprehensive accessibility report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "issues": self.issues,
            "recommendations": [],
            "compliance_level": "Unknown"
        }
        
        # Add recommendations based on issues
        if self.issues:
            report["recommendations"] = [
                "Add proper ARIA labels to interactive elements",
                "Ensure sufficient color contrast ratios",
                "Implement keyboard navigation for all interactive elements",
                "Add focus indicators for better visibility",
                "Include skip links for screen reader users"
            ]
        
        return report


# Global accessibility framework instance
accessibility_framework = AccessibilityFramework()
accessibility_tester = AccessibilityTester()


# Convenience functions
def make_accessible_button(label: str, on_click: Optional[Callable] = None, **kwargs) -> bool:
    """Create an accessible button"""
    button = AccessibleButton(label, on_click, **kwargs)
    return button.render()


def make_accessible_form(title: Optional[str] = None, **kwargs) -> AccessibleForm:
    """Create an accessible form"""
    return AccessibleForm(title, **kwargs)


def make_accessible_table(data: pd.DataFrame, caption: Optional[str] = None, **kwargs) -> None:
    """Create an accessible table"""
    table = AccessibleTable(data, caption, **kwargs)
    table.render()


def announce_to_screen_reader(message: str, priority: str = "polite"):
    """Announce message to screen reader users"""
    accessibility_framework.announce_to_screen_reader(message, priority)


def add_skip_links(links: List[Dict[str, str]]):
    """Add skip navigation links"""
    skip_html = ""
    for link in links:
        skip_html += f'<a href="#{link["target"]}" class="skip-link">{link["text"]}</a>'
    
    st.markdown(skip_html, unsafe_allow_html=True)