"""
Prometheus metrics for EdAgent application
"""

import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_conversations_total = Gauge(
    'active_conversations_total',
    'Number of active conversations'
)

gemini_api_calls_total = Counter(
    'gemini_api_calls_total',
    'Total Gemini API calls',
    ['model', 'status']
)

gemini_api_errors_total = Counter(
    'gemini_api_errors_total',
    'Total Gemini API errors',
    ['error_type']
)

database_connection_errors_total = Counter(
    'database_connection_errors_total',
    'Total database connection errors'
)

youtube_api_calls_total = Counter(
    'youtube_api_calls_total',
    'Total YouTube API calls',
    ['status']
)

user_sessions_active = Gauge(
    'user_sessions_active',
    'Number of active user sessions'
)

learning_paths_generated_total = Counter(
    'learning_paths_generated_total',
    'Total learning paths generated'
)

skill_assessments_completed_total = Counter(
    'skill_assessments_completed_total',
    'Total skill assessments completed'
)


def track_request_metrics(func):
    """Decorator to track HTTP request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = await func(*args, **kwargs)
            status_code = getattr(response, 'status_code', 200)
            
            # Extract method and endpoint from request context
            # This would need to be adapted based on your routing setup
            method = "GET"  # Default, should be extracted from request
            endpoint = func.__name__
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Track error metrics
            http_requests_total.labels(
                method="GET",  # Default
                endpoint=func.__name__,
                status="500"
            ).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method="GET",
                endpoint=func.__name__
            ).observe(duration)
            
            raise
    
    return wrapper


def track_gemini_api_call(model: str, success: bool, error_type: str = None):
    """Track Gemini API call metrics"""
    status = "success" if success else "error"
    gemini_api_calls_total.labels(model=model, status=status).inc()
    
    if not success and error_type:
        gemini_api_errors_total.labels(error_type=error_type).inc()


def track_database_error():
    """Track database connection errors"""
    database_connection_errors_total.inc()


def track_youtube_api_call(success: bool):
    """Track YouTube API call metrics"""
    status = "success" if success else "error"
    youtube_api_calls_total.labels(status=status).inc()


def update_active_conversations(count: int):
    """Update active conversations gauge"""
    active_conversations_total.set(count)


def update_active_sessions(count: int):
    """Update active user sessions gauge"""
    user_sessions_active.set(count)


def track_learning_path_generated():
    """Track learning path generation"""
    learning_paths_generated_total.inc()


def track_skill_assessment_completed():
    """Track skill assessment completion"""
    skill_assessments_completed_total.inc()


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    try:
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content="Error generating metrics",
            status_code=500
        )


# Context manager for tracking operation duration
class MetricsTimer:
    """Context manager for tracking operation duration"""
    
    def __init__(self, metric_name: str, labels: Dict[str, str] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Track duration based on metric name
            if self.metric_name == "gemini_api_duration":
                # You would need to define this histogram metric
                pass
            elif self.metric_name == "database_query_duration":
                # You would need to define this histogram metric
                pass