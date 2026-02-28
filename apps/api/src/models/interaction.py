"""
interaction.py - User-Paper Interaction SQLAlchemy Model

Tracks user interactions with papers for analytics and
potential collaborative filtering in future iterations.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
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
    
    Interaction types:
        - view: User viewed paper details
        - bookmark: User saved paper for later
        - download: User downloaded the paper
        - cite: User cited the paper
    """
    
    __tablename__ = "interactions"
    
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
