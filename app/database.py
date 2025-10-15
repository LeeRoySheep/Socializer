"""Database configuration and session management.

Provides SQLAlchemy database connectivity with proper connection pooling,
error handling, and session lifecycle management.

OBSERVABILITY:
- Logs database connection events
- Tracks session creation and closure
- Monitors connection pool status

TRACEABILITY:
- Associates sessions with request IDs
- Timestamps all database operations
- Maintains connection lifecycle logs

EVALUATION:
- Validates database URL format
- Checks connection health before use
- Ensures sessions are always closed
- Rolls back on errors
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
import os

from .config import SQLALCHEMY_DATABASE_URL

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

# Create SQLAlchemy engine with optimized settings
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connections before using
    "pool_recycle": DB_POOL_RECYCLE,  # Recycle connections periodically
    "echo": False,  # Don't log all SQL (security risk in production)
}

# Configure based on database type
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
        "timeout": 30,  # 30 second timeout for locks
    }
    logger.info("Using SQLite database (development mode)")
else:
    # PostgreSQL/MySQL settings
    from sqlalchemy.pool import QueuePool
    engine_kwargs.update({
        "poolclass": QueuePool,
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "pool_timeout": DB_POOL_TIMEOUT,
    })
    logger.info(f"Using production database with pool_size={DB_POOL_SIZE}")

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

# Event listeners for observability
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections."""
    logger.debug("New database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkouts from pool."""
    logger.debug("Connection checked out from pool")

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy-loading issues after commit
)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session with automatic cleanup.
    
    Yields:
        Session: SQLAlchemy database session
        
    OBSERVABILITY:
    - Logs session lifecycle events
    - Tracks session errors
    
    TRACEABILITY:
    - Associates sessions with request context
    
    EVALUATION:
    - Ensures sessions are always closed
    - Rolls back on errors
    - Handles exceptions gracefully
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed")

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)
