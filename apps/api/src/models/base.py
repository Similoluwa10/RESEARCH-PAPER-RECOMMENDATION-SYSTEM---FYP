"""
base.py - SQLAlchemy Base Model & Database Configuration

Defines the base class for all SQLAlchemy ORM models and
configures the async database engine and session factory.
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import DateTime, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import settings

_DEBUG_LOG_PATH = r"C:\Users\HP\OneDrive\Desktop\CODING FILES\2026\RESEARCH RECOMMENDATION SYSTEM - FYP\debug-b5fc23.log"


def _agent_debug_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        import json
        import time

        payload = {
            "sessionId": "b5fc23",
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # #endregion


def _password_probe(password: str | None) -> dict[str, object]:
    return {
        "present": bool(password),
        "length": len(password or ""),
        "is_mask": password == "***",
    }


def _build_async_engine_config(database_url: str) -> tuple[str, dict[str, object]]:
    """Normalize psycopg connection settings for SQLAlchemy's async engine."""

    url = make_url(database_url)
    password_before = url.password
    connect_args: dict[str, object] = {}

    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")

    query = dict(url.query)
    original_query_keys = sorted(query.keys())
    sslmode = query.pop("sslmode", None)
    channel_binding = query.pop("channel_binding", None)
    url = url.set(query=query)

    if sslmode and sslmode.lower() != "disable":
        if url.drivername.endswith("+psycopg"):
            connect_args["sslmode"] = sslmode
        else:
            connect_args["ssl"] = True

    rendered = str(url)
    rendered_password = make_url(rendered).password
    returned = url.render_as_string(hide_password=False)
    returned_password = make_url(returned).password
    # #region agent log
    import os

    _agent_debug_log(
        "H1-H4",
        "apps/api/src/models/base.py:_build_async_engine_config",
        "normalized database url before engine create",
        {
            "drivername": url.drivername,
            "host": url.host,
            "port": url.port,
            "username": url.username,
            "database": url.database,
            "password_before": _password_probe(password_before),
            "password_after_query_rewrite": _password_probe(url.password),
            "password_unchanged_after_rewrite": password_before == url.password,
            "rendered_password": _password_probe(rendered_password),
            "password_survives_str": password_before == rendered_password,
            "returned_password": _password_probe(returned_password),
            "returned_matches_original": returned_password == password_before,
            "original_query_keys": original_query_keys,
            "channel_binding_present": channel_binding is not None,
            "sslmode": sslmode,
            "connect_arg_keys": sorted(connect_args.keys()),
            "database_url_in_environ": "DATABASE_URL" in os.environ,
        },
    )
    # #endregion

    return returned, connect_args


# Create async database engine
database_url, connect_args = _build_async_engine_config(settings.DATABASE_URL)
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args=connect_args,
)


@event.listens_for(engine.sync_engine, "do_connect")
def _log_connect_params(dialect, conn_rec, cargs, cparams):
    # #region agent log
    _agent_debug_log(
        "H1-H5",
        "apps/api/src/models/base.py:do_connect",
        "password handed to dbapi connect",
        {
            "dialect": dialect.name,
            "cparam_keys": sorted(cparams.keys()),
            "password": _password_probe(cparams.get("password")),
            "user": cparams.get("user") or cparams.get("username"),
            "host": cparams.get("host"),
            "port": cparams.get("port"),
            "sslmode": cparams.get("sslmode"),
            "has_ssl_arg": "ssl" in cparams or "sslmode" in connect_args,
            "connect_args": {key: connect_args[key] for key in connect_args},
        },
    )
    # #endregion

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
