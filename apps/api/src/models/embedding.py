"""
embedding.py - Paper Embedding SQLAlchemy Model

Stores vector embeddings for papers using PostgreSQL pgvector extension.
Enables semantic similarity search for recommendations.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import settings
from src.models.base import Base

if TYPE_CHECKING:
    from src.models.paper import Paper


class Embedding(Base):
    """
    Paper embedding entity.
    
    Stores the vector representation of a paper's abstract
    for semantic similarity search using pgvector.
    """
    
    __tablename__ = "embeddings"
    
    # Foreign key to paper (one embedding per paper)
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Embedding metadata
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=settings.EMBEDDING_MODEL_NAME,
    )
    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
    )
    
    # Vector embedding (dimension from settings)
    vector: Mapped[list] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION),
        nullable=False,
    )
    
    # Quality metrics
    embedding_quality_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=None,
    )
    
    # Relationships
    paper: Mapped[Optional["Paper"]] = relationship(
        "Paper",
        back_populates="embedding",
    )
    
    def __repr__(self) -> str:
        return f"<Embedding(paper_id={self.paper_id}, model='{self.model_name}')>"
