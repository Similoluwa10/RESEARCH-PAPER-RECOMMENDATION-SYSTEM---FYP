"""
Paper Schemas

Pydantic models for paper request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaperBase(BaseModel):
    """Base paper schema."""
    
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str = Field(..., min_length=10)
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = Field(None, ge=1990, le=2100)
    venue: Optional[str] = Field(None, max_length=200)
    keywords: Optional[List[str]] = Field(default_factory=list)
    doi: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    category: str = Field(default="Other", max_length=100)
    source: str = Field(default="Other", max_length=50)
    

class PaperCreate(PaperBase):
    """Schema for creating a paper."""
    pass


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    abstract: Optional[str] = Field(None, min_length=10)
    authors: Optional[List[str]] = None
    year: Optional[int] = Field(None, ge=1990, le=2100)
    venue: Optional[str] = Field(None, max_length=200)
    keywords: Optional[List[str]] = None
    doi: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    


class PaperResponse(PaperBase):
    """Schema for paper response."""

    # Response payloads may contain legacy/imported venue values longer than
    # request-time validation limits. Keep read-path resilient without
    # weakening create/update validation in PaperCreate/PaperUpdate.
    venue: Optional[str] = None
    
    id: UUID    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, paper) -> "PaperResponse":
        """Build response model from ORM/model payload."""
        return cls.model_validate(paper, from_attributes=True)


class PaperList(BaseModel):
    """Schema for paginated paper list."""
    
    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_model(cls, result: dict) -> "PaperList":
        """Build paginated response model from service-layer payload."""
        papers = result.get("papers", [])
        parsed_papers = [PaperResponse.from_model(paper) for paper in papers]
        return cls(
            papers=parsed_papers,
            total=result.get("total", len(parsed_papers)),
            page=result.get("page", 1),
            page_size=result.get("page_size", len(parsed_papers)),
        )


class SavedPaperActionResponse(BaseModel):
    """Response for save/unsave paper actions."""

    paper: PaperResponse
    saved: bool


# Alias for backwards compatibility
PaperListResponse = PaperList
