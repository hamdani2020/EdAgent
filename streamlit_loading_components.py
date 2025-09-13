"""
Enhanced Loading Components for EdAgent Streamlit App
Provides comprehensive loading states, progress indicators, and user feedback.
"""

import streamlit as st
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
import threading
import json

from streamlit_error_handler import error_handler, ErrorHandlingContext


class LoadingStyle(Enum):
    """Different loading indicator styles"""
    SPINNER = "spinner"
    PROGRESS_BAR = "progress_bar"
    DOTS = "dots"
    PULSE = "pulse"
    SKELETON = "skeleton"


class LoadingPriority(Enum):
    """Loading operation priorities"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LoadingOperation:
    """Represents a loading operation"""
    id: str
    name: str
    message: str
    style: LoadingStyle = LoadingStyle.SPINNER
    priority: LoadingPriority = LoadingPriority.NORMAL
    progress: Optional[float] = None
    start_time: datetime = None
    estimated_duration: Optional[int] = None
    cancellable: bool = False
    steps: List[str] = None
    current_step: int = 0
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.steps is None:
            self.steps = []


class EnhancedLoadingManager:
    """Enhanced loading manager with multiple loading styles and progress tracking"""
    
    def __init__(self):
        self.active_operations: Dict[str, LoadingOperation] = {}
        self.operation_counter = 0
        self.global_loading_state = False
        
    def create_operation(self, name: str, message: str, 
                        style: LoadingStyle = LoadingStyle.SPINNER,
                        priority: LoadingPriority = LoadingPriority.NORMAL,
                        estimated_duration: Optional[int] = None,
                        cancellable: bool = False,
                        steps: Optional[List[str]] = None) -> str:
        """Create a new loading operation"""
        
        self.operation_counter += 1
        operation_id = f"op_{self.operation_counter}_{int(time.time())}"
        
        operation = LoadingOperation(
            id=operation_id,
            name=name,
            message=message,
            style=style,
            priority=priority,
            estimated_duration=estimated_duration,
            cancellable=cancellable,
            steps=steps or []
        )
        
        self.active_operations[operation_id] = operation
        self.global_loading_state = True
        
        return operation_id
    
    def update_operation(self, operation_id: str, 
                        progress: Optional[float] = None,
                        message: Optional[str] = None,
                        current_step: Optional[int] = None) -> None:
        """Update an existing loading operation"""
        
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        
        if progress is not None:
            operation.progress = max(0.0, min(1.0, progress))
        
        if message is not None:
            operation.message = message
        
        if current_step is not None and operation.steps:
            operation.current_step = max(0, min(len(operation.steps) - 1, current_step))
    
    def finish_operation(self, operation_id: str) -> None:
        """Finish a loading operation"""
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]
        
        # Update global loading state
        self.global_loading_state = len(self.active_operations) > 0
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a loading operation if cancellable"""
        if operation_id not in self.active_operations:
            return False
        
        operation = self.active_operations[operation_id]
        if not operation.cancellable:
            return False
        
        self.finish_operation(operation_id)
        return True
    
    def get_operation(self, operation_id: str) -> Optional[LoadingOperation]:
        """Get loading operation by ID"""
        return self.active_operations.get(operation_id)
    
    def get_active_operations(self) -> List[LoadingOperation]:
        """Get all active operations sorted by priority"""
        operations = list(self.active_operations.values())
        priority_order = {
            LoadingPriority.CRITICAL: 0,
            LoadingPriority.HIGH: 1,
            LoadingPriority.NORMAL: 2,
            LoadingPriority.LOW: 3
        }
        return sorted(operations, key=lambda op: priority_order[op.priority])


