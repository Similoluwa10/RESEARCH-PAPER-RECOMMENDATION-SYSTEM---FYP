"""
papers.py - Papers Router

Defines REST API endpoints for CRUD operations on research papers.
This is the primary router for paper management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_current_user, get_db
from src.schemas.paper import (
    PaperCreate,
    PaperListResponse,
    PaperResponse,
    PaperUpdate,
    SavedPaperActionResponse,
)
from src.services.paper_service import PaperService
from src.services.saved_paper_service import SavedPaperService

router = APIRouter(prefix="/papers")


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    venue: Optional[str] = Query(None, description="Filter by venue"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all papers with pagination and optional filters.
    
    Returns paginated list of papers with metadata.
    """
    service = PaperService(db)
    result = await service.list_papers(
        page=page,
        page_size=page_size,
        year=year,
        venue=venue,
    )
    return result


@router.get("/saved", response_model=PaperListResponse)
async def list_saved_papers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List papers saved by the authenticated user."""
    service = SavedPaperService(db)
    return await service.list_saved_papers(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{paper_id}/save",
    response_model=SavedPaperActionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Save a paper for the authenticated user."""
    service = SavedPaperService(db)
    return await service.save_paper(user_id=current_user.id, paper_id=paper_id)


@router.delete("/{paper_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove a paper from the authenticated user's saved list."""
    service = SavedPaperService(db)
    await service.unsave_paper(user_id=current_user.id, paper_id=paper_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single paper by ID."""
    service = PaperService(db)
    paper = await service.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    
    return paper


# @router.post("", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
# async def create_paper(
#     paper_data: PaperCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user),
# ):
#     """Create a new paper. Requires authentication."""
#     service = PaperService(db)
#     paper = await service.create_paper(paper_data)
#     return paper


# @router.put("/{paper_id}", response_model=PaperResponse)
# async def update_paper(
#     paper_id: UUID,
#     paper_data: PaperUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user),
# ):
#     """Update an existing paper. Requires authentication."""
#     service = PaperService(db)
#     paper = await service.update_paper(paper_id, paper_data)
    
#     if not paper:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Paper not found",
#         )
    
#     return paper


# @router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_paper(
#     paper_id: UUID,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user),
# ):
#     """Delete a paper. Requires authentication."""
#     service = PaperService(db)
#     deleted = await service.delete_paper(paper_id)
    
#     if not deleted:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Paper not found",
#         )
