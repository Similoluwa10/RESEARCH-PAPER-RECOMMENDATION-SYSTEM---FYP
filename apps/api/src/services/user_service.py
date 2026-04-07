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
from src.schemas.user import UserCreate, UserUpdate


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

    async def update_profile(self, user_id: UUID, data: UserUpdate) -> Optional[User]:
        """
        Update user profile fields.

        Performs email uniqueness validation when email is changed.
        """
        current_user = await self.repository.get_by_id(user_id)
        if not current_user:
            return None

        update_data = data.model_dump(exclude_unset=True)

        new_email = update_data.get("email")
        if new_email and new_email != current_user.email:
            existing = await self.repository.get_by_email(new_email)
            if existing and existing.id != user_id:
                raise ValueError("Email already registered")

        return await self.repository.update(user_id, update_data)

    async def update_password(self, user_id: UUID, new_password: str) -> Optional[User]:
        """Update user password with hashing."""
        return await self.repository.update_password(user_id, hash_password(new_password))
