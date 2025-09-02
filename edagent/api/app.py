"""
FastAPI application setup and configuration
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from ..config import get_settings
from ..database.connection import db_manager
from .middleware import RateLimitMiddleware, LoggingMiddleware, AuthenticationMiddleware, InputSanitizationMiddleware
from .endpoints import conversation_router, user_router, assessment_router, learning_router
from .endpoints.auth import router as auth_router
from .endpoints.privacy import router as privacy_router
from .websocket import websocket_router
from .exceptions import setup_exception_handlers
from .metrics import metrics_endpoint


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting EdAgent API server...")
    
    # Initialize database
    await db_manager.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down EdAgent API server...")
    await db_manager.close()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="EdAgent API",
        description="AI-powered career coaching assistant API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app, settings)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Add routers
    setup_routers(app)
    
    # Add health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    
    @app.get("/health/detailed", tags=["Health"])
    async def detailed_health_check():
        """Detailed health check with service dependencies"""
        from ..database.connection import get_database_engine
        from ..services.ai_service import AIService
        
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "services": {}
        }
        
        # Check database connection
        try:
            engine = get_database_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            health_status["services"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check AI service
        try:
            ai_service = AIService()
            # Simple test to verify API key is configured
            if ai_service.gemini_api_key:
                health_status["services"]["ai_service"] = {"status": "healthy"}
            else:
                health_status["services"]["ai_service"] = {
                    "status": "unhealthy",
                    "error": "API key not configured"
                }
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["ai_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
    
    @app.get("/metrics", tags=["Monitoring"])
    async def get_metrics():
        """Prometheus metrics endpoint"""
        return await metrics_endpoint()
    
    return app


def setup_middleware(app: FastAPI, settings) -> None:
    """Setup application middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    # Input sanitization middleware
    app.add_middleware(
        InputSanitizationMiddleware,
        max_content_length=1024 * 1024  # 1MB
    )
    
    # Authentication middleware
    app.add_middleware(AuthenticationMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests_per_minute,
        burst_size=settings.rate_limit_burst_size
    )
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)


def setup_routers(app: FastAPI) -> None:
    """Setup API routers"""
    
    # Include authentication router (public endpoints)
    app.include_router(
        auth_router,
        prefix="/api/v1/auth",
        tags=["Authentication"]
    )
    
    # Include all routers with prefixes
    app.include_router(
        conversation_router,
        prefix="/api/v1/conversations",
        tags=["Conversations"]
    )
    
    app.include_router(
        user_router,
        prefix="/api/v1/users",
        tags=["Users"]
    )
    
    app.include_router(
        assessment_router,
        prefix="/api/v1/assessments",
        tags=["Assessments"]
    )
    
    app.include_router(
        learning_router,
        prefix="/api/v1/learning",
        tags=["Learning Paths"]
    )
    
    app.include_router(
        privacy_router,
        prefix="/api/v1/privacy",
        tags=["Privacy"]
    )
    
    # Include WebSocket router
    app.include_router(
        websocket_router,
        prefix="/api/v1",
        tags=["WebSocket"]
    )


# Create the app instance
app = create_app()