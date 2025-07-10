import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine  # for sync operations
from config import settings

# Setup logging
logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# ✅ Async Engine and Session
async_engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False, future=True)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# ✅ Sync Engine and Session
sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

logger.info("✅ Database configuration initialized successfully")