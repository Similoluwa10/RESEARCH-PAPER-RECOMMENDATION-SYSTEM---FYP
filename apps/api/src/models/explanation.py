"""
explanation.py - Explanation SQLAlchemy Model

Defines the SQLAlchemy ORM model for recommendation explanations stored in PostgreSQL.
This is the core entity of the recommendation system.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import ExplanationType
from src.models.base import Base

if TYPE_CHECKING:
    from src.models.paper import Paper
    from src.models.user import User


class Explanation(Base):
    """
    Recommendation explanation entity.
    
    Stores explanations for why papers were recommended to users.
    Essential for explainable AI (XAI) in recommendations.
    """
    
    __tablename__ = "explanations"
    
    # Foreign keys
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Explanation content
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ExplanationType.CONTENT_BASED.value,
    )
    
    # Confidence score
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Similar papers (for "similar to X" explanations)
    similar_paper_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True,
    )
    
    # Relationships
    paper: Mapped[Optional["Paper"]] = relationship(
        "Paper",
        back_populates="explanations",
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="explanations",
    )
    
    def __repr__(self) -> str:
        return f"<Explanation(id={self.id}, paper_id={self.paper_id}, user_id={self.user_id})>"