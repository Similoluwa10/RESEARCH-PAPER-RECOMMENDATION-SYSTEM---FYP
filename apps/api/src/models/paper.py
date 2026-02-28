"""
paper.py - Paper SQLAlchemy Model

Defines the SQLAlchemy ORM model for research papers stored in PostgreSQL.
This is the core entity of the recommendation system.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.embedding import Embedding
    from src.models.interaction import Interaction


class Paper(Base):
    """
    Research paper entity.
    
    Stores metadata about academic papers including title, abstract,
    authors, and publication information.
    """
    
    __tablename__ = "papers"
    
    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Optional metadata
    venue: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    embedding: Mapped[Optional["Embedding"]] = relationship(
        "Embedding",
        back_populates="paper",
        uselist=False,
        cascade="all, delete-orphan",
    )
    interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, title='{self.title[:50]}...')>"
