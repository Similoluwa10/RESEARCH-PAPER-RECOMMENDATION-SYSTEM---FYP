"""
user.py - User SQLAlchemy Model

Defines the SQLAlchemy ORM model for system users.
Users can interact with papers (view, bookmark, download).
"""

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.interaction import Interaction


class User(Base):
    """
    User entity.
    
    Represents a registered user who can browse, search,
    and receive paper recommendations.
    """
    
    __tablename__ = "users"
    
    # User credentials
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