class LoadingIndicators:
    """Collection of loading indicator components"""
    
    @staticmethod
    def spinner_with_message(message: str, progress: Optional[float] = None) -> None:
        """Show spinner with message and optional progress"""
        with st.spinner(message):
            if progress is not None:
                st.progress(progress)
    
    @staticmethod
    def progress_bar_with_steps(message: str, progress: float, 
                               steps: List[str], current_step: int) -> None:
        """Show progress bar with step indicators"""
        st.write(f"**{message}**")
        
        # Progress bar
        st.progress(progress)
        
        # Step indicators
        if steps and current_step < len(steps):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write(f"Step {current_step + 1}/{len(steps)}")
            
            with col2:
                st.write(f"*{steps[current_step]}*")
            
            # Show all steps with status
            with st.expander("📋 All Steps"):
                for i, step in enumerate(steps):
                    if i < current_step:
                        st.write(f"✅ {step}")
                    elif i == current_step:
                        st.write(f"🔄 {step}")
                    else:
                        st.write(f"⏳ {step}")
    
    @staticmethod
    def skeleton_loader(num_lines: int = 3, line_height: int = 20) -> None:
        """Show skeleton loader for content"""
        st.markdown("""
        <style>
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 4px;
            margin: 8px 0;
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        for i in range(num_lines):
            width = 100 if i < num_lines - 1 else 60  # Last line shorter
            st.markdown(
                f'<div class="skeleton" style="height: {line_height}px; width: {width}%;"></div>',
                unsafe_allow_html=True
            )
    
    @staticmethod
    def pulse_indicator(message: str, color: str = "#1f77b4") -> None:
        """Show pulsing indicator"""
        st.markdown(f"""
        <style>
        .pulse {{
            display: inline-block;
            width: 12px;
            height: 12px;
            background-color: {color};
            border-radius: 50%;
            animation: pulse 1.5s ease-in-out infinite;
            margin-right: 8px;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.5; transform: scale(1.1); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}
        </style>
        
        <div style="display: flex; align-items: center; margin: 10px 0;">
            <div class="pulse"></div>
            <span>{message}</span>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def dots_loader(message: str) -> None:
        """Show animated dots loader"""
        st.markdown(f"""
        <style>
        .dots-loader {{
            display: inline-block;
            margin-left: 8px;
        }}
        
        .dots-loader::after {{
            content: '';
            animation: dots 1.5s steps(4, end) infinite;
        }}
        
        @keyframes dots {{
            0%, 20% {{ content: ''; }}
            40% {{ content: '.'; }}
            60% {{ content: '..'; }}
            80%, 100% {{ content: '...'; }}
        }}
        </style>
        
        <div style="margin: 10px 0;">
            {message}<span class="dots-loader"></span>
        </div>
        """, unsafe_allow_html=True)


class LoadingContextManager:
    """Context manager for loading operations"""
    
    def __init__(self, loading_manager: EnhancedLoadingManager,
                 name: str, message: str,
                 style: LoadingStyle = LoadingStyle.SPINNER,
                 priority: LoadingPriority = LoadingPriority.NORMAL,
                 estimated_duration: Optional[int] = None,
                 cancellable: bool = False,
                 steps: Optional[List[str]] = None):
        
        self.loading_manager = loading_manager
        self.name = name
        self.message = message
        self.style = style
        self.priority = priority
        self.estimated_duration = estimated_duration
        self.cancellable = cancellable
        self.steps = steps
        self.operation_id = None
        self.placeholder = None
    
    def __enter__(self):
        self.operation_id = self.loading_manager.create_operation(
            name=self.name,
            message=self.message,
            style=self.style,
            priority=self.priority,
            estimated_duration=self.estimated_duration,
            cancellable=self.cancellable,
            steps=self.steps
        )
        
        # Create placeholder for loading indicator
        self.placeholder = st.empty()
        self._update_display()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.operation_id:
            self.loading_manager.finish_operation(self.operation_id)
        
        if self.placeholder:
            self.placeholder.empty()
        
        return False
    
    def update_progress(self, progress: float, message: Optional[str] = None,
                       current_step: Optional[int] = None) -> None:
        """Update loading progress"""
        if self.operation_id:
            self.loading_manager.update_operation(
                self.operation_id, progress, message, current_step
            )
            self._update_display()
    
    def _update_display(self) -> None:
        """Update the loading display"""
        if not self.operation_id or not self.placeholder:
            return
        
        operation = self.loading_manager.get_operation(self.operation_id)
        if not operation:
            return
        
        with self.placeholder.container():
            # Show cancel button if cancellable
            if operation.cancellable:
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{self.operation_id}"):
                        self.loading_manager.cancel_operation(self.operation_id)
                        st.stop()
            
            # Show appropriate loading indicator based on style
            if operation.style == LoadingStyle.SPINNER:
                LoadingIndicators.spinner_with_message(operation.message, operation.progress)
            
            elif operation.style == LoadingStyle.PROGRESS_BAR:
                if operation.steps:
                    LoadingIndicators.progress_bar_with_steps(
                        operation.message, 
                        operation.progress or 0.0,
                        operation.steps,
                        operation.current_step
                    )
                else:
                    st.write(f"**{operation.message}**")
                    st.progress(operation.progress or 0.0)
            
            elif operation.style == LoadingStyle.SKELETON:
                LoadingIndicators.skeleton_loader()
            
            elif operation.style == LoadingStyle.PULSE:
                LoadingIndicators.pulse_indicator(operation.message)
            
            elif operation.style == LoadingStyle.DOTS:
                LoadingIndicators.dots_loader(operation.message)
            
            # Show estimated time remaining
            if operation.estimated_duration:
                elapsed = (datetime.now() - operation.start_time).total_seconds()
                remaining = max(0, operation.estimated_duration - elapsed)
                if remaining > 0:
                    st.caption(f"⏱️ Estimated time remaining: {int(remaining)}s")


class GlobalLoadingIndicator:
    """Global loading indicator for the entire app"""
    
    def __init__(self, loading_manager: EnhancedLoadingManager):
        self.loading_manager = loading_manager
        self.container = None
    
    def show(self) -> None:
        """Show global loading indicator"""
        if not self.loading_manager.global_loading_state:
            return
        
        operations = self.loading_manager.get_active_operations()
        if not operations:
            return
        
        # Show in sidebar or top of main area
        with st.sidebar:
            st.markdown("---")
            st.subheader("🔄 Active Operations")
            
            for operation in operations[:3]:  # Show top 3 operations
                with st.container():
                    # Priority indicator
                    priority_icons = {
                        LoadingPriority.CRITICAL: "🔴",
                        LoadingPriority.HIGH: "🟡",
                        LoadingPriority.NORMAL: "🔵",
                        LoadingPriority.LOW: "⚪"
                    }
                    
                    st.write(f"{priority_icons[operation.priority]} {operation.name}")
                    
                    if operation.progress is not None:
                        st.progress(operation.progress)
                    else:
                        LoadingIndicators.pulse_indicator("Processing...", "#666")
                    
                    # Show elapsed time
                    elapsed = (datetime.now() - operation.start_time).total_seconds()
                    st.caption(f"⏱️ {int(elapsed)}s elapsed")
            
            if len(operations) > 3:
                st.caption(f"... and {len(operations) - 3} more operations")


# Global loading manager instance
loading_manager = EnhancedLoadingManager()
global_indicator = GlobalLoadingIndicator(loading_manager)


# Convenience functions
def show_loading(name: str, message: str, 
                style: LoadingStyle = LoadingStyle.SPINNER,
                priority: LoadingPriority = LoadingPriority.NORMAL,
                estimated_duration: Optional[int] = None,
                cancellable: bool = False,
                steps: Optional[List[str]] = None) -> LoadingContextManager:
    """Create a loading context manager"""
    return LoadingContextManager(
        loading_manager, name, message, style, priority,
        estimated_duration, cancellable, steps
    )


def show_progress_loading(name: str, message: str, steps: List[str],
                         estimated_duration: Optional[int] = None) -> LoadingContextManager:
    """Create a progress bar loading context with steps"""
    return LoadingContextManager(
        loading_manager, name, message, 
        LoadingStyle.PROGRESS_BAR, LoadingPriority.NORMAL,
        estimated_duration, False, steps
    )


def show_skeleton_loading(num_lines: int = 3) -> None:
    """Show skeleton loading for content"""
    LoadingIndicators.skeleton_loader(num_lines)


def show_pulse_loading(message: str, color: str = "#1f77b4") -> None:
    """Show pulse loading indicator"""
    LoadingIndicators.pulse_indicator(message, color)


# Decorators for automatic loading states
def with_loading(name: str, message: str, 
                style: LoadingStyle = LoadingStyle.SPINNER,
                show_progress: bool = False):
    """Decorator to automatically show loading state for functions"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            steps = None
            if show_progress and hasattr(func, '_loading_steps'):
                steps = func._loading_steps
            
            with show_loading(name, message, style, steps=steps) as loading:
                if show_progress and steps:
                    # Update progress through steps
                    for i, step in enumerate(steps):
                        loading.update_progress(i / len(steps), f"{message} - {step}", i)
                        result = await func(*args, **kwargs)
                        if i < len(steps) - 1:
                            await asyncio.sleep(0.1)  # Small delay between steps
                    
                    loading.update_progress(1.0, f"{message} - Complete", len(steps) - 1)
                    return result
                else:
                    return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with show_loading(name, message, style) as loading:
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def loading_steps(*steps):
    """Decorator to define loading steps for a function"""
    def decorator(func):
        func._loading_steps = list(steps)
        return func
    return decorator


# Enhanced loading components for specific operations
class APILoadingComponents:
    """Loading components specifically for API operations"""
    
    @staticmethod
    def api_call_loading(operation_name: str, endpoint: str = None) -> LoadingContextManager:
        """Loading for API calls"""
        message = f"Calling {operation_name}"
        if endpoint:
            message += f" ({endpoint})"
        
        return show_loading(
            name=f"API: {operation_name}",
            message=message,
            style=LoadingStyle.SPINNER,
            priority=LoadingPriority.NORMAL,
            estimated_duration=10,
            cancellable=True
        )
    
    @staticmethod
    def data_loading(data_type: str, count: Optional[int] = None) -> LoadingContextManager:
        """Loading for data operations"""
        message = f"Loading {data_type}"
        if count:
            message += f" ({count} items)"
        
        return show_loading(
            name=f"Data: {data_type}",
            message=message,
            style=LoadingStyle.PROGRESS_BAR,
            priority=LoadingPriority.NORMAL
        )
    
    @staticmethod
    def file_upload_loading(filename: str, file_size: Optional[int] = None) -> LoadingContextManager:
        """Loading for file uploads"""
        message = f"Uploading {filename}"
        if file_size:
            message += f" ({file_size // 1024}KB)"
        
        return show_loading(
            name="File Upload",
            message=message,
            style=LoadingStyle.PROGRESS_BAR,
            priority=LoadingPriority.HIGH,
            cancellable=True
        )


# Integration with error handling
class LoadingWithErrorHandling:
    """Combine loading states with error handling"""
    
    def __init__(self, operation_name: str, loading_message: str,
                 error_context: Optional[str] = None):
        self.operation_name = operation_name
        self.loading_message = loading_message
        self.error_context = error_context or operation_name
        self.loading_context = None
        self.error_context_manager = None
    
    def __enter__(self):
        # Start loading
        self.loading_context = show_loading(
            self.operation_name, 
            self.loading_message,
            style=LoadingStyle.SPINNER,
            priority=LoadingPriority.NORMAL
        ).__enter__()
        
        # Start error handling
        self.error_context_manager = ErrorHandlingContext(
            self.error_context, 
            show_loading=False  # We're handling loading separately
        ).__enter__()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Finish loading
        if self.loading_context:
            self.loading_context.__exit__(exc_type, exc_val, exc_tb)
        
        # Handle errors
        if self.error_context_manager:
            return self.error_context_manager.__exit__(exc_type, exc_val, exc_tb)
        
        return False
    
    def update_progress(self, progress: float, message: Optional[str] = None):
        """Update loading progress"""
        if self.loading_context:
            self.loading_context.update_progress(progress, message)


def with_loading_and_error_handling(operation_name: str, loading_message: str):
    """Context manager that combines loading and error handling"""
    return LoadingWithErrorHandling(operation_name, loading_message)