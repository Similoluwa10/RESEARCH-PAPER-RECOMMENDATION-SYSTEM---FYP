"""
saved_paper_service.py - Saved Paper Service

Handles bookmark/save actions and retrieval for authenticated users.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import InteractionType
from src.repositories.interaction_repository import InteractionRepository
from src.repositories.paper_repository import PaperRepository
from src.schemas.paper import PaperListResponse, PaperResponse, SavedPaperActionResponse


class SavedPaperService:
    """Service layer for saved paper operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.interaction_repo = InteractionRepository(db)
        self.paper_repo = PaperRepository(db)

    async def save_paper(self, user_id: UUID, paper_id: UUID) -> SavedPaperActionResponse:
        """Save a paper for a user if not already saved."""
        paper = await self.paper_repo.get_by_id(paper_id)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found",
            )

        existing = await self.interaction_repo.get_by_user_paper_type(
            user_id=user_id,
            paper_id=paper_id,
            interaction_type=InteractionType.BOOKMARK.value,
        )

        if not existing:
            await self.interaction_repo.create_interaction(
                user_id=user_id,
                paper_id=paper_id,
                interaction_type=InteractionType.BOOKMARK.value,
            )

        return SavedPaperActionResponse(
            paper=PaperResponse.from_model(paper),
            saved=True,
        )

    async def unsave_paper(self, user_id: UUID, paper_id: UUID) -> bool:
        """Remove a saved paper from a user's library."""
        return await self.interaction_repo.delete_by_user_paper_type(
            user_id=user_id,
            paper_id=paper_id,
            interaction_type=InteractionType.BOOKMARK.value,
        )

    async def list_saved_papers(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
    ) -> PaperListResponse:
        """Get paginated saved papers for a user."""
        offset = (page - 1) * page_size
        papers, total = await self.interaction_repo.get_saved_papers_paginated(
            user_id=user_id,
            limit=page_size,
            offset=offset,
            interaction_type=InteractionType.BOOKMARK.value,
        )

        return PaperListResponse.from_model(
            {
                "papers": papers,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )
