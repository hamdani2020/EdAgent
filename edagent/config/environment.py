"""
Environment detection and configuration
"""

import os
from enum import Enum
from typing import Dict, Any


class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


def get_environment() -> Environment:
    """
    Detect current environment from environment variables
    
    Returns:
        Current environment type
    """
    env_name = os.getenv("ENVIRONMENT", "development").lower()
    
    try:
        return Environment(env_name)
    except ValueError:
        return Environment.DEVELOPMENT


def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration
    
    Returns:
        Dictionary of environment-specific settings
    """
    env = get_environment()
    
    base_config = {
        "debug": False,
        "testing": False,
        "log_level": "INFO",
    }
    
    environment_configs = {
        Environment.DEVELOPMENT: {
            "debug": True,
            "log_level": "DEBUG",
            "database_url": "sqlite:///./edagent_dev.db",
        },
        Environment.TESTING: {
            "testing": True,
            "log_level": "WARNING",
            "database_url": "sqlite:///:memory:",
        },
        Environment.STAGING: {
            "log_level": "INFO",
        },
        Environment.PRODUCTION: {
            "log_level": "WARNING",
        }
    }
    
    config = base_config.copy()
    config.update(environment_configs.get(env, {}))
    
    return config


def is_development() -> bool:
    """Check if running in development environment"""
    return get_environment() == Environment.DEVELOPMENT


def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_environment() == Environment.TESTING


def is_production() -> bool:
    """Check if running in production environment"""
    return get_environment() == Environment.PRODUCTION