"""
Logging configuration for EdAgent application
"""

import logging
import logging.config
import os
from typing import Dict, Any
from pathlib import Path

from .settings import get_settings


def setup_logging() -> None:
    """
    Set up logging configuration based on environment settings
    """
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define logging configuration
    logging_config = get_logging_config(settings)
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Set up root logger
    logger = logging.getLogger("edagent")
    logger.info(f"Logging initialized for {settings.environment} environment")


def get_logging_config(settings) -> Dict[str, Any]:
    """
    Get logging configuration dictionary
    
    Args:
        settings: Application settings
        
    Returns:
        Logging configuration dictionary
    """
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "edagent": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"]
        }
    }
    
    # Add file handler if log file is specified
    if settings.log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "detailed" if settings.is_development else "json",
            "filename": settings.log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
        config["root"]["handlers"].append("file")
    
    # Production-specific configuration
    if settings.is_production:
        # Use JSON formatter for structured logging
        config["handlers"]["console"]["formatter"] = "json"
        
        # Add error file handler for production
        if settings.log_file:
            error_log_file = settings.log_file.replace(".log", "-error.log")
            config["handlers"]["error_file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": error_log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8"
            }
            
            # Add error handler to root logger
            config["root"]["handlers"].append("error_file")
    
    return config


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"edagent.{name}")


# Context manager for request logging
class RequestLoggingContext:
    """Context manager for request-specific logging"""
    
    def __init__(self, request_id: str, user_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.logger = get_logger("request")
    
    def __enter__(self):
        self.logger.info(
            "Request started",
            extra={
                "request_id": self.request_id,
                "user_id": self.user_id
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                f"Request failed: {exc_val}",
                extra={
                    "request_id": self.request_id,
                    "user_id": self.user_id,
                    "error_type": exc_type.__name__
                }
            )
        else:
            self.logger.info(
                "Request completed",
                extra={
                    "request_id": self.request_id,
                    "user_id": self.user_id
                }
            )