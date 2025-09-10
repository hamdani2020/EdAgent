"""
Configuration Management System for EdAgent Streamlit Application

This module provides comprehensive configuration management with:
- Environment-specific settings
- Feature flags for different deployment environments
- API configuration with proper defaults
- UI/UX configuration options
- Security and performance settings
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class APIConfig:
    """API configuration settings"""
    base_url: str = field(default_factory=lambda: os.getenv("EDAGENT_API_URL", "http://localhost:8000/api/v1"))
    websocket_url: str = field(default_factory=lambda: os.getenv("EDAGENT_WS_URL", "ws://localhost:8000/api/v1/ws"))
    timeout: int = field(default_factory=lambda: int(os.getenv("API_TIMEOUT", "30")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("API_MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("API_RETRY_DELAY", "1.0")))
    rate_limit_requests: int = field(default_factory=lambda: int(os.getenv("API_RATE_LIMIT", "100")))
    rate_limit_window: int = field(default_factory=lambda: int(os.getenv("API_RATE_WINDOW", "60")))


@dataclass
class UIConfig:
    """UI/UX configuration settings"""
    app_title: str = "EdAgent - AI Career Coach"
    app_icon: str = "🎓"
    page_layout: str = "wide"
    sidebar_state: str = "expanded"
    
    # Theme settings
    primary_color: str = "#1f77b4"
    background_color: str = "#ffffff"
    secondary_background_color: str = "#f8f9fa"
    text_color: str = "#262730"
    
    # Component settings
    chat_message_limit: int = 100
    pagination_size: int = 10
    max_file_size_mb: int = 10
    
    # Animation settings
    enable_animations: bool = True
    animation_duration: str = "0.3s"
    
    # Accessibility settings
    high_contrast_mode: bool = False
    reduced_motion: bool = False
    screen_reader_support: bool = True


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    session_timeout_minutes: int = field(default_factory=lambda: int(os.getenv("SESSION_TIMEOUT", "480")))  # 8 hours
    token_refresh_threshold_minutes: int = field(default_factory=lambda: int(os.getenv("TOKEN_REFRESH_THRESHOLD", "5")))
    max_login_attempts: int = field(default_factory=lambda: int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")))
    lockout_duration_minutes: int = field(default_factory=lambda: int(os.getenv("LOCKOUT_DURATION", "15")))
    
    # Password requirements
    password_min_length: int = 8
    password_max_length: int = 128
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    password_special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Data protection
    encrypt_session_data: bool = field(default_factory=lambda: os.getenv("ENCRYPT_SESSION_DATA", "false").lower() == "true")
    secure_cookies: bool = field(default_factory=lambda: os.getenv("SECURE_COOKIES", "false").lower() == "true")


@dataclass
class FeatureFlags:
    """Feature flags for different environments and A/B testing"""
    # Core features
    websocket_chat: bool = field(default_factory=lambda: os.getenv("FEATURE_WEBSOCKET_CHAT", "true").lower() == "true")
    real_time_updates: bool = field(default_factory=lambda: os.getenv("FEATURE_REAL_TIME_UPDATES", "true").lower() == "true")
    
    # File handling
    file_upload: bool = field(default_factory=lambda: os.getenv("FEATURE_FILE_UPLOAD", "true").lower() == "true")
    data_export: bool = field(default_factory=lambda: os.getenv("FEATURE_DATA_EXPORT", "true").lower() == "true")
    
    # Analytics and tracking
    analytics_dashboard: bool = field(default_factory=lambda: os.getenv("FEATURE_ANALYTICS", "true").lower() == "true")
    user_tracking: bool = field(default_factory=lambda: os.getenv("FEATURE_USER_TRACKING", "false").lower() == "true")
    
    # Advanced features
    interview_prep: bool = field(default_factory=lambda: os.getenv("FEATURE_INTERVIEW_PREP", "true").lower() == "true")
    resume_analysis: bool = field(default_factory=lambda: os.getenv("FEATURE_RESUME_ANALYSIS", "true").lower() == "true")
    ai_recommendations: bool = field(default_factory=lambda: os.getenv("FEATURE_AI_RECOMMENDATIONS", "true").lower() == "true")
    
    # Experimental features
    voice_chat: bool = field(default_factory=lambda: os.getenv("FEATURE_VOICE_CHAT", "false").lower() == "true")
    video_calls: bool = field(default_factory=lambda: os.getenv("FEATURE_VIDEO_CALLS", "false").lower() == "true")
    collaborative_learning: bool = field(default_factory=lambda: os.getenv("FEATURE_COLLABORATIVE_LEARNING", "false").lower() == "true")
    
    # Development and debugging
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    mock_data: bool = field(default_factory=lambda: os.getenv("USE_MOCK_DATA", "false").lower() == "true")
    performance_monitoring: bool = field(default_factory=lambda: os.getenv("PERFORMANCE_MONITORING", "false").lower() == "true")


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: LogLevel = field(default_factory=lambda: LogLevel(os.getenv("LOG_LEVEL", "INFO")))
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # File logging
    log_to_file: bool = field(default_factory=lambda: os.getenv("LOG_TO_FILE", "false").lower() == "true")
    log_file_path: str = field(default_factory=lambda: os.getenv("LOG_FILE_PATH", "logs/edagent_streamlit.log"))
    max_file_size_mb: int = field(default_factory=lambda: int(os.getenv("LOG_MAX_FILE_SIZE", "10")))
    backup_count: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5")))
    
    # Console logging
    log_to_console: bool = True
    console_format: str = "%(levelname)s: %(message)s"
    
    # Structured logging
    structured_logging: bool = field(default_factory=lambda: os.getenv("STRUCTURED_LOGGING", "false").lower() == "true")
    log_json_format: bool = field(default_factory=lambda: os.getenv("LOG_JSON_FORMAT", "false").lower() == "true")


class StreamlitConfig:
    """
    Main configuration class for EdAgent Streamlit application
    
    This class provides centralized configuration management with environment-specific
    settings, feature flags, and proper defaults for all application components.
    """
    
    def __init__(self, environment: Optional[Environment] = None):
        # Determine environment
        self.environment = environment or Environment(os.getenv("ENVIRONMENT", "development"))
        
        # Initialize configuration sections
        self.api = APIConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self.features = FeatureFlags()
        self.logging = LoggingConfig()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
        
        # Validate configuration
        self._validate_config()
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides"""
        if self.environment == Environment.PRODUCTION:
            # Production overrides
            self.security.encrypt_session_data = True
            self.security.secure_cookies = True
            self.features.debug_mode = False
            self.features.mock_data = False
            self.logging.level = LogLevel.WARNING
            self.logging.log_to_file = True
            
        elif self.environment == Environment.STAGING:
            # Staging overrides
            self.features.debug_mode = False
            self.features.mock_data = False
            self.logging.level = LogLevel.INFO
            self.logging.log_to_file = True
            
        elif self.environment == Environment.DEVELOPMENT:
            # Development overrides
            self.features.debug_mode = True
            self.features.performance_monitoring = True
            self.logging.level = LogLevel.DEBUG
            self.logging.log_to_console = True
            
        elif self.environment == Environment.TESTING:
            # Testing overrides
            self.features.mock_data = True
            self.api.timeout = 5  # Shorter timeout for tests
            self.logging.level = LogLevel.ERROR
    
    def _validate_config(self) -> None:
        """Validate configuration settings"""
        # Validate API configuration
        if not self.api.base_url:
            raise ValueError("API base URL is required")
        
        if self.api.timeout <= 0:
            raise ValueError("API timeout must be positive")
        
        if self.api.max_retries < 0:
            raise ValueError("API max retries cannot be negative")
        
        # Validate security configuration
        if self.security.session_timeout_minutes <= 0:
            raise ValueError("Session timeout must be positive")
        
        if self.security.password_min_length < 4:
            raise ValueError("Password minimum length must be at least 4")
        
        if self.security.password_max_length < self.security.password_min_length:
            raise ValueError("Password maximum length must be greater than minimum length")
        
        # Validate UI configuration
        if self.ui.chat_message_limit <= 0:
            raise ValueError("Chat message limit must be positive")
        
        if self.ui.pagination_size <= 0:
            raise ValueError("Pagination size must be positive")
    
    def get_api_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        """Get standardized API headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"EdAgent-Streamlit/1.0 ({self.environment.value})",
            "Accept": "application/json"
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        return headers
    
    def get_websocket_headers(self, auth_token: str, user_id: str) -> Dict[str, str]:
        """Get WebSocket connection headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "User-ID": user_id,
            "Client-Type": "streamlit-web"
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.features, feature_name, False)
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """Get Streamlit-specific configuration"""
        return {
            "page_title": self.ui.app_title,
            "page_icon": self.ui.app_icon,
            "layout": self.ui.page_layout,
            "initial_sidebar_state": self.ui.sidebar_state
        }
    
    def get_theme_config(self) -> Dict[str, str]:
        """Get theme configuration for Streamlit"""
        return {
            "primaryColor": self.ui.primary_color,
            "backgroundColor": self.ui.background_color,
            "secondaryBackgroundColor": self.ui.secondary_background_color,
            "textColor": self.ui.text_color
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "environment": self.environment.value,
            "api": self.api.__dict__,
            "ui": self.ui.__dict__,
            "security": {k: v for k, v in self.security.__dict__.items() if not k.startswith('password')},  # Exclude sensitive data
            "features": self.features.__dict__,
            "logging": self.logging.__dict__
        }
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"StreamlitConfig(environment={self.environment.value}, api_url={self.api.base_url})"


