"""
Application settings and configuration management
"""

import os
from typing import Optional, Literal
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    youtube_api_key: str = Field(..., env="YOUTUBE_API_KEY")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./edagent.db", 
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # AI Service Configuration
    gemini_model_chat: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL_CHAT")
    gemini_model_reasoning: str = Field(default="gemini-1.5-pro", env="GEMINI_MODEL_REASONING")
    gemini_temperature_chat: float = Field(default=0.7, env="GEMINI_TEMPERATURE_CHAT")
    gemini_temperature_reasoning: float = Field(default=0.3, env="GEMINI_TEMPERATURE_REASONING")
    gemini_max_tokens_response: int = Field(default=1000, env="GEMINI_MAX_TOKENS_RESPONSE")
    gemini_max_tokens_learning_path: int = Field(default=2000, env="GEMINI_MAX_TOKENS_LEARNING_PATH")
    
    # Rate Limiting Configuration
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_RPM")
    rate_limit_burst_size: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # API Server Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=False, env="API_DEBUG")
    
    # Security Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    session_expire_minutes: int = Field(default=1440, env="SESSION_EXPIRE_MINUTES")  # 24 hours
    
    # Content Recommendation Configuration
    youtube_max_results: int = Field(default=10, env="YOUTUBE_MAX_RESULTS")
    content_cache_ttl_seconds: int = Field(default=3600, env="CONTENT_CACHE_TTL")  # 1 hour
    
    # Environment Configuration
    environment: Literal["development", "staging", "production"] = Field(
        default="development", env="ENVIRONMENT"
    )
    
    # Redis Configuration
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_ttl_seconds: int = Field(default=3600, env="REDIS_TTL")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Health Check Configuration
    health_check_timeout: int = Field(default=30, env="HEALTH_CHECK_TIMEOUT")
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level setting"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings
    
    Returns:
        Application settings instance
    """
    return Settings()