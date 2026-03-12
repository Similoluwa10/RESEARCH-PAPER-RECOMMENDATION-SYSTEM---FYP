"""
user.py - User SQLAlchemy Model

Defines the SQLAlchemy ORM model for system users.
Users can interact with papers (view, bookmark, download).
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import UserRole
from src.models.base import Base

if TYPE_CHECKING:
    from src.models.interaction import Interaction
    from src.models.recommendation import Recommendation
    from src.models.explanation import Explanation


class User(Base):
    """
    User entity.
    
    Represents a registered user who can browse, search,
    and receive paper recommendations.
    """
    
    __tablename__ = "users"
    
    # User credentials & profile
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # User role (enum-backed)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", create_constraint=True),
        nullable=False,
        default=UserRole.USER,
    )
    
    # User interests (for personalization)
    preferred_categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        default=None,
    )
    
    # Relationships
    interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    explanations: Mapped[List["Explanation"]] = relationship(
        "Explanation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
