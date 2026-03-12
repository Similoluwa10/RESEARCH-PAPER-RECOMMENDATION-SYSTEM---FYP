"""
User Schemas

Pydantic models for user request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.core.enums import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    preferred_categories: Optional[List[str]] = None


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: UUID
    role: UserRole
    is_active: bool
    preferred_categories: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str
    token_type: str = "bearer"
