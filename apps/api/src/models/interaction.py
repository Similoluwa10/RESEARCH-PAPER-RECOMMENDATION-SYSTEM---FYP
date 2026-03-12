"""
interaction.py - User-Paper Interaction SQLAlchemy Model

Tracks user interactions with papers for analytics and
potential collaborative filtering in future iterations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.paper import Paper
    from src.models.user import User


class Interaction(Base):
    """
    User-Paper interaction entity.
    
    Records user interactions with papers for tracking
    engagement and building preference profiles.
    """
    
    __tablename__ = "interactions"
    
    __table_args__ = (
        UniqueConstraint(
            'user_id', 'paper_id', 'interaction_type',
            name='uq_user_paper_interaction',
        ),
        CheckConstraint(
            'rating IS NULL OR (rating >= 1 AND rating <= 5)',
            name='ck_interaction_rating_range',
        ),
    )
    
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
    
    # Interaction type
    interaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # Engagement weight
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    
    # User rating (explicit feedback, 1-5)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Interaction timestamp
    interaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="interactions",
    )
    paper: Mapped[Optional["Paper"]] = relationship(
        "Paper",
        back_populates="interactions",
    )
    
    def __repr__(self) -> str:
        return f"<Interaction(user_id={self.user_id}, paper_id={self.paper_id}, type='{self.interaction_type}')>"
