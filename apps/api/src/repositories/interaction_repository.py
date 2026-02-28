"""
interaction_repository.py - Interaction Repository

Data access layer for user-paper Interaction entities.
Tracks user engagement with papers for analytics and recommendations.
"""

from typing import Dict, List
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.interaction import Interaction
from src.models.paper import Paper
from src.repositories.base import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    """
    Repository for Interaction entities.
    
    Tracks and queries user-paper interactions for
    analytics and recommendation personalization.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Interaction)
    
    async def create_interaction(
        self,
        user_id: UUID,
        paper_id: UUID,
        interaction_type: str,
    ) -> Interaction:
        """
        Record a new user-paper interaction.
        
        Args:
            user_id: ID of the user
            paper_id: ID of the paper
            interaction_type: Type of interaction (view, bookmark, etc.)
            
        Returns:
            Created interaction instance
        """
        return await self.create({
            "user_id": user_id,
            "paper_id": paper_id,
            "interaction_type": interaction_type,
        })
    
    async def get_user_interactions(
        self,
        user_id: UUID,
        limit: int = 100,
        interaction_type: str = None,
    ) -> List[Interaction]:
        """
        Get all interactions for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of results
            interaction_type: Optional filter by type
            
        Returns:
            List of user's interactions
        """
        query = select(Interaction).where(Interaction.user_id == user_id)
        
        if interaction_type:
            query = query.where(Interaction.interaction_type == interaction_type)
        
        query = query.order_by(Interaction.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_paper_interactions(
        self,
        paper_id: UUID,
    ) -> List[Interaction]:
        """Get all interactions for a specific paper."""
        result = await self.db.execute(
            select(Interaction)
            .where(Interaction.paper_id == paper_id)
            .order_by(Interaction.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_user_papers(
        self,
        user_id: UUID,
        interaction_type: str = None,
    ) -> List[Paper]:
        """
        Get papers a user has interacted with.
        
        Args:
            user_id: ID of the user
            interaction_type: Optional filter by interaction type
            
        Returns:
            List of papers the user has interacted with
        """
        query = (
            select(Paper)
            .join(Interaction)
            .where(Interaction.user_id == user_id)
        )
        
        if interaction_type:
            query = query.where(Interaction.interaction_type == interaction_type)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_by_type(self, paper_id: UUID) -> Dict[str, int]:
        """
        Count interactions by type for a paper.
        
        Useful for engagement analytics.
        
        Returns:
            Dictionary mapping interaction types to counts
        """
        result = await self.db.execute(
            select(
                Interaction.interaction_type,
                func.count(Interaction.id).label("count"),
            )
            .where(Interaction.paper_id == paper_id)
            .group_by(Interaction.interaction_type)
        )
        
        return {row.interaction_type: row.count for row in result.all()}
