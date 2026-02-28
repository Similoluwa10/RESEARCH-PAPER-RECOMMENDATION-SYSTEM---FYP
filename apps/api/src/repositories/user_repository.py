"""
user_repository.py - User Repository

Data access layer for User entities.
Handles database operations for user management.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User entities.
    
    Provides CRUD operations and specialized queries
    for user management and authentication.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email address.
        
        Used for authentication and registration validation.
        
        Args:
            email: User's email address
            
        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if an email is already registered.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        user = await self.get_by_email(email)
        return user is not None
    
    async def update_password(
        self,
        user_id: UUID,
        hashed_password: str,
    ) -> Optional[User]:
        """
        Update a user's password.
        
        Args:
            user_id: User's ID
            hashed_password: New bcrypt-hashed password
            
        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, {"hashed_password": hashed_password})
