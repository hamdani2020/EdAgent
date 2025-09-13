"""
Enhanced Navigation System for EdAgent Streamlit App
Provides smooth transitions, breadcrumbs, and improved navigation UX.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import time
from datetime import datetime


class NavigationType(Enum):
    """Types of navigation"""
    TABS = "tabs"
    SIDEBAR = "sidebar"
    BREADCRUMB = "breadcrumb"
    STEPPER = "stepper"
    DRAWER = "drawer"


class TransitionType(Enum):
    """Animation transition types"""
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM = "zoom"
    NONE = "none"


@dataclass
class NavigationItem:
    """Navigation item configuration"""
    key: str
    label: str
    icon: Optional[str] = None
    description: Optional[str] = None
    disabled: bool = False
    hidden: bool = False
    badge: Optional[str] = None
    children: Optional[List['NavigationItem']] = None
    url: Optional[str] = None
    external: bool = False
    permission_required: Optional[str] = None


@dataclass
class NavigationConfig:
    """Navigation system configuration"""
    show_icons: bool = True
    show_badges: bool = True
    show_descriptions: bool = False
    collapsible: bool = True
    sticky: bool = True
    animated: bool = True
    transition_type: TransitionType = TransitionType.FADE
    transition_duration: float = 0.3
    breadcrumb_separator: str = "/"
    max_breadcrumb_items: int = 5


class EnhancedNavigationSystem:
    """Enhanced navigation system with animations and improved UX"""
    
    def __init__(self, config: Optional[NavigationConfig] = None):
        self.config = config or NavigationConfig()
        self.navigation_items: Dict[str, NavigationItem] = {}
        self.navigation_history: List[str] = []
        self.current_path: List[str] = []
        
        # Initialize session state
        self._init_session_state()
        
        # Inject CSS and JavaScript
        self._inject_navigation_assets()
    
    def _init_session_state(self):
        """Initialize navigation session state"""
        if "nav_current_item" not in st.session_state:
            st.session_state.nav_current_item = None
        
        if "nav_history" not in st.session_state:
            st.session_state.nav_history = []
        
        if "nav_breadcrumb" not in st.session_state:
            st.session_state.nav_breadcrumb = []
        
        if "nav_sidebar_collapsed" not in st.session_state:
            st.session_state.nav_sidebar_collapsed = False
        
        if "nav_transition_active" not in st.session_state:
            st.session_state.nav_transition_active = False
    
    def _inject_navigation_assets(self):
        """Inject CSS and JavaScript for navigation"""
        css = self._generate_navigation_css()
        js = self._generate_navigation_js()
        
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(js, unsafe_allow_html=True)
    
    def _generate_navigation_css(self) -> str:
        """Generate navigation CSS"""
        return f"""
        /* Enhanced Navigation CSS */
        
        /* Navigation container */
        .enhanced-nav-container {{
            position: relative;
            width: 100%;
            background: var(--background-color, #ffffff);
            border-bottom: 1px solid var(--border-color, #e0e0e0);
            z-index: 100;
        }}
        
        .enhanced-nav-container.sticky {{
            position: sticky;
            top: 0;
        }}
        
        /* Tab navigation */
        .enhanced-nav-tabs {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }}
        
        .enhanced-nav-tabs::-webkit-scrollbar {{
            display: none;
        }}
        
        .nav-tab-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border: none;
            background: transparent;
            color: var(--secondary-text-color, #666);
            cursor: pointer;
            border-radius: 8px;
            transition: all {self.config.transition_duration}s ease;
            white-space: nowrap;
            font-weight: 500;
            text-decoration: none;
            position: relative;
            min-height: 44px;
        }}
        
        .nav-tab-item:hover {{
            background: var(--hover-color, #f5f5f5);
            color: var(--primary-color, #1f77b4);
            transform: translateY(-1px);
        }}
        
        .nav-tab-item.active {{
            background: var(--primary-color, #1f77b4);
            color: white;
            box-shadow: 0 2px 8px rgba(31, 119, 180, 0.3);
        }}
        
        .nav-tab-item.disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            pointer-events: none;
        }}
        
        .nav-tab-icon {{
            font-size: 1.2em;
        }}
        
        .nav-tab-badge {{
            background: var(--error-color, #dc3545);
            color: white;
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            margin-left: 0.5rem;
            min-width: 20px;
            text-align: center;
        }}
        
        .nav-tab-description {{
            font-size: 0.875rem;
            opacity: 0.8;
            margin-top: 0.25rem;
        }}
        
        /* Breadcrumb navigation */
        .enhanced-breadcrumb {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--secondary-background-color, #f8f9fa);
            border-bottom: 1px solid var(--border-color, #e0e0e0);
            font-size: 0.875rem;
        }}
        
        .breadcrumb-item {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
            color: var(--secondary-text-color, #666);
            text-decoration: none;
            transition: color 0.2s ease;
        }}
        
        .breadcrumb-item:hover {{
            color: var(--primary-color, #1f77b4);
        }}
        
        .breadcrumb-item.current {{
            color: var(--text-color, #333);
            font-weight: 600;
        }}
        
        .breadcrumb-separator {{
            color: var(--secondary-text-color, #666);
            margin: 0 0.25rem;
        }}
        
        /* Sidebar navigation */
        .enhanced-nav-sidebar {{
            width: 280px;
            height: 100vh;
            background: var(--background-color, #ffffff);
            border-right: 1px solid var(--border-color, #e0e0e0);
            padding: 1rem;
            overflow-y: auto;
            transition: transform {self.config.transition_duration}s ease;
        }}
        
        .enhanced-nav-sidebar.collapsed {{
            transform: translateX(-100%);
        }}
        
        .sidebar-nav-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            margin: 0.25rem 0;
            border-radius: 8px;
            color: var(--text-color, #333);
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        
        .sidebar-nav-item:hover {{
            background: var(--hover-color, #f5f5f5);
            transform: translateX(4px);
        }}
        
        .sidebar-nav-item.active {{
            background: var(--primary-color, #1f77b4);
            color: white;
        }}
        
        .sidebar-nav-group {{
            margin: 1rem 0;
        }}
        
        .sidebar-nav-group-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--secondary-text-color, #666);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
            padding: 0 1rem;
        }}
        
        /* Stepper navigation */
        .enhanced-nav-stepper {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem 1rem;
            background: var(--background-color, #ffffff);
        }}
        
        .stepper-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            flex: 1;
            max-width: 200px;
        }}
        
        .stepper-circle {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--border-color, #e0e0e0);
            color: var(--secondary-text-color, #666);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            transition: all 0.3s ease;
            z-index: 2;
            position: relative;
        }}
        
        .stepper-item.completed .stepper-circle {{
            background: var(--success-color, #28a745);
            color: white;
        }}
        
        .stepper-item.active .stepper-circle {{
            background: var(--primary-color, #1f77b4);
            color: white;
            transform: scale(1.1);
        }}
        
        .stepper-label {{
            margin-top: 0.5rem;
            font-size: 0.875rem;
            text-align: center;
            color: var(--text-color, #333);
        }}
        
        .stepper-line {{
            position: absolute;
            top: 20px;
            left: 50%;
            right: -50%;
            height: 2px;
            background: var(--border-color, #e0e0e0);
            z-index: 1;
        }}
        
        .stepper-item.completed .stepper-line {{
            background: var(--success-color, #28a745);
        }}
        
        .stepper-item:last-child .stepper-line {{
            display: none;
        }}
        
        /* Drawer navigation */
        .enhanced-nav-drawer {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all {self.config.transition_duration}s ease;
        }}
        
        .enhanced-nav-drawer.open {{
            opacity: 1;
            visibility: visible;
        }}
        
        .drawer-content {{
            position: absolute;
            top: 0;
            left: 0;
            width: 320px;
            height: 100%;
            background: var(--background-color, #ffffff);
            padding: 2rem;
            transform: translateX(-100%);
            transition: transform {self.config.transition_duration}s ease;
            overflow-y: auto;
        }}
        
        .enhanced-nav-drawer.open .drawer-content {{
            transform: translateX(0);
        }}
        
        /* Animations */
        .nav-content {{
            transition: all {self.config.transition_duration}s ease;
        }}
        
        .nav-content.fade-enter {{
            opacity: 0;
        }}
        
        .nav-content.fade-enter-active {{
            opacity: 1;
        }}
        
        .nav-content.slide-left-enter {{
            transform: translateX(100%);
        }}
        
        .nav-content.slide-left-enter-active {{
            transform: translateX(0);
        }}
        
        .nav-content.slide-right-enter {{
            transform: translateX(-100%);
        }}
        
        .nav-content.slide-right-enter-active {{
            transform: translateX(0);
        }}
        
        .nav-content.slide-up-enter {{
            transform: translateY(100%);
        }}
        
        .nav-content.slide-up-enter-active {{
            transform: translateY(0);
        }}
        
        .nav-content.zoom-enter {{
            transform: scale(0.8);
            opacity: 0;
        }}
        
        .nav-content.zoom-enter-active {{
            transform: scale(1);
            opacity: 1;
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .enhanced-nav-tabs {{
                padding: 0.5rem;
                gap: 0.25rem;
            }}
            
            .nav-tab-item {{
                padding: 0.5rem 1rem;
                font-size: 0.875rem;
            }}
            
            .enhanced-nav-sidebar {{
                width: 100%;
                position: fixed;
                top: 0;
                left: 0;
                z-index: 1000;
            }}
            
            .enhanced-nav-stepper {{
                flex-direction: column;
                gap: 1rem;
            }}
            
            .stepper-item {{
                flex-direction: row;
                max-width: none;
                width: 100%;
            }}
            
            .stepper-line {{
                top: 50%;
                left: 20px;
                right: auto;
                bottom: -50%;
                width: 2px;
                height: auto;
            }}
        }}
        
        /* Loading states */
        .nav-loading {{
            position: relative;
            overflow: hidden;
        }}
        
        .nav-loading::after {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            animation: nav-loading 1.5s infinite;
        }}
        
        @keyframes nav-loading {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}
        
        /* Focus states for accessibility */
        .nav-tab-item:focus,
        .sidebar-nav-item:focus,
        .breadcrumb-item:focus {{
            outline: 2px solid var(--primary-color, #1f77b4);
            outline-offset: 2px;
        }}
        """
    
    def _generate_navigation_js(self) -> str:
        """Generate navigation JavaScript"""
        return f"""
        <script>
        // Enhanced Navigation JavaScript
        
        class EnhancedNavigation {{
            constructor() {{
                this.transitionDuration = {self.config.transition_duration * 1000};
                this.currentTransition = null;
                this.init();
            }}
            
            init() {{
                this.setupKeyboardNavigation();
                this.setupTouchGestures();
                this.setupAnimations();
            }}
            
            setupKeyboardNavigation() {{
                document.addEventListener('keydown', (e) => {{
                    // Tab navigation with arrow keys
                    if (e.target.classList.contains('nav-tab-item')) {{
                        const tabs = Array.from(document.querySelectorAll('.nav-tab-item'));
                        const currentIndex = tabs.indexOf(e.target);
                        let targetIndex = currentIndex;
                        
                        switch(e.key) {{
                            case 'ArrowLeft':
                                targetIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                                break;
                            case 'ArrowRight':
                                targetIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                                break;
                            case 'Home':
                                targetIndex = 0;
                                break;
                            case 'End':
                                targetIndex = tabs.length - 1;
                                break;
                        }}
                        
                        if (targetIndex !== currentIndex) {{
                            e.preventDefault();
                            tabs[targetIndex].focus();
                            tabs[targetIndex].click();
                        }}
                    }}
                }});
            }}
            
            setupTouchGestures() {{
                let startX = 0;
                let startY = 0;
                
                document.addEventListener('touchstart', (e) => {{
                    startX = e.touches[0].clientX;
                    startY = e.touches[0].clientY;
                }});
                
                document.addEventListener('touchend', (e) => {{
                    const endX = e.changedTouches[0].clientX;
                    const endY = e.changedTouches[0].clientY;
                    const deltaX = endX - startX;
                    const deltaY = endY - startY;
                    
                    // Swipe gestures for navigation
                    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {{
                        if (deltaX > 0) {{
                            // Swipe right - previous tab
                            this.navigateTabs(-1);
                        }} else {{
                            // Swipe left - next tab
                            this.navigateTabs(1);
                        }}
                    }}
                }});
            }}
            
            setupAnimations() {{
                // Intersection Observer for scroll animations
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            entry.target.classList.add('animate-in');
                        }}
                    }});
                }});
                
                document.querySelectorAll('.nav-tab-item, .sidebar-nav-item').forEach(el => {{
                    observer.observe(el);
                }});
            }}
            
            navigateTabs(direction) {{
                const tabs = Array.from(document.querySelectorAll('.nav-tab-item'));
                const activeTab = document.querySelector('.nav-tab-item.active');
                
                if (activeTab && tabs.length > 1) {{
                    const currentIndex = tabs.indexOf(activeTab);
                    let targetIndex = currentIndex + direction;
                    
                    if (targetIndex < 0) targetIndex = tabs.length - 1;
                    if (targetIndex >= tabs.length) targetIndex = 0;
                    
                    tabs[targetIndex].click();
                }}
            }}
            
            animateTransition(fromElement, toElement, type = '{self.config.transition_type.value}') {{
                if (this.currentTransition) {{
                    clearTimeout(this.currentTransition);
                }}
                
                const container = document.querySelector('.nav-content');
                if (!container) return;
                
                container.classList.add(`${{type}}-enter`);
                
                this.currentTransition = setTimeout(() => {{
                    container.classList.add(`${{type}}-enter-active`);
                    container.classList.remove(`${{type}}-enter`);
                    
                    setTimeout(() => {{
                        container.classList.remove(`${{type}}-enter-active`);
                        this.currentTransition = null;
                    }}, this.transitionDuration);
                }}, 10);
            }}
            
            toggleSidebar() {{
                const sidebar = document.querySelector('.enhanced-nav-sidebar');
                if (sidebar) {{
                    sidebar.classList.toggle('collapsed');
                }}
            }}
            
            openDrawer() {{
                const drawer = document.querySelector('.enhanced-nav-drawer');
                if (drawer) {{
                    drawer.classList.add('open');
                    document.body.style.overflow = 'hidden';
                }}
            }}
            
            closeDrawer() {{
                const drawer = document.querySelector('.enhanced-nav-drawer');
                if (drawer) {{
                    drawer.classList.remove('open');
                    document.body.style.overflow = '';
                }}
            }}
        }}
        
        // Initialize navigation when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {{
            window.enhancedNav = new EnhancedNavigation();
        }});
        </script>
        """
    
    def add_navigation_item(self, item: NavigationItem, parent_key: Optional[str] = None):
        """Add a navigation item"""
        if parent_key:
            parent = self.navigation_items.get(parent_key)
            if parent:
                if not parent.children:
                    parent.children = []
                parent.children.append(item)
        else:
            self.navigation_items[item.key] = item
    
    def remove_navigation_item(self, key: str):
        """Remove a navigation item"""
        if key in self.navigation_items:
            del self.navigation_items[key]
    
    def set_current_item(self, key: str):
        """Set the current navigation item"""
        st.session_state.nav_current_item = key
        
        # Update navigation history
        if key not in st.session_state.nav_history:
            st.session_state.nav_history.append(key)
        
        # Update breadcrumb
        self._update_breadcrumb(key)
    
    def _update_breadcrumb(self, key: str):
        """Update breadcrumb navigation"""
        breadcrumb = []
        
        # Find the path to the current item
        def find_path(items: Dict[str, NavigationItem], target_key: str, path: List[str] = []) -> Optional[List[str]]:
            for item_key, item in items.items():
                current_path = path + [item_key]
                
                if item_key == target_key:
                    return current_path
                
                if item.children:
                    child_items = {child.key: child for child in item.children}
                    result = find_path(child_items, target_key, current_path)
                    if result:
                        return result
            
            return None
        
        path = find_path(self.navigation_items, key)
        if path:
            st.session_state.nav_breadcrumb = path
    
    def render_tabs(self, items: List[NavigationItem], 
                   selected_key: Optional[str] = None) -> Optional[str]:
        """Render tab navigation"""
        
        if not items:
            return None
        
        # Filter visible items
        visible_items = [item for item in items if not item.hidden]
        
        if not visible_items:
            return None
        
        # Create tab container
        st.markdown('<div class="enhanced-nav-container">', unsafe_allow_html=True)
        st.markdown('<div class="enhanced-nav-tabs">', unsafe_allow_html=True)
        
        selected_item = None
        
        for item in visible_items:
            # Build tab classes
            tab_classes = ["nav-tab-item"]
            if item.key == selected_key:
                tab_classes.append("active")
            if item.disabled:
                tab_classes.append("disabled")
            
            # Build tab content
            tab_content = ""
            if self.config.show_icons and item.icon:
                tab_content += f'<span class="nav-tab-icon">{item.icon}</span>'
            
            tab_content += f'<span>{item.label}</span>'
            
            if self.config.show_badges and item.badge:
                tab_content += f'<span class="nav-tab-badge">{item.badge}</span>'
            
            # Create button
            button_html = f'''
            <button class="{' '.join(tab_classes)}" 
                    onclick="window.streamlitSetComponentValue('{item.key}')"
                    {'disabled' if item.disabled else ''}
                    aria-selected="{'true' if item.key == selected_key else 'false'}"
                    role="tab">
                {tab_content}
            </button>
            '''
            
            st.markdown(button_html, unsafe_allow_html=True)
            
            if item.key == selected_key:
                selected_item = item
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show description for active tab
        if selected_item and self.config.show_descriptions and selected_item.description:
            st.markdown(f'<div class="nav-tab-description">{selected_item.description}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return selected_key
    
    def render_breadcrumb(self) -> None:
        """Render breadcrumb navigation"""
        
        breadcrumb_path = st.session_state.nav_breadcrumb
        
        if not breadcrumb_path:
            return
        
        st.markdown('<div class="enhanced-breadcrumb">', unsafe_allow_html=True)
        
        for i, item_key in enumerate(breadcrumb_path):
            item = self.navigation_items.get(item_key)
            if not item:
                continue
            
            is_current = i == len(breadcrumb_path) - 1
            
            # Add separator
            if i > 0:
                st.markdown(f'<span class="breadcrumb-separator">{self.config.breadcrumb_separator}</span>', unsafe_allow_html=True)
            
            # Add breadcrumb item
            item_classes = ["breadcrumb-item"]
            if is_current:
                item_classes.append("current")
            
            if is_current or item.disabled:
                st.markdown(f'<span class="{" ".join(item_classes)}">{item.label}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<a href="#" class="{" ".join(item_classes)}" onclick="window.streamlitSetComponentValue(\'{item_key}\')">{item.label}</a>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_sidebar(self, items: List[NavigationItem], 
                      selected_key: Optional[str] = None) -> Optional[str]:
        """Render sidebar navigation"""
        
        if not items:
            return None
        
        # Sidebar toggle button
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("☰", key="nav_sidebar_toggle", help="Toggle navigation"):
                st.session_state.nav_sidebar_collapsed = not st.session_state.nav_sidebar_collapsed
                st.rerun()
        
        if st.session_state.nav_sidebar_collapsed:
            return selected_key
        
        # Sidebar container
        sidebar_classes = ["enhanced-nav-sidebar"]
        if st.session_state.nav_sidebar_collapsed:
            sidebar_classes.append("collapsed")
        
        with st.sidebar:
            st.markdown(f'<div class="{" ".join(sidebar_classes)}">', unsafe_allow_html=True)
            
            selected_item = None
            
            for item in items:
                if item.hidden:
                    continue
                
                # Build item classes
                item_classes = ["sidebar-nav-item"]
                if item.key == selected_key:
                    item_classes.append("active")
                if item.disabled:
                    item_classes.append("disabled")
                
                # Build item content
                item_content = ""
                if self.config.show_icons and item.icon:
                    item_content += f'<span class="nav-tab-icon">{item.icon}</span>'
                
                item_content += f'<span>{item.label}</span>'
                
                if self.config.show_badges and item.badge:
                    item_content += f'<span class="nav-tab-badge">{item.badge}</span>'
                
                # Create sidebar item
                if st.button(
                    item.label,
                    key=f"sidebar_{item.key}",
                    disabled=item.disabled,
                    use_container_width=True
                ):
                    selected_item = item
                    self.set_current_item(item.key)
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        return selected_item.key if selected_item else selected_key
    
    def render_stepper(self, items: List[NavigationItem], 
                      current_step: int = 0,
                      completed_steps: List[int] = None) -> None:
        """Render stepper navigation"""
        
        if not items:
            return
        
        completed_steps = completed_steps or []
        
        st.markdown('<div class="enhanced-nav-stepper">', unsafe_allow_html=True)
        
        for i, item in enumerate(items):
            if item.hidden:
                continue
            
            # Build stepper classes
            stepper_classes = ["stepper-item"]
            if i == current_step:
                stepper_classes.append("active")
            if i in completed_steps:
                stepper_classes.append("completed")
            
            # Create stepper item
            st.markdown(f'<div class="{" ".join(stepper_classes)}">', unsafe_allow_html=True)
            
            # Circle with number or checkmark
            circle_content = "✓" if i in completed_steps else str(i + 1)
            st.markdown(f'<div class="stepper-circle">{circle_content}</div>', unsafe_allow_html=True)
            
            # Label
            st.markdown(f'<div class="stepper-label">{item.label}</div>', unsafe_allow_html=True)
            
            # Connection line
            if i < len(items) - 1:
                st.markdown('<div class="stepper-line"></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_drawer(self, items: List[NavigationItem], 
                     is_open: bool = False) -> Optional[str]:
        """Render drawer navigation"""
        
        if not items:
            return None
        
        # Drawer toggle button
        if st.button("☰ Menu", key="nav_drawer_toggle"):
            is_open = not is_open
        
        if not is_open:
            return None
        
        # Drawer overlay
        drawer_classes = ["enhanced-nav-drawer"]
        if is_open:
            drawer_classes.append("open")
        
        st.markdown(f'<div class="{" ".join(drawer_classes)}">', unsafe_allow_html=True)
        st.markdown('<div class="drawer-content">', unsafe_allow_html=True)
        
        # Close button
        if st.button("✕", key="nav_drawer_close"):
            is_open = False
        
        # Navigation items
        selected_item = None
        
        for item in items:
            if item.hidden:
                continue
            
            if st.button(
                f"{item.icon} {item.label}" if item.icon else item.label,
                key=f"drawer_{item.key}",
                disabled=item.disabled,
                use_container_width=True
            ):
                selected_item = item
                self.set_current_item(item.key)
                is_open = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        return selected_item.key if selected_item else None
    
    def get_navigation_history(self) -> List[str]:
        """Get navigation history"""
        return st.session_state.nav_history.copy()
    
    def clear_navigation_history(self):
        """Clear navigation history"""
        st.session_state.nav_history = []
    
    def go_back(self) -> Optional[str]:
        """Navigate back in history"""
        history = st.session_state.nav_history
        
        if len(history) > 1:
            # Remove current item and go to previous
            history.pop()
            previous_item = history[-1]
            self.set_current_item(previous_item)
            return previous_item
        
        return None
    
    def create_navigation_context(self) -> Dict[str, Any]:
        """Create navigation context for components"""
        return {
            "current_item": st.session_state.nav_current_item,
            "history": st.session_state.nav_history,
            "breadcrumb": st.session_state.nav_breadcrumb,
            "sidebar_collapsed": st.session_state.nav_sidebar_collapsed
        }


# Global navigation system instance
navigation_system = EnhancedNavigationSystem()


# Convenience functions
def create_navigation_item(key: str, label: str, icon: Optional[str] = None, **kwargs) -> NavigationItem:
    """Create a navigation item"""
    return NavigationItem(key=key, label=label, icon=icon, **kwargs)


def render_enhanced_tabs(items: List[NavigationItem], selected_key: Optional[str] = None) -> Optional[str]:
    """Render enhanced tab navigation"""
    return navigation_system.render_tabs(items, selected_key)


def render_enhanced_breadcrumb():
    """Render enhanced breadcrumb navigation"""
    navigation_system.render_breadcrumb()


def render_enhanced_sidebar(items: List[NavigationItem], selected_key: Optional[str] = None) -> Optional[str]:
    """Render enhanced sidebar navigation"""
    return navigation_system.render_sidebar(items, selected_key)


def render_enhanced_stepper(items: List[NavigationItem], current_step: int = 0, completed_steps: List[int] = None):
    """Render enhanced stepper navigation"""
    navigation_system.render_stepper(items, current_step, completed_steps)


def set_current_navigation_item(key: str):
    """Set current navigation item"""
    navigation_system.set_current_item(key)