@dataclass
class DeploymentConfig:
    """
    Deployment-specific configuration for different environments
    
    This class handles environment-specific deployment settings including
    database connections, external service configurations, and infrastructure settings.
    """
    
    # Database configuration
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    
    # External services
    sentry_dsn: str = field(default_factory=lambda: os.getenv("SENTRY_DSN", ""))
    analytics_key: str = field(default_factory=lambda: os.getenv("ANALYTICS_KEY", ""))
    
    # Infrastructure
    health_check_url: str = field(default_factory=lambda: os.getenv("HEALTH_CHECK_URL", "/health"))
    metrics_port: int = field(default_factory=lambda: int(os.getenv("METRICS_PORT", "8080")))
    
    # CDN and static assets
    static_assets_url: str = field(default_factory=lambda: os.getenv("STATIC_ASSETS_URL", ""))
    cdn_url: str = field(default_factory=lambda: os.getenv("CDN_URL", ""))
    
    # Monitoring and alerting
    enable_monitoring: bool = field(default_factory=lambda: os.getenv("ENABLE_MONITORING", "false").lower() == "true")
    alert_webhook_url: str = field(default_factory=lambda: os.getenv("ALERT_WEBHOOK_URL", ""))
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return {
            "url": self.database_url,
            "pool_size": os.getenv("DB_POOL_SIZE", "10"),
            "max_overflow": os.getenv("DB_MAX_OVERFLOW", "20"),
            "pool_timeout": os.getenv("DB_POOL_TIMEOUT", "30")
        }
    
    def get_cache_config(self) -> Dict[str, str]:
        """Get cache configuration"""
        return {
            "redis_url": self.redis_url,
            "default_ttl": os.getenv("CACHE_DEFAULT_TTL", "3600"),
            "max_connections": os.getenv("CACHE_MAX_CONNECTIONS", "10")
        }


# Global configuration instance
_config_instance: Optional[StreamlitConfig] = None


def get_config() -> StreamlitConfig:
    """Get global configuration instance (singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = StreamlitConfig()
    return _config_instance


def reload_config() -> StreamlitConfig:
    """Reload configuration (useful for testing or config changes)"""
    global _config_instance
    _config_instance = None
    return get_config()


# Utility functions for common configuration tasks

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled (convenience function)"""
    return get_config().is_feature_enabled(feature_name)


def get_api_base_url() -> str:
    """Get API base URL (convenience function)"""
    return get_config().api.base_url


def get_websocket_url() -> str:
    """Get WebSocket URL (convenience function)"""
    return get_config().api.websocket_url


def is_development() -> bool:
    """Check if running in development environment"""
    return get_config().environment == Environment.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production environment"""
    return get_config().environment == Environment.PRODUCTION


def get_log_level() -> str:
    """Get current log level"""
    return get_config().logging.level.value