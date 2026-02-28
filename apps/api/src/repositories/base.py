"""
base.py - Base Repository

Abstract base class implementing the Repository Pattern.
Provides common CRUD operations for all entity repositories.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base

# Type variable for generic repository
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository providing common CRUD operations.
    
    All entity repositories should inherit from this class.
    
    Type Parameters:
        ModelType: The SQLAlchemy model class
    """
    
    def __init__(self, db: AsyncSession, model: type[ModelType]):
        """
        Initialize repository with database session and model class.
        
        Args:
            db: Async database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Retrieve a single record by primary key."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ModelType]:
        """Retrieve paginated list of records."""
        result = await self.db.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def count(self) -> int:
        """Get total count of records."""
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()
    
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def update(
        self,
        id: UUID,
        data: Dict[str, Any],
    ) -> Optional[ModelType]:
        """Update an existing record."""
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        for key, value in data.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        await self.db.delete(instance)
        await self.db.commit()
        return True
