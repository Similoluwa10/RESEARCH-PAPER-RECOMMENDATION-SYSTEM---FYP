"""
recommendation.py - Recommendation SQLAlchemy Model

Tracks all recommendations made to users for analytics
and measuring recommendation quality.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.paper import Paper
    from src.models.user import User


class Recommendation(Base):
    """
    Paper recommendation entity.
    
    Tracks all recommendations made to users for analytics
    and measuring recommendation quality.
    """
    
    __tablename__ = "recommendations"
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Recommendation details
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # User feedback
    clicked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    helpful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="recommendations",
    )
    paper: Mapped[Optional["Paper"]] = relationship(
        "Paper",
    )
    
    def __repr__(self) -> str:
        return f"<Recommendation(user_id={self.user_id}, paper_id={self.paper_id}, rank={self.rank})>"
