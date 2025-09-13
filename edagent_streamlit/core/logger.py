"""
Comprehensive Logging System for EdAgent Streamlit Application

This module provides structured logging with:
- Multiple output formats (console, file, JSON)
- Environment-specific log levels
- Performance monitoring integration
- Error tracking and alerting
- Structured logging for better analysis
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
import traceback

from .config import get_config, LogLevel, Environment


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured data"""
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if enabled
        if self.include_extra:
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info'
                }
            }
            if extra_fields:
                log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class JSONFormatter(logging.Formatter):
    """JSON formatter for machine-readable logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_api_call(
        self, 
        endpoint: str, 
        method: str, 
        duration: float, 
        status_code: int,
        user_id: Optional[str] = None
    ) -> None:
        """Log API call performance"""
        self.logger.info(
            "API call completed",
            extra={
                "event_type": "api_call",
                "endpoint": endpoint,
                "method": method,
                "duration_ms": duration * 1000,
                "status_code": status_code,
                "user_id": user_id
            }
        )
    
    def log_page_load(
        self, 
        page: str, 
        duration: float, 
        user_id: Optional[str] = None
    ) -> None:
        """Log page load performance"""
        self.logger.info(
            "Page loaded",
            extra={
                "event_type": "page_load",
                "page": page,
                "duration_ms": duration * 1000,
                "user_id": user_id
            }
        )
    
    def log_user_action(
        self, 
        action: str, 
        component: str, 
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log user interaction"""
        extra_data = {
            "event_type": "user_action",
            "action": action,
            "component": component,
            "user_id": user_id
        }
        
        if metadata:
            extra_data["metadata"] = metadata
        
        self.logger.info(f"User action: {action}", extra=extra_data)


class ErrorTracker:
    """Error tracking and alerting system"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_counts = {}
    
    def track_error(
        self, 
        error: Exception, 
        context: str,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track and log errors with context"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Count errors for alerting
        error_key = f"{error_type}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log error with full context
        extra_data = {
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "user_id": user_id,
            "error_count": self.error_counts[error_key]
        }
        
        if additional_data:
            extra_data["additional_data"] = additional_data
        
        self.logger.error(
            f"Error in {context}: {error_message}",
            exc_info=True,
            extra=extra_data
        )
        
        # Check if we need to alert (e.g., if error count exceeds threshold)
        if self.error_counts[error_key] >= 5:  # Alert after 5 occurrences
            self._send_alert(error_type, context, self.error_counts[error_key])
    
    def _send_alert(self, error_type: str, context: str, count: int) -> None:
        """Send alert for repeated errors"""
        self.logger.critical(
            f"High error frequency detected: {error_type} in {context} ({count} occurrences)",
            extra={
                "event_type": "alert",
                "alert_type": "high_error_frequency",
                "error_type": error_type,
                "context": context,
                "count": count
            }
        )


class EdAgentLogger:
    """Main logger class for EdAgent Streamlit application"""
    
    def __init__(self, name: str = "edagent_streamlit"):
        self.name = name
        self.config = get_config()
        self.logger = logging.getLogger(name)
        self.performance = PerformanceLogger(self.logger)
        self.error_tracker = ErrorTracker(self.logger)
        
        # Configure logger
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger with appropriate handlers and formatters"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, self.config.logging.level.value)
        self.logger.setLevel(log_level)
        
        # Console handler
        if self.config.logging.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            if self.config.logging.structured_logging:
                console_formatter = StructuredFormatter()
            elif self.config.logging.log_json_format:
                console_formatter = JSONFormatter()
            else:
                console_formatter = logging.Formatter(
                    self.config.logging.console_format,
                    datefmt=self.config.logging.date_format
                )
            
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.config.logging.log_to_file:
            # Ensure log directory exists
            log_file_path = Path(self.config.logging.log_file_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file_path,
                maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            
            if self.config.logging.log_json_format:
                file_formatter = JSONFormatter()
            else:
                file_formatter = logging.Formatter(
                    self.config.logging.format,
                    datefmt=self.config.logging.date_format
                )
            
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Add environment info to first log
        self.logger.info(
            f"Logger initialized for {self.name}",
            extra={
                "event_type": "logger_init",
                "environment": self.config.environment.value,
                "log_level": self.config.logging.level.value,
                "handlers": [type(h).__name__ for h in self.logger.handlers]
            }
        )
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)
    
    def log_user_session(self, user_id: str, action: str, **kwargs) -> None:
        """Log user session activity"""
        self.info(
            f"User session: {action}",
            user_id=user_id,
            event_type="user_session",
            action=action,
            **kwargs
        )
    
    def log_api_interaction(
        self, 
        endpoint: str, 
        method: str, 
        status_code: int,
        duration: float,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log API interaction"""
        self.performance.log_api_call(endpoint, method, duration, status_code, user_id)
    
    def log_error_with_context(
        self, 
        error: Exception, 
        context: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log error with full context tracking"""
        self.error_tracker.track_error(error, context, user_id, kwargs)
    
    def log_performance_metric(
        self, 
        metric_name: str, 
        value: float, 
        unit: str = "ms",
        **kwargs
    ) -> None:
        """Log performance metric"""
        self.info(
            f"Performance metric: {metric_name}",
            event_type="performance_metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )


# Global logger instances
_loggers: Dict[str, EdAgentLogger] = {}


def setup_logging(name: str = "edagent_streamlit") -> EdAgentLogger:
    """Setup and configure logging for the application"""
    if name not in _loggers:
        _loggers[name] = EdAgentLogger(name)
    return _loggers[name]


def get_logger(name: str = "edagent_streamlit") -> EdAgentLogger:
    """Get logger instance (creates if doesn't exist)"""
    if name not in _loggers:
        _loggers[name] = EdAgentLogger(name)
    return _loggers[name]


def log_startup_info() -> None:
    """Log application startup information"""
    logger = get_logger()
    config = get_config()
    
    logger.info(
        "EdAgent Streamlit application starting",
        event_type="app_startup",
        environment=config.environment.value,
        api_url=config.api.base_url,
        features_enabled=[
            name for name, enabled in config.features.__dict__.items() 
            if enabled
        ]
    )


def log_shutdown_info() -> None:
    """Log application shutdown information"""
    logger = get_logger()
    logger.info(
        "EdAgent Streamlit application shutting down",
        event_type="app_shutdown"
    )


# Context managers for logging

class LogContext:
    """Context manager for adding context to logs"""
    
    def __init__(self, logger: EdAgentLogger, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        # Store old context and add new context
        for key, value in self.context.items():
            if hasattr(self.logger.logger, key):
                self.old_context[key] = getattr(self.logger.logger, key)
            setattr(self.logger.logger, key, value)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        for key in self.context:
            if key in self.old_context:
                setattr(self.logger.logger, key, self.old_context[key])
            else:
                delattr(self.logger.logger, key)


class PerformanceContext:
    """Context manager for performance logging"""
    
    def __init__(self, logger: EdAgentLogger, operation: str, **metadata):
        self.logger = logger
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}", **self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.log_performance_metric(
                f"{self.operation}_duration",
                duration * 1000,  # Convert to milliseconds
                "ms",
                **self.metadata
            )
            self.logger.debug(
                f"Completed operation: {self.operation} in {duration:.3f}s",
                **self.metadata
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation} after {duration:.3f}s",
                exc_info=True,
                **self.metadata
            )


# Utility functions

def with_logging_context(**context):
    """Decorator to add logging context to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            with LogContext(logger, **context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_performance_logging(operation_name: str = None):
    """Decorator to add performance logging to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with PerformanceContext(logger, op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator