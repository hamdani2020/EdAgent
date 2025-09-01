"""
Database connection management and utilities
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ..config.settings import get_settings
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self.settings = get_settings()
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory"""
        if self._engine is not None:
            return
        
        # Configure engine based on database URL
        if self.settings.database_url.startswith("sqlite"):
            # SQLite configuration
            self._engine = create_async_engine(
                self.settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
                echo=self.settings.api_debug,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30
                }
            )
        else:
            # PostgreSQL configuration
            self._engine = create_async_engine(
                self.settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
                echo=self.settings.api_debug,
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600  # Recycle connections every hour
            )
        
        # Enable foreign key constraints for SQLite
        if self.settings.database_url.startswith("sqlite"):
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(f"Database engine initialized with URL: {self._mask_db_url()}")
    
    async def create_tables(self) -> None:
        """Create all database tables"""
        if self._engine is None:
            await self.initialize()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
    
    async def drop_tables(self) -> None:
        """Drop all database tables (for testing)"""
        if self._engine is None:
            await self.initialize()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped successfully")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if self._session_factory is None:
            await self.initialize()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database engine and cleanup connections"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")
    
    def _mask_db_url(self) -> str:
        """Mask sensitive information in database URL for logging"""
        url = self.settings.database_url
        if "@" in url:
            # Mask password in URL
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split(":")
                if len(user_pass) >= 3:  # protocol:user:pass
                    user_pass[2] = "***"
                    parts[0] = ":".join(user_pass)
            return "@".join(parts)
        return url


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_connection() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session for FastAPI
    
    Yields:
        Database session
    """
    async with db_manager.get_session() as session:
        yield session


async def init_database() -> None:
    """Initialize database and create tables"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_database() -> None:
    """Close database connections"""
    await db_manager.close()


# Database utility functions
async def health_check() -> bool:
    """
    Check database connectivity
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        async with db_manager.get_session() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get database information for monitoring
    
    Returns:
        Dictionary with database information
    """
    try:
        if db_manager._engine is None:
            return {"status": "not_initialized"}
        
        pool = db_manager._engine.pool
        return {
            "status": "connected",
            "pool_size": getattr(pool, 'size', lambda: 0)(),
            "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
            "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
            "overflow": getattr(pool, 'overflow', lambda: 0)(),
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"status": "error", "error": str(e)}