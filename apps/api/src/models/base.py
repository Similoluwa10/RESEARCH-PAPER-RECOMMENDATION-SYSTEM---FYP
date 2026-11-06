"""
base.py - SQLAlchemy Base Model & Database Configuration

Defines the base class for all SQLAlchemy ORM models and
configures the async database engine and session factory.
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import settings


def _build_async_engine_config(database_url: str) -> tuple[str, dict[str, object]]:
    """Normalize asyncpg connection settings for SQLAlchemy."""

    url = make_url(database_url)
    connect_args: dict[str, object] = {}

    if url.drivername.endswith("+asyncpg"):
        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        url = url.set(query=query)

        if sslmode and sslmode.lower() != "disable":
            connect_args["ssl"] = True

    return str(url), connect_args


# Create async database engine
database_url, connect_args = _build_async_engine_config(settings.DATABASE_URL)
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args=connect_args,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common columns:
        - id: UUID primary key
        - created_at: Auto-set creation timestamp
        - updated_at: Auto-updated modification timestamp
    """
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with async_session_maker() as session:
        yield session
