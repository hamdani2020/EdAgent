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
from .middleware import RateLimitMiddleware, LoggingMiddleware
from .endpoints import conversation_router, user_router, assessment_router, learning_router
from .websocket import websocket_router
from .exceptions import setup_exception_handlers


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
    
    # Add health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    
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
    
    # Include WebSocket router
    app.include_router(
        websocket_router,
        prefix="/api/v1",
        tags=["WebSocket"]
    )


# Create the app instance
app = create_app()