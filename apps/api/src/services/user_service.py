"""
user_service.py - User Service

Business logic for user management and authentication.
Handles registration, login, and password management.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_password
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate


class UserService:
    """
    Service for user management and authentication.
    
    Handles user registration, authentication, and profile management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
    
    async def create_user(self, data: UserCreate) -> User:
        """
        Register a new user with hashed password.
        
        Args:
            data: User registration data (email, name, password)
            
        Returns:
            Created user instance
        """
        user_data = {
            "email": data.email,
            "name": data.name,
            "hashed_password": hash_password(data.password),
        }
        return await self.repository.create(user_data)
    
    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User if credentials valid, None otherwise
        """
        user = await self.repository.get_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.repository.get_by_email(email)
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await self.repository.get_by_id(user_id)
